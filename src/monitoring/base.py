"""Contract for any inbound channel (SMS, email, voice).

Each adapter yields `Response` rows; the matcher handles attribution. Real
adapters (live Twilio webhook, Gmail IMAP) implement the same interface as
the mocks — swap via env var, the rest of the pipeline doesn't change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Response


class ResponseChannelAdapter(ABC):
    @abstractmethod
    def pull_new_responses(self) -> list[Response]:
        """Return all unseen responses since last poll (or since fixture start)."""
