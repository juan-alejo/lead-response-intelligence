"""Deduplication — skip prospects already tested in the last N days.

Dedup key is `place_id`. That's the stable Google identifier; business
names vary between sources (capitalization, legal suffixes like "LLC")
so name-based dedup is a trap.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from ..models import Prospect, _utc_now


class Deduplicator:
    def __init__(self, recent_place_ids_with_dates: dict[str, datetime], window_days: int = 90):
        self._recent: dict[str, datetime] = recent_place_ids_with_dates
        self._cutoff = _utc_now() - timedelta(days=window_days)

    def filter(self, prospects: Iterable[Prospect]) -> list[Prospect]:
        """Return only prospects NOT tested within the window."""
        fresh: list[Prospect] = []
        for p in prospects:
            last_seen = self._recent.get(p.place_id)
            if last_seen is None or last_seen < self._cutoff:
                fresh.append(p)
        return fresh

    @classmethod
    def from_place_ids(cls, place_ids: Iterable[str], window_days: int = 90) -> Deduplicator:
        """Convenience: treat every id as 'just tested now' (worst case for dedup)."""
        now = _utc_now()
        return cls({pid: now for pid in place_ids}, window_days=window_days)
