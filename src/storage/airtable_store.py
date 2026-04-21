"""Airtable implementation — production system of record.

Skeleton implementation. Real wiring uses `pyairtable`. We keep this
minimal and document the expected base schema below so anyone cloning
the project can reproduce it in their own Airtable workspace.

Expected base schema:

    Table: prospects
      - place_id (Single line text, primary)
      - business_name (Single line text)
      - vertical (Single select: law_firm, home_services, med_spa, general)
      - borough (Single select: manhattan, brooklyn, queens, bronx, staten_island)
      - website (URL)
      - phone (Phone)
      - email (Email)
      - discovered_at (Date)

    Table: submissions
      - submission_id (Single line text, primary)
      - prospect_place_id (Single line text; links to prospects.place_id)
      - business_name (Single line text)
      - vertical (Single select)
      - submission_method (Single select)
      - test_phone (Phone)
      - test_email (Email)
      - submitted_at (Date)

    Table: responses
      - response_id (Single line text, primary)
      - channel (Single select: sms, email, phone)
      - received_at (Date)
      - matched_submission_id (Single line text)
      - elapsed_seconds (Number)
      - sender_phone (Phone)
      - sender_email (Email)
      - content_snippet (Long text)
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from ..models import Prospect, Response, Submission
from .base import Storage


class AirtableStore(Storage):
    """Thin wrapper around pyairtable.

    Not fully implemented — swap in real methods following the schema above.
    The SQLite implementation is feature-complete and what CI / local dev
    actually exercises. This class exists to document the production path
    and to let the scheduler code be storage-agnostic.
    """

    def __init__(self, api_key: str, base_id: str) -> None:
        if not api_key or not base_id:
            raise RuntimeError("AIRTABLE_API_KEY and AIRTABLE_BASE_ID required")
        # Lazy import so projects using SQLite don't have to install pyairtable
        # just to type-check.
        try:
            from pyairtable import Api
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "pyairtable is required for the Airtable backend: pip install pyairtable"
            ) from e
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        logger.info(f"[airtable] connected to base {base_id}")

    def _not_implemented(self) -> None:
        raise NotImplementedError(
            "AirtableStore is a schema reference stub. Implement the "
            "pyairtable-backed methods against the documented schema, or use "
            "SQLiteStore for local/CI."
        )

    def upsert_prospects(self, prospects: list[Prospect]) -> int:
        self._not_implemented()

    def recent_place_ids(self, window_days: int = 90) -> dict[str, datetime]:
        self._not_implemented()

    def upsert_submissions(self, submissions: list[Submission]) -> int:
        self._not_implemented()

    def all_submissions(self) -> list[Submission]:
        self._not_implemented()

    def upsert_responses(self, responses: list[Response]) -> int:
        self._not_implemented()

    def all_responses(self) -> list[Response]:
        self._not_implemented()
