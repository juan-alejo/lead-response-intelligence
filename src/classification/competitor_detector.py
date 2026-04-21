"""Regex-based detection of competitor tools via script tag signatures.

This is a pure-HTML parse; no LLM needed. Chat widgets and booking tools
all ship a script tag or embed snippet that's stable enough to fingerprint.

Adding a new tool: append to `_SIGNATURES`. Each entry is (tool, patterns)
where patterns is a list of regexes checked against the full HTML.
"""

from __future__ import annotations

import re

from ..models import CompetitorTool

_SIGNATURES: list[tuple[CompetitorTool, list[re.Pattern]]] = [
    (
        CompetitorTool.INTERCOM,
        [
            re.compile(r"widget\.intercom\.io", re.IGNORECASE),
            re.compile(r"\bIntercom\b\s*\(", re.IGNORECASE),
        ],
    ),
    (
        CompetitorTool.DRIFT,
        [
            re.compile(r"js\.driftt\.com", re.IGNORECASE),
            re.compile(r"drift\.com/embed", re.IGNORECASE),
        ],
    ),
    (
        CompetitorTool.LIVECHAT,
        [re.compile(r"cdn\.livechatinc\.com", re.IGNORECASE)],
    ),
    (
        CompetitorTool.INTAKER,
        [re.compile(r"intaker\.com", re.IGNORECASE)],
    ),
    (
        CompetitorTool.JUVO_LEADS,
        [re.compile(r"juvoleads\.com", re.IGNORECASE)],
    ),
    (
        CompetitorTool.CALENDLY,
        [
            re.compile(r"assets\.calendly\.com", re.IGNORECASE),
            re.compile(r"calendly\.com/embed", re.IGNORECASE),
        ],
    ),
    (
        CompetitorTool.ACUITY,
        [re.compile(r"acuityscheduling\.com", re.IGNORECASE)],
    ),
    (
        CompetitorTool.HUBSPOT_MEETINGS,
        [
            re.compile(r"meetings\.hubspot\.com", re.IGNORECASE),
            re.compile(r"js\.hs-scripts\.com", re.IGNORECASE),
        ],
    ),
]


class CompetitorDetector:
    """Scan HTML for known competitor tool signatures. Deterministic, no LLM."""

    def detect(self, html: str) -> list[CompetitorTool]:
        found: list[CompetitorTool] = []
        for tool, patterns in _SIGNATURES:
            if any(p.search(html) for p in patterns):
                found.append(tool)
        return found
