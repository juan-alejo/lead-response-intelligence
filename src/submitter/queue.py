"""Batch façade over a FormSubmitter.

Phase 1 queues `Submission` rows in SQLite. The queue layer here:

1. Reads the pending submissions (= those without a terminal attempt yet).
2. Delegates each to the configured `FormSubmitter`.
3. Writes the resulting `SubmissionAttempt` rows back through `Storage`.

The queue is deliberately synchronous: real-world throughput is well under
one submission per second per worker (sites we target are operator-facing
forms, not high-volume endpoints), so async buys nothing. Concurrency, when
needed for the live Playwright submitter, lives one level up via a
thread/process pool wrapping `.run_once()`.
"""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from ..models import (
    Submission,
    SubmissionAttempt,
    SubmissionAttemptStatus,
)
from ..storage import Storage
from .base import FormSubmitter, LeadIdentity, SubmissionRequest


@dataclass
class BatchResult:
    attempted: int = 0
    completed: int = 0
    failed: int = 0
    needs_manual: int = 0
    skipped: int = 0  # submissions we didn't touch (already terminal)
    attempts: list[SubmissionAttempt] = None  # populated by run_once

    def __post_init__(self) -> None:
        if self.attempts is None:
            self.attempts = []


class SubmissionQueue:
    """Wraps a FormSubmitter + Storage into a 'run the next batch' action.

    Typical use (inside pipeline.py):

        queue = SubmissionQueue(storage, submitter, lead=LeadIdentity(...))
        result = queue.run_once(limit=50)

    And from the dashboard: same call, optionally filtered to a vertical.
    """

    def __init__(
        self,
        storage: Storage,
        submitter: FormSubmitter,
        *,
        lead: LeadIdentity,
    ) -> None:
        self.storage = storage
        self.submitter = submitter
        self.lead = lead

    # ---------- reads ----------

    def pending_submissions(
        self, submissions: list[Submission] | None = None
    ) -> list[Submission]:
        """Submissions with no terminal attempt yet.

        If `submissions` is provided, filter that list; otherwise pull the
        full set from storage. Passing in the list is a micro-optimization
        for the dashboard, which already has it cached.
        """
        all_subs = submissions if submissions is not None else self.storage.all_submissions()
        attempts = self.storage.all_attempts()
        terminal_ids = {
            a.submission_id
            for a in attempts
            if a.is_terminal()
        }
        return [s for s in all_subs if s.submission_id not in terminal_ids]

    def attempt_count_by_submission(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self.storage.all_attempts():
            counts[a.submission_id] = counts.get(a.submission_id, 0) + 1
        return counts

    # ---------- writes ----------

    def run_once(
        self,
        *,
        limit: int = 50,
        vertical: str | None = None,
    ) -> BatchResult:
        """Run up to `limit` pending submissions. Persists attempts.

        `vertical`: optional filter — e.g., "only law_firm this run" — for
        operators who want to segment their daily batch.

        Error isolation: one broken submitter run never takes down the batch.
        The submitter contract promises never to raise, but we belt-and-
        suspenders it here: any exception still gets captured as a FAILED
        attempt so the operator can see it in the UI.
        """
        pending = self.pending_submissions()
        if vertical:
            pending = [s for s in pending if s.vertical == vertical]
        pending = pending[:limit]

        prior_counts = self.attempt_count_by_submission()
        result = BatchResult()
        new_attempts: list[SubmissionAttempt] = []

        for sub in pending:
            # The real submitter derives `form_url` from the stored
            # Classification row; in the queue we fall back to the simpler
            # "whatever was queued" shape so mock mode doesn't need a join.
            form_url = _resolve_form_url(self.storage, sub)
            request = SubmissionRequest(
                submission=sub,
                form_url=form_url,
                lead=self.lead,
            )
            try:
                attempt = self.submitter.submit(request)
            except Exception as e:  # noqa: BLE001 - defensive; see docstring
                logger.exception(
                    f"[submitter] {type(self.submitter).__name__} raised on "
                    f"{sub.submission_id}; capturing as FAILED"
                )
                import uuid

                from ..models import _utc_now

                attempt = SubmissionAttempt(
                    attempt_id=str(uuid.uuid4()),
                    submission_id=sub.submission_id,
                    status=SubmissionAttemptStatus.FAILED,
                    started_at=_utc_now(),
                    completed_at=_utc_now(),
                    duration_ms=0,
                    form_url=form_url,
                    error_message=f"Submitter crashed: {type(e).__name__}: {e}",
                )

            attempt.attempt_number = prior_counts.get(sub.submission_id, 0) + 1
            prior_counts[sub.submission_id] = attempt.attempt_number

            new_attempts.append(attempt)
            result.attempted += 1
            if attempt.status == SubmissionAttemptStatus.COMPLETED:
                result.completed += 1
            elif attempt.status == SubmissionAttemptStatus.NEEDS_MANUAL:
                result.needs_manual += 1
            elif attempt.status == SubmissionAttemptStatus.FAILED:
                result.failed += 1

        if new_attempts:
            self.storage.upsert_attempts(new_attempts)
        result.attempts = new_attempts
        logger.info(
            f"[queue] ran batch: attempted={result.attempted} "
            f"completed={result.completed} failed={result.failed} "
            f"needs_manual={result.needs_manual}"
        )
        return result


def _resolve_form_url(storage: Storage, submission: Submission) -> str:
    """Best-effort lookup: prefer the classification's form_url, then the
    prospect's website, then empty string.

    Concrete implementations are free to pass a different url via their
    own adapter; the queue's behavior is intentionally permissive so the
    mock path doesn't need a classifications join.
    """
    # The storage interface doesn't expose classifications directly (Phase 1
    # only persists the form_type via Submission.submission_method), so we
    # fall back to the prospect website via place_id.
    if hasattr(storage, "prospect_website"):
        website = storage.prospect_website(submission.prospect_place_id)  # type: ignore[attr-defined]
        if website:
            return website
    return ""
