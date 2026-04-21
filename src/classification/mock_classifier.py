"""Heuristic classifier — no LLM, pure pattern matching.

Used for tests and as the `mock` mode default. Also works as a first-pass
prefilter in the hybrid strategy (see `ClaudeClassifier`).
"""

from __future__ import annotations

import re

from ..models import FormType
from .base import FormClassifier

_CHAT_HINTS = re.compile(
    r"intercom|drift|livechat|juvoleads|intaker|tidio|zendesk-chat",
    re.IGNORECASE,
)
_BOOKING_HINTS = re.compile(
    r"calendly|acuityscheduling|meetings\.hubspot|bookingwidget",
    re.IGNORECASE,
)
_CONTACT_HINTS = re.compile(
    r"<form[^>]*(contact|inquiry|quote|consultation)[^>]*>",
    re.IGNORECASE,
)
_INPUT_HINT = re.compile(r"<input[^>]*type=['\"](email|tel|text)['\"]", re.IGNORECASE)


class HeuristicClassifier(FormClassifier):
    """Cheap, deterministic, offline. Good enough for ~70% of real sites."""

    def classify(self, html: str, *, url: str) -> FormType:
        if _CHAT_HINTS.search(html):
            return FormType.CHAT_WIDGET
        if _BOOKING_HINTS.search(html):
            return FormType.BOOKING_WIDGET
        if _CONTACT_HINTS.search(html) or _INPUT_HINT.search(html):
            return FormType.CONTACT_FORM
        return FormType.NONE
