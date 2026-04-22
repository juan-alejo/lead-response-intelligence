"""Core domain models.

Prospects flow through the pipeline in one direction:

    Prospect  ─► classified into ─►  Submission  ◄─ matched ─►  Response

Everything is a Pydantic model so validation happens at the boundary between
modules, not as a silent source of KeyError three hops down the call stack.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


def _utc_now() -> datetime:
    """Naive UTC — future-proof replacement for `datetime.utcnow()`."""
    return datetime.now(UTC).replace(tzinfo=None)


class FormType(StrEnum):
    CONTACT_FORM = "contact_form"
    CHAT_WIDGET = "chat_widget"
    BOOKING_WIDGET = "booking_widget"
    NONE = "none"


class CompetitorTool(StrEnum):
    INTERCOM = "intercom"
    DRIFT = "drift"
    LIVECHAT = "livechat"
    INTAKER = "intaker"
    JUVO_LEADS = "juvo_leads"
    CALENDLY = "calendly"
    ACUITY = "acuity"
    HUBSPOT_MEETINGS = "hubspot_meetings"


class ResponseChannel(StrEnum):
    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"
    WHATSAPP = "whatsapp"


class SubmissionMethod(StrEnum):
    CONTACT_FORM = "contact_form"
    CHAT_WIDGET = "chat_widget"
    BOOKING_WIDGET = "booking_widget"


class Prospect(BaseModel):
    """A business we might test, ingested from Google Places or CSV."""

    place_id: str  # Stable external id — our natural key for deduplication.
    business_name: str
    vertical: str  # free-form; validated against VerticalRegistry at CLI level
    location: str  # free-form; validated against LocationRegistry at CLI level
    website: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    discovered_at: datetime = Field(default_factory=_utc_now)


class Classification(BaseModel):
    """Output of the classification step for a single prospect."""

    prospect_place_id: str
    form_type: FormType
    form_url: str | None = None  # URL where the form was detected (if any)
    competitor_tools: list[CompetitorTool] = Field(default_factory=list)
    classified_at: datetime = Field(default_factory=_utc_now)
    notes: str = ""


class Submission(BaseModel):
    """A test lead we've queued for a prospect. The actual form-fill is
    manual in Phase 1; this is the queue a human works through.

    `expected_sender_phone` / `expected_sender_email` are the prospect's
    published contact details — copied in at queue time so the matcher
    can attribute inbound responses without a join against `prospects`
    at every lookup.
    """

    submission_id: str  # uuid
    prospect_place_id: str
    business_name: str
    vertical: str  # free-form; validated against VerticalRegistry at CLI level
    submission_method: SubmissionMethod
    expected_sender_phone: str | None = None
    expected_sender_email: EmailStr | None = None
    submitted_at: datetime | None = None  # Filled in when human submits


class Response(BaseModel):
    """An inbound message attributed (possibly) to a submission."""

    response_id: str  # uuid
    channel: ResponseChannel
    received_at: datetime
    matched_submission_id: str | None = None
    elapsed_seconds: int | None = None
    sender_phone: str | None = None
    sender_email: EmailStr | None = None
    content_snippet: str = ""


# ---------------------------------------------------------------------------
# Phase 2: automated form submission
# ---------------------------------------------------------------------------


class SubmissionAttemptStatus(StrEnum):
    """Lifecycle of one automated submission attempt.

    A queued attempt starts `PENDING`, flips to `SUBMITTING` while a worker
    owns it, and ends in one of three terminal states. `NEEDS_MANUAL` is the
    graceful-degradation bucket — the submitter tried, couldn't finish (e.g.
    CAPTCHA, auth wall), and bounced the job back to the human queue that
    Phase 1 already supports.
    """

    PENDING = "pending"
    SUBMITTING = "submitting"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_MANUAL = "needs_manual"


TERMINAL_ATTEMPT_STATUSES = frozenset(
    {
        SubmissionAttemptStatus.COMPLETED,
        SubmissionAttemptStatus.FAILED,
        SubmissionAttemptStatus.NEEDS_MANUAL,
    }
)


class SubmissionAttempt(BaseModel):
    """One run of the auto-submitter against a queued `Submission`.

    Multiple attempts per submission are allowed (a FAILED attempt can be
    retried manually from the dashboard) — they stack in creation order, and
    the "latest attempt" is what the UI reports as the current status of the
    underlying submission.
    """

    attempt_id: str  # uuid
    submission_id: str
    status: SubmissionAttemptStatus = SubmissionAttemptStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    form_url: str | None = None
    confirmation_text: str = ""  # "Thanks — we'll be in touch" from the site
    screenshot_path: str | None = None  # Post-submit screenshot path, when real mode
    error_message: str = ""
    logs: list[str] = Field(default_factory=list)
    # `attempt_number` lets the dashboard show "Attempt 2 of N" without a
    # subquery. Maintained by whichever code inserts the attempt.
    attempt_number: int = 1

    def is_terminal(self) -> bool:
        return self.status in TERMINAL_ATTEMPT_STATUSES
