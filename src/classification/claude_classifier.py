"""LLM-backed form classifier using Anthropic's Claude API.

Why LLM and not a hand-rolled parser: real-world small-business sites are
a zoo — templates, custom builds, agency-of-the-month designs. A regex
matrix that covers all of them is a full-time job. Claude reads the page
and returns a structured classification; cheaper in aggregate than
maintaining the rules.

Strategy is hybrid by default: a cheap heuristic pass first, and only
the ambiguous cases hit the API. For 200 prospects/week at ~$0.005 per
classification, that's about $1/week of Claude spend.
"""

from __future__ import annotations

import json

from anthropic import Anthropic
from loguru import logger

from ..models import FormType
from .base import FormClassifier
from .mock_classifier import HeuristicClassifier

_SYSTEM_PROMPT = """\
You classify the primary inbound-contact mechanism on a small-business webpage.

Return STRICT JSON with a single key "form_type" whose value is exactly one of:
  "contact_form"   — a traditional HTML form with fields like name/email/phone
  "chat_widget"    — an embedded live chat (Intercom, Drift, LiveChat, etc.)
  "booking_widget" — an embedded scheduler (Calendly, Acuity, HubSpot Meetings)
  "none"           — no clear inbound mechanism visible

Pick the most prominent option if the page has multiple. Do not explain.\
"""


class ClaudeClassifier(FormClassifier):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        use_heuristic_prefilter: bool = True,
    ) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.prefilter = HeuristicClassifier() if use_heuristic_prefilter else None

    def classify(self, html: str, *, url: str) -> FormType:
        # Cheap pass — skip the API if the heuristic is confident.
        if self.prefilter is not None:
            cheap = self.prefilter.classify(html, url=url)
            if cheap in {FormType.CHAT_WIDGET, FormType.BOOKING_WIDGET}:
                return cheap

        # Trim html to something Claude can actually chew on — first 20KB
        # covers the head + top of body, which is where widget scripts live.
        trimmed = html[:20_000]
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=64,
                system=_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"URL: {url}\n\nHTML (truncated):\n{trimmed}",
                    }
                ],
            )
            raw = message.content[0].text.strip()
            parsed = json.loads(raw)
            return FormType(parsed["form_type"])
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Claude classification failed for {url}: {e}; falling back to heuristic"
            )
            return HeuristicClassifier().classify(html, url=url)
