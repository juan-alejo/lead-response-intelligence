"""Dashboard smoke tests via Streamlit AppTest.

Not a full UI test (no browser), but it renders the whole app in-process
and asserts no exception escaped. Catches the class of regression that
manifests as "tab crashes" in prod — missing i18n keys, import cycles,
None dereferences on empty data — without a browser-in-the-loop.

Two runs:
    1. Phase 2 disabled (default) → teaser tab renders.
    2. Phase 2 enabled → live tab + all widgets render.

The dashboard auto-saves a handful of files during first render (the
verticals + locations editors call `save()` when their signatures
differ from the session-state snapshot, which is None on a fresh run).
The `_snapshot_and_restore` fixture isolates our tests from that side
effect so running the smoke tests never mutates committed config.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_PATH = str(_REPO_ROOT / "src" / "dashboard" / "app.py")
_FILES_THAT_AUTOSAVE = [
    _REPO_ROOT / "config" / "locations.yaml",
    _REPO_ROOT / "config" / "verticals.yaml",
    _REPO_ROOT / "data" / "run_history.json",
]


@pytest.fixture(autouse=True)
def _snapshot_and_restore():
    """Snapshot any file the dashboard auto-saves; restore after each test."""
    snapshots: dict[Path, bytes | None] = {
        p: (p.read_bytes() if p.exists() else None) for p in _FILES_THAT_AUTOSAVE
    }
    try:
        yield
    finally:
        for p, content in snapshots.items():
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(content)


def _run(**env: str) -> AppTest:
    """Run the full app with the given env overrides; fail on any exception."""
    original = {k: os.environ.get(k) for k in env}
    try:
        os.environ.update(env)
        at = AppTest.from_file(_APP_PATH, default_timeout=30)
        at.run()
        assert not at.exception, f"dashboard raised: {at.exception}"
        return at
    finally:
        for k, v in original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_dashboard_renders_with_phase_2_disabled() -> None:
    at = _run(PHASE_2_ENABLED="false")
    # Sanity: the Home tab title is always present regardless of data state.
    text_blobs = " ".join(
        m.value for m in at.markdown if hasattr(m, "value")
    )
    # The disabled-phase-2 banner is shown on the Phase 2 tab.
    assert "Phase 2" in text_blobs


def test_dashboard_renders_with_phase_2_enabled() -> None:
    """Flag on — live tab should render without throwing even with an empty DB."""
    at = _run(PHASE_2_ENABLED="true", SUBMITTER_MODE="mock")
    # With phase 2 on, the run-panel button should be present.
    button_labels = [b.label for b in at.button]
    assert any("batch" in label.lower() or "lote" in label.lower() for label in button_labels), (
        f"expected a phase-2 run button, got: {button_labels!r}"
    )


@pytest.mark.parametrize("mode", ["mock", "disabled"])
def test_dashboard_renders_across_submitter_modes(mode: str) -> None:
    """Both modes must render without raising — disabled just greys out the CTA."""
    _run(PHASE_2_ENABLED="true", SUBMITTER_MODE=mode)
