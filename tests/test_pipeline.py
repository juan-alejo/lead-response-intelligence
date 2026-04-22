"""End-to-end pipeline integration: ingestion → classification → reporting.

Uses the committed fixtures under data/fixtures/, so this is a real
integration test of every module wired together, minus live HTTP/APIs.
"""

from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.pipeline import run_full_pipeline


def _settings_for(tmp_path: Path) -> Settings:
    return Settings(
        places_mode="mock",
        claude_mode="mock",
        twilio_mode="mock",
        gmail_mode="mock",
        storage_backend="sqlite",
        sqlite_path=tmp_path / "pipeline.sqlite",
        mock_places_fixture=Path("data/fixtures/places.json"),
        mock_sms_fixture=Path("data/fixtures/sms_responses.json"),
        mock_email_fixture=Path("data/fixtures/email_responses.json"),
        report_output_dir=tmp_path / "reports",
    )


def test_full_pipeline_law_firm_manhattan(tmp_path: Path) -> None:
    settings = _settings_for(tmp_path)

    result = run_full_pipeline(
        settings,
        vertical="law_firm",
        location="manhattan",
        limit=50,
        fetch_pages=False,
    )

    # 3 law firms in Manhattan in the fixture.
    assert result.ingested == 3
    assert result.deduplicated == 3
    # Each classified as contact_form (heuristic offline fallback).
    assert result.classified == 3
    assert result.submissions_queued == 3
    # 4 SMS + 2 email + 2 WhatsApp = 8 responses pulled.
    assert result.responses_pulled == 8
    assert result.report_paths["outreach_priority"].exists()
    assert result.report_paths["vertical_stats"].exists()
    assert result.report_paths["competitor_distribution"].exists()
