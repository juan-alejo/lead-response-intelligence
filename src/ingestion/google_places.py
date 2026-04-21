"""Google Places prospect source.

Runs in two modes:

- `mock`: read fixture JSON from disk. Zero API calls, zero cost. Used for
  tests, CI, and local dev without a Google billing account.
- `real`: hit Google's Places API (Text Search endpoint). Requires an API
  key with Places API enabled.

Both paths return the same `Prospect` objects — callers don't know or care
which is active. Swap via `PLACES_MODE` env var.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import httpx
from loguru import logger

from ..models import Borough, Prospect, Vertical
from .base import ProspectSource

_PLACES_TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"

_VERTICAL_QUERIES: dict[Vertical, str] = {
    Vertical.LAW_FIRM: "law firm",
    Vertical.HOME_SERVICES: "home services contractor",
    Vertical.MED_SPA: "med spa",
    Vertical.GENERAL: "small business",
}

_BOROUGH_NAMES: dict[Borough, str] = {
    Borough.MANHATTAN: "Manhattan, New York",
    Borough.BROOKLYN: "Brooklyn, New York",
    Borough.QUEENS: "Queens, New York",
    Borough.BRONX: "Bronx, New York",
    Borough.STATEN_ISLAND: "Staten Island, New York",
}


class GooglePlacesSource(ProspectSource):
    def __init__(
        self,
        *,
        mode: str = "mock",
        api_key: str = "",
        mock_fixture: Path = Path("data/fixtures/places.json"),
    ) -> None:
        self.mode = mode
        self.api_key = api_key
        self.mock_fixture = mock_fixture

    def fetch(
        self, vertical: Vertical, borough: Borough, limit: int = 100
    ) -> Iterable[Prospect]:
        if self.mode == "mock":
            return self._fetch_mock(vertical, borough, limit)
        return self._fetch_real(vertical, borough, limit)

    def _fetch_mock(
        self, vertical: Vertical, borough: Borough, limit: int
    ) -> list[Prospect]:
        if not self.mock_fixture.exists():
            logger.warning(f"mock fixture not found: {self.mock_fixture}")
            return []
        raw = json.loads(self.mock_fixture.read_text(encoding="utf-8"))
        prospects: list[Prospect] = []
        for entry in raw:
            if entry.get("vertical") != vertical.value:
                continue
            if entry.get("borough") != borough.value:
                continue
            prospects.append(Prospect(**entry))
            if len(prospects) >= limit:
                break
        logger.info(
            f"[mock] places returned {len(prospects)} prospects "
            f"for {vertical.value} in {borough.value}"
        )
        return prospects

    def _fetch_real(
        self, vertical: Vertical, borough: Borough, limit: int
    ) -> list[Prospect]:
        if not self.api_key:
            raise RuntimeError("GOOGLE_PLACES_API_KEY is required for real mode")
        query = f"{_VERTICAL_QUERIES[vertical]} in {_BOROUGH_NAMES[borough]}"
        logger.info(f"[real] querying Google Places: {query!r}")
        params = {"query": query, "key": self.api_key}
        prospects: list[Prospect] = []
        with httpx.Client(timeout=15.0) as client:
            response = client.get(_PLACES_TEXT_SEARCH, params=params)
            response.raise_for_status()
            data = response.json()
            for result in data.get("results", [])[:limit]:
                prospects.append(
                    Prospect(
                        place_id=result["place_id"],
                        business_name=result["name"],
                        vertical=vertical,
                        borough=borough,
                        website=result.get("website"),
                        phone=result.get("formatted_phone_number"),
                    )
                )
        return prospects
