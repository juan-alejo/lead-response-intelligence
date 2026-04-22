"""Phase 2 submitter tests.

Covers the three behaviors the rest of the system depends on:

1. `MockFormSubmitter` is deterministic — same submission id → same outcome.
2. The success/manual/failed distribution matches the design intent (~80/10/10).
3. `SubmissionQueue.run_once` writes attempts to storage, skips already-
   terminal submissions, and gracefully captures submitter exceptions.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.models import (
    Prospect,
    Submission,
    SubmissionAttempt,
    SubmissionAttemptStatus,
    SubmissionMethod,
)
from src.storage import SQLiteStore
from src.submitter import (
    FormSubmitter,
    LeadIdentity,
    MockFormSubmitter,
    SubmissionQueue,
    SubmissionRequest,
)
from src.submitter.mock import FixedClock, _stable_bucket

# ------------------------------------------------------------------ helpers


def _submission(
    idx: int, method: SubmissionMethod = SubmissionMethod.CONTACT_FORM
) -> Submission:
    return Submission(
        submission_id=f"sub-{idx:04d}",
        prospect_place_id=f"place-{idx}",
        business_name=f"Business {idx}",
        vertical="law_firm",
        submission_method=method,
        expected_sender_email=f"biz{idx}@example.com",
        expected_sender_phone=f"+1212555{idx:04d}",
    )


def _store(tmp_path: Path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "phase2.sqlite")
    # Seed a broad set of prospects so any submission we build here satisfies
    # the foreign-key constraint and prospect_website() returns something.
    store.upsert_prospects(
        [
            Prospect(
                place_id=f"place-{i}",
                business_name=f"Business {i}",
                vertical="law_firm",
                location="manhattan",
                website="https://example.com",
            )
            for i in range(0, 20)
        ]
        + [
            Prospect(
                place_id="place-spa",
                business_name="Aurora Med Spa",
                vertical="med_spa",
                location="manhattan",
                website="https://aurora.example.com",
            )
        ]
    )
    return store


# ------------------------------------------------------------------ mock submitter


def test_mock_submitter_is_deterministic() -> None:
    """Same submission_id → same outcome, twice."""
    submitter = MockFormSubmitter(
        clock=FixedClock(frozen=datetime(2026, 4, 22, 10, 0), monotonic=True)
    )
    sub = _submission(1)
    req = SubmissionRequest(
        submission=sub,
        form_url="https://example.com",
        lead=LeadIdentity.default_demo(),
    )

    a = submitter.submit(req)
    b = submitter.submit(req)

    assert a.status == b.status
    assert a.duration_ms == b.duration_ms


def test_mock_submitter_covers_all_three_outcomes() -> None:
    """Across 100 submissions we should see success / needs_manual / failed all
    represented — otherwise the dashboard never shows red rows in demo."""
    submitter = MockFormSubmitter(
        clock=FixedClock(frozen=datetime(2026, 4, 22, 10, 0), monotonic=True)
    )
    outcomes: dict[SubmissionAttemptStatus, int] = {}
    for i in range(100):
        sub = _submission(i)
        req = SubmissionRequest(
        submission=sub,
        form_url="https://example.com",
        lead=LeadIdentity.default_demo(),
    )
        attempt = submitter.submit(req)
        outcomes[attempt.status] = outcomes.get(attempt.status, 0) + 1

    assert outcomes.get(SubmissionAttemptStatus.COMPLETED, 0) > 50, outcomes
    assert outcomes.get(SubmissionAttemptStatus.NEEDS_MANUAL, 0) >= 1, outcomes
    assert outcomes.get(SubmissionAttemptStatus.FAILED, 0) >= 1, outcomes


def test_mock_submitter_populates_audit_fields() -> None:
    submitter = MockFormSubmitter(
        clock=FixedClock(frozen=datetime(2026, 4, 22, 10, 0), monotonic=True)
    )
    sub = _submission(42)
    req = SubmissionRequest(
        submission=sub,
        form_url="https://example.com/contact",
        lead=LeadIdentity.default_demo(),
    )

    attempt = submitter.submit(req)

    assert attempt.attempt_id
    assert attempt.submission_id == sub.submission_id
    assert attempt.form_url == "https://example.com/contact"
    assert attempt.started_at is not None
    assert attempt.completed_at is not None
    assert attempt.duration_ms is not None and attempt.duration_ms > 0
    assert len(attempt.logs) >= 3
    assert attempt.is_terminal()


def test_stable_bucket_deterministic() -> None:
    """Hash bucketing is stable regardless of platform."""
    assert _stable_bucket("sub-0001") == _stable_bucket("sub-0001")
    assert 0 <= _stable_bucket("any-id") < 100


# ------------------------------------------------------------------ queue


def test_queue_runs_batch_and_persists_attempts(tmp_path: Path) -> None:
    store = _store(tmp_path)
    subs = [_submission(i) for i in range(1, 6)]
    store.upsert_submissions(subs)

    queue = SubmissionQueue(
        storage=store,
        submitter=MockFormSubmitter(
            clock=FixedClock(frozen=datetime(2026, 4, 22), monotonic=True)
        ),
        lead=LeadIdentity.default_demo(),
    )

    result = queue.run_once(limit=10)

    assert result.attempted == 5
    assert len(store.all_attempts()) == 5
    # Every submission has exactly one attempt so attempt_number is 1.
    assert all(a.attempt_number == 1 for a in store.all_attempts())


def test_queue_skips_already_terminal_submissions(tmp_path: Path) -> None:
    """A submission with a terminal attempt doesn't get re-submitted on the
    next batch — otherwise we'd double-submit and double-bill."""
    store = _store(tmp_path)
    subs = [_submission(i) for i in range(1, 4)]
    store.upsert_submissions(subs)

    queue = SubmissionQueue(
        storage=store,
        submitter=MockFormSubmitter(
            clock=FixedClock(frozen=datetime(2026, 4, 22), monotonic=True)
        ),
        lead=LeadIdentity.default_demo(),
    )

    first = queue.run_once(limit=10)
    second = queue.run_once(limit=10)

    assert first.attempted == 3
    assert second.attempted == 0  # nothing left to do


def test_queue_filters_by_vertical(tmp_path: Path) -> None:
    store = _store(tmp_path)
    subs = [
        _submission(1),  # law_firm
        Submission(
            submission_id="sub-spa",
            prospect_place_id="place-spa",
            business_name="Aurora Med Spa",
            vertical="med_spa",
            submission_method=SubmissionMethod.BOOKING_WIDGET,
        ),
    ]
    store.upsert_submissions(subs)

    queue = SubmissionQueue(
        storage=store,
        submitter=MockFormSubmitter(
            clock=FixedClock(frozen=datetime(2026, 4, 22), monotonic=True)
        ),
        lead=LeadIdentity.default_demo(),
    )

    result = queue.run_once(limit=10, vertical="med_spa")

    assert result.attempted == 1
    assert result.attempts[0].submission_id == "sub-spa"


def test_queue_captures_submitter_crash_as_failed(tmp_path: Path) -> None:
    """A buggy real-world submitter shouldn't ever take down the batch."""

    class ExplodingSubmitter(FormSubmitter):
        def submit(self, request: SubmissionRequest) -> SubmissionAttempt:
            raise RuntimeError("selector not found — page layout changed")

    store = _store(tmp_path)
    store.upsert_submissions([_submission(1)])
    queue = SubmissionQueue(
        storage=store,
        submitter=ExplodingSubmitter(),
        lead=LeadIdentity.default_demo(),
    )

    result = queue.run_once(limit=10)

    assert result.attempted == 1
    assert result.failed == 1
    attempts = store.all_attempts()
    assert len(attempts) == 1
    assert attempts[0].status == SubmissionAttemptStatus.FAILED
    assert "RuntimeError" in attempts[0].error_message


def test_queue_respects_limit(tmp_path: Path) -> None:
    store = _store(tmp_path)
    subs = [_submission(i) for i in range(1, 11)]
    store.upsert_submissions(subs)
    queue = SubmissionQueue(
        storage=store,
        submitter=MockFormSubmitter(
            clock=FixedClock(frozen=datetime(2026, 4, 22), monotonic=True)
        ),
        lead=LeadIdentity.default_demo(),
    )

    result = queue.run_once(limit=3)

    assert result.attempted == 3
    assert len(store.all_attempts()) == 3


# ------------------------------------------------------------------ storage


def test_storage_roundtrips_attempts(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_submissions([_submission(1)])
    attempt = SubmissionAttempt(
        attempt_id="att-1",
        submission_id="sub-0001",
        status=SubmissionAttemptStatus.COMPLETED,
        started_at=datetime(2026, 4, 22, 10, 0, 0),
        completed_at=datetime(2026, 4, 22, 10, 0, 1),
        duration_ms=1234,
        form_url="https://example.com",
        confirmation_text="Thanks!",
        logs=["line1", "line2"],
        attempt_number=1,
    )
    store.upsert_attempts([attempt])

    all_attempts = store.all_attempts()
    assert len(all_attempts) == 1
    roundtrip = all_attempts[0]
    assert roundtrip.attempt_id == "att-1"
    assert roundtrip.status == SubmissionAttemptStatus.COMPLETED
    assert roundtrip.duration_ms == 1234
    assert roundtrip.logs == ["line1", "line2"]


def test_storage_attempts_for_submission(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_submissions([_submission(1), _submission(2)])
    attempts = [
        SubmissionAttempt(attempt_id="a1", submission_id="sub-0001", attempt_number=1),
        SubmissionAttempt(attempt_id="a2", submission_id="sub-0001", attempt_number=2),
        SubmissionAttempt(attempt_id="a3", submission_id="sub-0002", attempt_number=1),
    ]
    store.upsert_attempts(attempts)

    sub1_attempts = store.attempts_for_submission("sub-0001")
    assert len(sub1_attempts) == 2
    assert [a.attempt_number for a in sub1_attempts] == [1, 2]


@pytest.mark.parametrize("status", list(SubmissionAttemptStatus))
def test_attempt_is_terminal_matrix(status: SubmissionAttemptStatus) -> None:
    attempt = SubmissionAttempt(attempt_id="a", submission_id="s", status=status)
    if status in (
        SubmissionAttemptStatus.COMPLETED,
        SubmissionAttemptStatus.FAILED,
        SubmissionAttemptStatus.NEEDS_MANUAL,
    ):
        assert attempt.is_terminal()
    else:
        assert not attempt.is_terminal()
