"""CSV prospect source — accepts a manually curated list of businesses."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from loguru import logger

from ..models import Borough, Prospect
from .base import ProspectSource


class CSVSource(ProspectSource):
    """Load prospects from a CSV with headers matching the `Prospect` model.

    Required columns: place_id, business_name, vertical, borough.
    Optional: website, phone, email.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(
        self, vertical: str, borough: Borough, limit: int = 100
    ) -> Iterable[Prospect]:
        if not self.path.exists():
            logger.error(f"CSV source not found: {self.path}")
            return []

        prospects: list[Prospect] = []
        with self.path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("vertical") != vertical:
                    continue
                if row.get("borough") != borough.value:
                    continue
                prospects.append(
                    Prospect(
                        place_id=row["place_id"],
                        business_name=row["business_name"],
                        vertical=row["vertical"],
                        borough=Borough(row["borough"]),
                        website=row.get("website") or None,
                        phone=row.get("phone") or None,
                        email=row.get("email") or None,
                    )
                )
                if len(prospects) >= limit:
                    break
        logger.info(f"[csv] loaded {len(prospects)} prospects from {self.path}")
        return prospects
