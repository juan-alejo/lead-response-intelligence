"""Deterministic mock submitter — used by demos, CI, and the Phase 2 tab.

Design goals:

1. **Deterministic** — the same submission always produces the same outcome
   (success / failure / needs_manual). Crucial for CI assertions and for
   giving demos a stable story.
2. **Covers the interesting branches** — a naïve mock that always succeeds
   hides the UX around failure. This mock fails a predictable minority of
   submissions so the dashboard actually shows red rows in demo mode.
3. **Cheap to run** — no I/O, no network, no real time. Fractional-ms
   latency is simulated by stamping `duration_ms` based on the submission
   id hash, so the UI can show a sensible distribution.

Failure simulation is keyed on a stable hash of `submission_id` so reruns
don't flicker, and the breakdown roughly matches real-world results the
`PlaywrightFormSubmitter` sees (see PHASE_2_SPEC.md §4): ~80% success,
~10% needs-manual (CAPTCHA / auth), ~10% failed (site down, field
mismatch).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta

from ..models import (
    SubmissionAttempt,
    SubmissionAttemptStatus,
    SubmissionMethod,
)
from .base import FormSubmitter, SubmissionRequest

# ---- outcome selection ----------------------------------------------------

_SUCCESS_BAND = 80   # 0..79   → completed
_MANUAL_BAND = 90    # 80..89  → needs_manual (CAPTCHA / auth)
# 90..99 → failed


def _stable_bucket(submission_id: str) -> int:
    """Return 0-99 deterministically from the submission id."""
    digest = hashlib.sha256(submission_id.encode("utf-8")).digest()
    return digest[0] % 100


def _stable_duration_ms(submission_id: str) -> int:
    """350-2500 ms, deterministic — enough to make a realistic histogram."""
    digest = hashlib.sha256(submission_id.encode("utf-8")).digest()
    return 350 + (int.from_bytes(digest[1:3], "big") % 2151)


# ---- method-specific "confirmation" copy ----------------------------------

_CONFIRMATION_BY_METHOD = {
    SubmissionMethod.CONTACT_FORM: (
        "Thanks — we received your message and will get back to you shortly."
    ),
    SubmissionMethod.CHAT_WIDGET: (
        "Your chat has been queued — an agent will respond during business hours."
    ),
    SubmissionMethod.BOOKING_WIDGET: (
        "Booking request received. A confirmation email is on its way."
    ),
}


class MockFormSubmitter(FormSubmitter):
    """Offline submitter with a realistic success/failure mix.

    Use for:
        - Demo mode (`PHASE_2_ENABLED=true, SUBMITTER_MODE=mock`)
        - CI tests (deterministic outcomes)
        - Local development before the Playwright submitter is wired up

    Behavior:
        - ~80% of submissions succeed.
        - ~10% return `NEEDS_MANUAL` (simulated CAPTCHA or auth wall).
        - ~10% fail with an actionable error message.
        - Every attempt emits 3-5 log lines documenting the decisions the
          real submitter would make on the same site, so the dashboard
          has something meaningful to show.
    """

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or _WallClock()

    def submit(self, request: SubmissionRequest) -> SubmissionAttempt:
        sub = request.submission
        bucket = _stable_bucket(sub.submission_id)
        duration_ms = _stable_duration_ms(sub.submission_id)

        started_at = self._clock.now()
        completed_at = started_at + timedelta(milliseconds=duration_ms)

        attempt = SubmissionAttempt(
            attempt_id=str(uuid.uuid4()),
            submission_id=sub.submission_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            form_url=request.form_url,
        )

        attempt.logs.append(
            f"[mock] target={sub.business_name} method={sub.submission_method.value}"
        )
        attempt.logs.append(
            f"[mock] filling name='{request.lead.full_name}' "
            f"email='{request.lead.email}' phone='{request.lead.phone}'"
        )

        if bucket < _SUCCESS_BAND:
            attempt.status = SubmissionAttemptStatus.COMPLETED
            attempt.confirmation_text = _CONFIRMATION_BY_METHOD.get(
                sub.submission_method, ""
            )
            attempt.logs.append(
                "[mock] form submitted → confirmation text detected"
            )
            attempt.logs.append(
                f"[mock] completed in {duration_ms}ms"
            )
        elif bucket < _MANUAL_BAND:
            attempt.status = SubmissionAttemptStatus.NEEDS_MANUAL
            attempt.error_message = (
                "CAPTCHA detected on submit — bouncing back to the human queue."
            )
            attempt.logs.append("[mock] reCAPTCHA v2 challenge appeared post-click")
            attempt.logs.append(
                "[mock] not bypassing — policy is to never solve live CAPTCHAs"
            )
            attempt.logs.append(
                "[mock] marked needs_manual so an operator can submit by hand"
            )
        else:
            attempt.status = SubmissionAttemptStatus.FAILED
            attempt.error_message = (
                "Expected form field 'email' not found on page — likely a "
                "chat-only site mis-classified upstream."
            )
            attempt.logs.append(
                "[mock] selector [name=email] not present; aborted"
            )
            attempt.logs.append(
                "[mock] retry safe after manual re-classification"
            )

        return attempt


# ---- clock injection (keeps tests pure) -----------------------------------


class Clock:
    def now(self) -> datetime:  # pragma: no cover - protocol only
        raise NotImplementedError


class _WallClock:
    def now(self) -> datetime:
        return datetime.now()


class FixedClock:
    """Test double — returns a frozen timestamp (optionally monotonic).

    When `monotonic=True`, each call advances the clock by 1 ms so a single
    test can assert `started_at < completed_at` without fighting the `ms`
    resolution of the wall clock.
    """

    def __init__(self, *, frozen: datetime, monotonic: bool = False) -> None:
        self._t = frozen
        self._monotonic = monotonic

    def now(self) -> datetime:
        if self._monotonic:
            self._t = self._t + timedelta(milliseconds=1)
        return self._t
