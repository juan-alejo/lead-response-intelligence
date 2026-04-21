"""Mock Gmail adapter — loads email responses from a JSON fixture.

Fixture format (list of objects):
    {
      "response_id": "email_001",
      "received_at": "2026-04-21T15:02:00Z",
      "sender_email": "admin@acme.law",
      "content_snippet": "Thanks for your inquiry..."
    }

Real Gmail adapter wraps google-api-python-client + stored OAuth tokens
and lives in gmail_real.py (same `ResponseChannelAdapter` contract).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from ..models import Response, ResponseChannel
from .base import ResponseChannelAdapter


class GmailMockAdapter(ResponseChannelAdapter):
    def __init__(self, fixture: Path) -> None:
        self.fixture = fixture

    def pull_new_responses(self) -> list[Response]:
        if not self.fixture.exists():
            logger.warning(f"[gmail-mock] fixture not found: {self.fixture}")
            return []
        raw = json.loads(self.fixture.read_text(encoding="utf-8"))
        out: list[Response] = []
        for entry in raw:
            out.append(
                Response(
                    response_id=entry["response_id"],
                    channel=ResponseChannel.EMAIL,
                    received_at=_parse_dt(entry["received_at"]),
                    sender_email=entry.get("sender_email"),
                    content_snippet=entry.get("content_snippet", ""),
                )
            )
        logger.info(f"[gmail-mock] pulled {len(out)} responses")
        return out


def _parse_dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
