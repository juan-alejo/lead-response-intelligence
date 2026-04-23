"""End-to-end pipeline integration: ingestion → classification → reporting.

Uses the committed fixtures under data/fixtures/, so this is a real
integration test of every module wired together, minus live HTTP/APIs.
"""

from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.pipeline import Pipeline, run_all_verticals, run_full_pipeline
from src.storage import SQLiteStore

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _settings_for(tmp_path: Path, **overrides) -> Settings:
    """Fixture paths are absolutized so tests that monkeypatch.chdir still
    resolve bundled fixtures correctly."""
    base = dict(
        places_mode="mock",
        claude_mode="mock",
        twilio_mode="mock",
        gmail_mode="mock",
        storage_backend="sqlite",
        sqlite_path=tmp_path / "pipeline.sqlite",
        mock_places_fixture=_REPO_ROOT / "data/fixtures/places.json",
        mock_sms_fixture=_REPO_ROOT / "data/fixtures/sms_responses.json",
        mock_email_fixture=_REPO_ROOT / "data/fixtures/email_responses.json",
        mock_whatsapp_fixture=_REPO_ROOT / "data/fixtures/whatsapp_responses.json",
        mock_classifications_fixture=(
            _REPO_ROOT / "data/fixtures/classifications.json"
        ),
        report_output_dir=tmp_path / "reports",
    )
    base.update(overrides)
    return Settings(**base)


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
    # Responses aggregated across all three channels in the fixtures:
    # 4 SMS + 5 email + 6 WhatsApp = 15. Includes Argentine-locale entries
    # added alongside the Spanish bundled verticals.
    assert result.responses_pulled == 15
    assert result.report_paths["outreach_priority"].exists()
    assert result.report_paths["vertical_stats"].exists()
    assert result.report_paths["competitor_distribution"].exists()


def _isolate_run_history(monkeypatch, tmp_path: Path) -> None:
    """`run_all_verticals` calls `_append_run_history` with a hardcoded
    `data/run_history.json` path. Changing CWD to tmp_path keeps the test
    from mutating the committed file."""
    monkeypatch.chdir(tmp_path)


def test_phase_2_disabled_by_default_no_attempts_written(
    tmp_path: Path, monkeypatch
) -> None:
    """Existing Phase 1 installs must not suddenly start auto-submitting."""
    _isolate_run_history(monkeypatch, tmp_path)
    settings = _settings_for(tmp_path)
    # Run the full weekly pipeline — the Phase 2 hook is inside run_all_verticals.
    run_all_verticals(settings, location="caba", limit=50, fetch_pages=False)

    store = SQLiteStore(settings.sqlite_path)
    assert store.all_attempts() == []


def test_phase_2_enabled_produces_attempts(tmp_path: Path, monkeypatch) -> None:
    """With the flag on, every queued submission gets a MockFormSubmitter attempt."""
    _isolate_run_history(monkeypatch, tmp_path)
    settings = _settings_for(tmp_path, phase_2_enabled=True, submitter_mode="mock")

    result = run_all_verticals(
        settings, location="caba", limit=50, fetch_pages=False
    )

    store = SQLiteStore(settings.sqlite_path)
    attempts = store.all_attempts()
    # There's at least one queued submission per vertical × fixture — all of
    # them should have exactly one attempt after the run.
    assert len(attempts) >= 1
    assert len(attempts) == result.submissions_queued
    assert (
        result.auto_submitted + result.auto_failed + result.auto_needs_manual
        == len(attempts)
    )


def test_phase_2_submitter_mode_disabled_skips(
    tmp_path: Path, monkeypatch
) -> None:
    """`submitter_mode=disabled` cleanly short-circuits even when the flag is on."""
    _isolate_run_history(monkeypatch, tmp_path)
    settings = _settings_for(
        tmp_path, phase_2_enabled=True, submitter_mode="disabled"
    )

    result = run_all_verticals(
        settings, location="caba", limit=50, fetch_pages=False
    )

    store = SQLiteStore(settings.sqlite_path)
    assert store.all_attempts() == []
    assert result.auto_submitted == 0


def test_phase_2_real_mode_raises_until_implemented(tmp_path: Path) -> None:
    """Guard against a silent config typo that puts prod on mock data."""
    import pytest

    settings = _settings_for(tmp_path, phase_2_enabled=True, submitter_mode="real")
    pipeline = Pipeline(settings)
    with pytest.raises(NotImplementedError, match="PHASE_2_SPEC"):
        pipeline.run_form_submission()
