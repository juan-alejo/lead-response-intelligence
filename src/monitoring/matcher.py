"""Match inbound responses to their originating submissions.

Matching rules, in order of precedence:
  1. Exact email address match against submission.test_email
  2. Normalized phone-number match against submission.test_phone
     (strip all non-digits, compare trailing 10 digits)
  3. Unmatched — response is kept but `matched_submission_id` stays None

The acceptance criteria from the spec calls for ≥95% match rate. The
phone-number normalization is the non-obvious bit: "+1 (555) 123-4567"
and "5551234567" need to land on the same bucket.
"""

from __future__ import annotations

import re

from loguru import logger

from ..models import Response, Submission

_DIGITS = re.compile(r"\D+")


def _normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = _DIGITS.sub("", raw)
    # Keep the trailing 10 digits — handles both +1-prefixed and bare US numbers.
    return digits[-10:] if len(digits) >= 10 else digits


class ResponseMatcher:
    def __init__(self, submissions: list[Submission]) -> None:
        self._by_email: dict[str, Submission] = {}
        self._by_phone: dict[str, Submission] = {}
        for s in submissions:
            if s.expected_sender_email:
                self._by_email[s.expected_sender_email.lower()] = s
            norm = _normalize_phone(s.expected_sender_phone)
            if norm:
                self._by_phone[norm] = s

    def match(self, response: Response) -> Response:
        """Return a new `Response` with matched_submission_id + elapsed_seconds filled."""
        submission = self._lookup(response)
        if submission is None or submission.submitted_at is None:
            return response

        elapsed = int((response.received_at - submission.submitted_at).total_seconds())
        return response.model_copy(
            update={
                "matched_submission_id": submission.submission_id,
                "elapsed_seconds": max(elapsed, 0),
            }
        )

    def match_all(self, responses: list[Response]) -> list[Response]:
        matched = [self.match(r) for r in responses]
        hit_count = sum(1 for r in matched if r.matched_submission_id is not None)
        hit_rate = hit_count / max(len(matched), 1)
        logger.info(
            f"[matcher] matched {hit_count} / {len(matched)} responses ({hit_rate:.0%})"
        )
        return matched

    def _lookup(self, response: Response) -> Submission | None:
        if response.sender_email:
            hit = self._by_email.get(response.sender_email.lower())
            if hit:
                return hit
        norm = _normalize_phone(response.sender_phone)
        if norm:
            return self._by_phone.get(norm)
        return None
