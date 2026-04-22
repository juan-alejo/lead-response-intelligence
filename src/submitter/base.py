"""Submitter contract — one interface, multiple implementations.

The Phase 1 pipeline produces a `Submission` row per discovered form. The
Phase 2 submitter takes that row + the site URL and actually fills out the
form. The interface is deliberately narrow: give me a request, I give you
back an attempt record. Batching, concurrency, storage — that's the
`SubmissionQueue`'s job.

Every real-world decision the submitter makes (CAPTCHA detected → bounce to
human, form fields not found → fail loud, auth wall → needs_manual) shows
up as `logs` entries and a terminal `SubmissionAttemptStatus`. The
dashboard renders that verbatim so the operator can audit each decision.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models import Submission, SubmissionAttempt


@dataclass(frozen=True)
class LeadIdentity:
    """The fake-lead contact details that get typed into the form.

    Everything is configurable via env vars so each operator can use a
    dedicated test identity they own (recommended — the submitter's
    confirmation replies will flow back to these addresses, and the
    matcher in Phase 1 will attribute them).

    Using a shared default identity in demo mode is fine; in production the
    deliverable includes a checklist item to swap these in the Settings tab.
    """

    full_name: str
    email: str
    phone: str
    company: str
    message: str

    @classmethod
    def default_demo(cls) -> LeadIdentity:
        return cls(
            full_name="Demo Tester",
            email="demo+reachrate@example.com",
            phone="+15555550100",
            company="ReachRate Demo",
            message=(
                "Hi — checking how quickly your team responds to inbound "
                "contact. This is an automated deliverability test."
            ),
        )


@dataclass(frozen=True)
class SubmissionRequest:
    """Input to `FormSubmitter.submit()`.

    Bundling the three inputs (submission row, form URL, lead identity) into
    one dataclass means we can evolve the contract (e.g. passing a hint from
    the classifier about chat vs form) without renaming the interface.
    """

    submission: Submission
    form_url: str
    lead: LeadIdentity


class FormSubmitter(ABC):
    """Every submitter implementation speaks this interface.

    - `MockFormSubmitter`: deterministic, offline, used by CI and demos.
    - `PlaywrightFormSubmitter` (not shipped here — spec'd in PHASE_2_SPEC):
      fills real forms in a headless browser, retries on transient errors.

    The return value is a fully-populated `SubmissionAttempt` — status,
    timestamps, duration, logs. The caller persists it; the submitter
    itself is stateless.
    """

    @abstractmethod
    def submit(self, request: SubmissionRequest) -> SubmissionAttempt:
        """Run one attempt against `request`. Always returns — never raises.

        A submitter that encounters an unexpected condition MUST catch it and
        turn it into a FAILED attempt with the exception text in
        `error_message`. Exceptions that leak out break the queue's batch
        loop and lose the half-submitted work.
        """
