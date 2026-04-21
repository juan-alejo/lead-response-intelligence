"""Mock Twilio adapter — loads SMS / voice responses from a JSON fixture.

Fixture format (list of objects):
    {
      "response_id": "sms_001",
      "channel": "sms",                   # or "phone"
      "received_at": "2026-04-21T15:02:00Z",
      "sender_phone": "+15551234567",
      "content_snippet": "Hi, thanks for reaching out..."
    }

Real Twilio integration lives next to this file (see twilio_real.py) and
shares the same `ResponseChannelAdapter` contract.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from ..models import Response, ResponseChannel
from .base import ResponseChannelAdapter


class TwilioMockAdapter(ResponseChannelAdapter):
    def __init__(self, fixture: Path) -> None:
        self.fixture = fixture

    def pull_new_responses(self) -> list[Response]:
        if not self.fixture.exists():
            logger.warning(f"[twilio-mock] fixture not found: {self.fixture}")
            return []
        raw = json.loads(self.fixture.read_text(encoding="utf-8"))
        out: list[Response] = []
        for entry in raw:
            channel = ResponseChannel(entry["channel"])
            if channel not in {ResponseChannel.SMS, ResponseChannel.PHONE}:
                continue
            out.append(
                Response(
                    response_id=entry["response_id"],
                    channel=channel,
                    received_at=_parse_dt(entry["received_at"]),
                    sender_phone=entry.get("sender_phone"),
                    content_snippet=entry.get("content_snippet", ""),
                )
            )
        logger.info(f"[twilio-mock] pulled {len(out)} responses")
        return out


def _parse_dt(raw: str) -> datetime:
    # Accept '...Z' as UTC.
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
