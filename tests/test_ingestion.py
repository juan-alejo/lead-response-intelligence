"""Prospect ingestion: CSV source, Google Places mock, dedup window."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from src.ingestion import CSVSource, Deduplicator, GooglePlacesSource
from src.models import Borough, Prospect

_FIXTURE = [
    {
        "place_id": "p1",
        "business_name": "Acme Law",
        "vertical": "law_firm",
        "borough": "manhattan",
        "website": "https://acme.example.com",
        "phone": "+12125551111",
    },
    {
        "place_id": "p2",
        "business_name": "Beta HVAC",
        "vertical": "home_services",
        "borough": "brooklyn",
        "website": "https://beta.example.com",
    },
]


def test_mock_places_filters_by_vertical_and_borough(tmp_path: Path) -> None:
    f = tmp_path / "places.json"
    f.write_text(json.dumps(_FIXTURE))

    src = GooglePlacesSource(mode="mock", mock_fixture=f)

    manhattan_law = list(src.fetch("law_firm", Borough.MANHATTAN))
    brooklyn_home = list(src.fetch("home_services", Borough.BROOKLYN))
    queens_law = list(src.fetch("law_firm", Borough.QUEENS))

    assert [p.place_id for p in manhattan_law] == ["p1"]
    assert [p.place_id for p in brooklyn_home] == ["p2"]
    assert queens_law == []


def test_mock_places_respects_limit(tmp_path: Path) -> None:
    big = [
        {
            "place_id": f"p{i}",
            "business_name": f"Biz {i}",
            "vertical": "law_firm",
            "borough": "manhattan",
        }
        for i in range(10)
    ]
    f = tmp_path / "places.json"
    f.write_text(json.dumps(big))

    src = GooglePlacesSource(mode="mock", mock_fixture=f)
    result = list(src.fetch("law_firm", Borough.MANHATTAN, limit=3))

    assert len(result) == 3


def test_csv_source_loads_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "prospects.csv"
    csv_path.write_text(
        "place_id,business_name,vertical,borough,website,phone,email\n"
        "c1,Acme Law,law_firm,manhattan,https://acme.example.com,+12125551111,\n"
        "c2,Beta HVAC,home_services,brooklyn,https://beta.example.com,,info@beta.example.com\n",
        encoding="utf-8",
    )

    rows = list(CSVSource(csv_path).fetch("law_firm", Borough.MANHATTAN))
    assert len(rows) == 1
    assert rows[0].business_name == "Acme Law"


def test_dedup_filters_recent_place_ids() -> None:
    from src.models import _utc_now

    now = _utc_now()
    recent = {"p1": now - timedelta(days=5), "p2": now - timedelta(days=120)}

    dedup = Deduplicator(recent, window_days=90)

    fresh = dedup.filter(
        [
            Prospect(
                place_id="p1",
                business_name="X",
                vertical="law_firm",
                borough=Borough.MANHATTAN,
            ),
            Prospect(
                place_id="p2",
                business_name="Y",
                vertical="law_firm",
                borough=Borough.MANHATTAN,
            ),
            Prospect(
                place_id="p3",
                business_name="Z",
                vertical="law_firm",
                borough=Borough.MANHATTAN,
            ),
        ]
    )

    assert [p.place_id for p in fresh] == ["p2", "p3"]
