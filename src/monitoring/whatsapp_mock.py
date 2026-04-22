"""Mock WhatsApp adapter — structurally identical to the SMS mock.

In production, WhatsApp Business API messages arrive via a Twilio webhook on
a separate endpoint, but the payload shape (sender phone, timestamp, body)
matches closely enough that the matcher handles them identically.

For LatAm clients where WhatsApp is the dominant response channel, this
adapter is the one that matters most — enable it and leave SMS/voice
disabled to skip the unused channel entirely.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from ..models import Response, ResponseChannel
from .base import ResponseChannelAdapter


class WhatsAppMockAdapter(ResponseChannelAdapter):
    def __init__(self, fixture: Path) -> None:
        self.fixture = fixture

    def pull_new_responses(self) -> list[Response]:
        if not self.fixture.exists():
            logger.warning(f"[whatsapp-mock] fixture not found: {self.fixture}")
            return []
        raw = json.loads(self.fixture.read_text(encoding="utf-8"))
        out: list[Response] = []
        for entry in raw:
            out.append(
                Response(
                    response_id=entry["response_id"],
                    channel=ResponseChannel.WHATSAPP,
                    received_at=_parse_dt(entry["received_at"]),
                    sender_phone=entry.get("sender_phone"),
                    content_snippet=entry.get("content_snippet", ""),
                )
            )
        logger.info(f"[whatsapp-mock] pulled {len(out)} responses")
        return out


def _parse_dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
