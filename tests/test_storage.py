"""SQLite store: prospects / submissions / responses CRUD + dedup helper."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from src.models import (
    Prospect,
    Response,
    ResponseChannel,
    Submission,
    SubmissionMethod,
)
from src.storage import SQLiteStore


def _make_prospect(pid: str = "p1") -> Prospect:
    return Prospect(
        place_id=pid,
        business_name=f"Biz {pid}",
        vertical="law_firm",
        location="manhattan",
        website="https://biz.example.com",
    )


def _make_submission(sid: str = "s1", pid: str = "p1") -> Submission:
    return Submission(
        submission_id=sid,
        prospect_place_id=pid,
        business_name="Biz p1",
        vertical="law_firm",
        submission_method=SubmissionMethod.CONTACT_FORM,
        expected_sender_phone="+15555550100",
        expected_sender_email="inbox@test.example.com",
        submitted_at=datetime(2026, 4, 21, 14, 0),
    )


def test_upsert_prospects_roundtrip(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "db.sqlite")

    written = store.upsert_prospects([_make_prospect("p1"), _make_prospect("p2")])
    assert written == 2

    recent = store.recent_place_ids()
    assert set(recent.keys()) == {"p1", "p2"}


def test_upsert_is_idempotent(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "db.sqlite")
    prospect = _make_prospect("p1")

    store.upsert_prospects([prospect])
    store.upsert_prospects([prospect])  # same id, should not duplicate

    assert len(store.recent_place_ids()) == 1


def test_recent_place_ids_respects_window(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "db.sqlite")
    store.upsert_prospects([_make_prospect("p1")])

    from src.models import _utc_now

    result = store.recent_place_ids(window_days=90)
    assert "p1" in result
    assert result["p1"] > _utc_now() - timedelta(days=1)


def test_submissions_roundtrip(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "db.sqlite")
    store.upsert_prospects([_make_prospect("p1")])
    store.upsert_submissions([_make_submission("s1", "p1")])

    loaded = store.all_submissions()
    assert len(loaded) == 1
    assert loaded[0].submission_id == "s1"
    assert loaded[0].submitted_at == datetime(2026, 4, 21, 14, 0)


def test_responses_roundtrip(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "db.sqlite")
    store.upsert_prospects([_make_prospect("p1")])
    store.upsert_submissions([_make_submission("s1", "p1")])

    response = Response(
        response_id="r1",
        channel=ResponseChannel.EMAIL,
        received_at=datetime(2026, 4, 21, 14, 30),
        matched_submission_id="s1",
        elapsed_seconds=1800,
        sender_email="response@biz-p1.example.com",
        content_snippet="Thanks for reaching out",
    )
    store.upsert_responses([response])

    loaded = store.all_responses()
    assert len(loaded) == 1
    assert loaded[0].matched_submission_id == "s1"
    assert loaded[0].elapsed_seconds == 1800
