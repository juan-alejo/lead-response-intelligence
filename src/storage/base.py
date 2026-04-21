"""Storage contract — persists the three core tables.

Keep this minimal. Both SQLite and Airtable implementations speak the
same interface, so the scheduler code doesn't care which is behind it.
Swap via the `STORAGE_BACKEND` env var.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ..models import Prospect, Response, Submission


class Storage(ABC):
    # --- Prospects ---

    @abstractmethod
    def upsert_prospects(self, prospects: list[Prospect]) -> int:
        """Insert or update prospects. Returns count actually written."""

    @abstractmethod
    def recent_place_ids(self, window_days: int = 90) -> dict[str, datetime]:
        """Return place_id → last_tested_at for prospects seen within the window."""

    # --- Submissions ---

    @abstractmethod
    def upsert_submissions(self, submissions: list[Submission]) -> int: ...

    @abstractmethod
    def all_submissions(self) -> list[Submission]: ...

    # --- Responses ---

    @abstractmethod
    def upsert_responses(self, responses: list[Response]) -> int: ...

    @abstractmethod
    def all_responses(self) -> list[Response]: ...
