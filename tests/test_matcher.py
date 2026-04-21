"""Response matcher: email match, phone normalization, unmatched fallback."""

from __future__ import annotations

from datetime import datetime

from src.models import (
    Response,
    ResponseChannel,
    Submission,
    SubmissionMethod,
    Vertical,
)
from src.monitoring import ResponseMatcher


def _sub(sid: str, phone: str, email: str, submitted_at: datetime) -> Submission:
    return Submission(
        submission_id=sid,
        prospect_place_id=f"p_{sid}",
        business_name=f"Biz {sid}",
        vertical=Vertical.LAW_FIRM,
        submission_method=SubmissionMethod.CONTACT_FORM,
        expected_sender_phone=phone,
        expected_sender_email=email,
        submitted_at=submitted_at,
    )


def _resp(rid: str, *, phone: str | None = None, email: str | None = None,
          received_at: datetime = datetime(2026, 4, 21, 14, 30)) -> Response:
    return Response(
        response_id=rid,
        channel=ResponseChannel.SMS if phone else ResponseChannel.EMAIL,
        received_at=received_at,
        sender_phone=phone,
        sender_email=email,
    )


def test_exact_email_match() -> None:
    sub = _sub("s1", "+15555550100", "test@example.com", datetime(2026, 4, 21, 14, 0))
    matcher = ResponseMatcher([sub])

    matched = matcher.match(_resp("r1", email="test@example.com"))

    assert matched.matched_submission_id == "s1"
    assert matched.elapsed_seconds == 30 * 60


def test_email_match_is_case_insensitive() -> None:
    sub = _sub("s1", "+15555550100", "Test@Example.com", datetime(2026, 4, 21, 14, 0))
    matcher = ResponseMatcher([sub])

    matched = matcher.match(_resp("r1", email="test@example.com"))

    assert matched.matched_submission_id == "s1"


def test_phone_match_normalizes_formatting() -> None:
    sub = _sub("s1", "+1 (555) 555-0100", "test@example.com", datetime(2026, 4, 21, 14, 0))
    matcher = ResponseMatcher([sub])

    # Caller sends a bare 10-digit number — should still match.
    matched = matcher.match(_resp("r1", phone="5555550100"))
    assert matched.matched_submission_id == "s1"

    # And a differently-formatted +1 number.
    matched2 = matcher.match(_resp("r2", phone="+1-555-555-0100"))
    assert matched2.matched_submission_id == "s1"


def test_unmatched_response_keeps_no_submission_id() -> None:
    sub = _sub("s1", "+15555550100", "test@example.com", datetime(2026, 4, 21, 14, 0))
    matcher = ResponseMatcher([sub])

    matched = matcher.match(_resp("r1", phone="+15559999999"))
    assert matched.matched_submission_id is None
    assert matched.elapsed_seconds is None


def test_match_all_hits_95_percent_on_golden_set() -> None:
    """Acceptance criterion: ≥95% of well-formed responses are attributable."""
    submissions = [
        _sub("s1", "+15555550100", "a@example.com", datetime(2026, 4, 21, 14, 0)),
        _sub("s2", "+15555550200", "b@example.com", datetime(2026, 4, 21, 14, 0)),
        _sub("s3", "+15555550300", "c@example.com", datetime(2026, 4, 21, 14, 0)),
        _sub("s4", "+15555550400", "d@example.com", datetime(2026, 4, 21, 14, 0)),
    ]
    matcher = ResponseMatcher(submissions)

    responses = [
        _resp("r1", email="a@example.com"),
        _resp("r2", phone="5555550200"),
        _resp("r3", phone="+1-555-555-0300"),
        _resp("r4", email="D@example.com"),  # case-insensitive
    ]
    matched = matcher.match_all(responses)

    hits = sum(1 for r in matched if r.matched_submission_id)
    assert hits / len(matched) >= 0.95
