"""Pack registry + apply-to-verticals flow.

Covers the three behaviors the Settings-tab apply UI relies on:

1. The bundled YAML loads cleanly and every pack has non-empty verticals.
2. `apply_pack(mode="replace")` wipes the current verticals.
3. `apply_pack(mode="append")` unions + lets pack definitions win on conflict.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.vertical_packs import (
    PackRegistry,
    VerticalPack,
    apply_pack,
    get_pack_registry,
)
from src.verticals import Vertical, VerticalRegistry


def test_bundled_packs_load_cleanly() -> None:
    """Smoke: the committed YAML parses and every pack has verticals."""
    # Call on the singleton to catch misconfig in the bundled YAML,
    # not just a synthetic test fixture.
    registry = get_pack_registry()
    packs = registry.all()
    assert len(packs) >= 3, "expected at least 3 bundled packs"
    for pack in packs:
        assert pack.verticals, f"pack {pack.name} is empty"
        # Every vertical query must be non-empty — empty queries produce
        # empty Google Places results and that silently fails user trust.
        for v in pack.verticals:
            assert v.query.strip(), f"{pack.name}/{v.name} has empty query"


def test_bundled_packs_include_argentina() -> None:
    """The core commercial pitch depends on having a Spanish-first pack."""
    registry = get_pack_registry()
    arg = registry.get("servicios_argentina")
    assert arg.language == "es"
    assert "Argentina" in arg.region
    # At least the core verticals the sales deck promises.
    vertical_names = {v.name for v in arg.verticals}
    assert {"abogados", "dentistas", "inmobiliarias"}.issubset(vertical_names)


def test_pack_registry_loads_custom_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "packs.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "packs": [
                    {
                        "name": "test_pack",
                        "display_name": "Test Pack",
                        "description": "unit test",
                        "language": "es",
                        "region": "Test",
                        "verticals": [
                            {"name": "foo", "display_name": "Foo", "query": "foo query"}
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    registry = PackRegistry(path=yaml_path)
    assert registry.names() == ["test_pack"]
    pack = registry.get("test_pack")
    assert pack.verticals[0].name == "foo"


def test_pack_registry_skips_malformed_entries(tmp_path: Path) -> None:
    """A single bad pack shouldn't take down the whole registry."""
    yaml_path = tmp_path / "packs.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "packs": [
                    {"name": "bad_pack", "display_name": "Broken"},  # no verticals
                    {
                        "name": "good_pack",
                        "display_name": "Good",
                        "verticals": [
                            {"name": "x", "display_name": "X", "query": "x"}
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    registry = PackRegistry(path=yaml_path)
    assert registry.names() == ["good_pack"]


def test_pack_registry_missing_yaml_falls_back(tmp_path: Path) -> None:
    """If the bundled YAML is missing we still get a usable (if minimal) registry."""
    registry = PackRegistry(path=tmp_path / "does-not-exist.yaml")
    assert len(registry.all()) >= 1, "expected builtin fallback"


def test_apply_pack_replace_mode(tmp_path: Path, monkeypatch) -> None:
    """`mode='replace'` wipes existing verticals — typical onboarding flow."""
    verticals_yaml = tmp_path / "verticals.yaml"

    # Patch the verticals singleton to use a temp file.
    from src import verticals as verticals_mod

    monkeypatch.setattr(
        verticals_mod, "_registry", VerticalRegistry(path=verticals_yaml)
    )
    # Seed with a vertical the pack doesn't have.
    verticals_mod.get_vertical_registry().save(
        [Vertical("custom", "Custom", "custom query")]
    )

    count = apply_pack("servicios_argentina", mode="replace")

    registry = verticals_mod.get_vertical_registry()
    names = {v.name for v in registry.all()}
    assert "custom" not in names, "replace mode must drop existing verticals"
    assert count == len(registry.all())
    assert count >= 5


def test_apply_pack_append_mode(tmp_path: Path, monkeypatch) -> None:
    """`mode='append'` unions — custom verticals are preserved."""
    verticals_yaml = tmp_path / "verticals.yaml"
    from src import verticals as verticals_mod

    monkeypatch.setattr(
        verticals_mod, "_registry", VerticalRegistry(path=verticals_yaml)
    )
    verticals_mod.get_vertical_registry().save(
        [Vertical("custom", "Custom", "custom query")]
    )

    apply_pack("servicios_argentina", mode="append")

    registry = verticals_mod.get_vertical_registry()
    names = {v.name for v in registry.all()}
    assert "custom" in names, "append mode must preserve existing verticals"
    assert "abogados" in names


def test_apply_pack_append_pack_wins_on_conflict(tmp_path: Path, monkeypatch) -> None:
    """If operator had a stale query for a name the pack also defines, the
    pack's vetted query wins — otherwise upgrading a pack is useless."""
    verticals_yaml = tmp_path / "verticals.yaml"
    from src import verticals as verticals_mod

    monkeypatch.setattr(
        verticals_mod, "_registry", VerticalRegistry(path=verticals_yaml)
    )
    # Seed with a stale version of a vertical the pack also has.
    verticals_mod.get_vertical_registry().save(
        [Vertical("abogados", "Lawyers (old)", "lawyer")]
    )

    apply_pack("servicios_argentina", mode="append")

    abogados = verticals_mod.get_vertical_registry().get("abogados")
    assert abogados.query == "estudio jurídico"


def test_apply_pack_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="replace.*append"):
        apply_pack("servicios_argentina", mode="upsert")


def test_vertical_pack_as_vertical_list_is_safe() -> None:
    pack = VerticalPack(
        name="p",
        display_name="P",
        description="",
        language="",
        region="",
        verticals=(Vertical("a", "A", "a"),),
    )
    mutable = pack.as_vertical_list()
    mutable.append(Vertical("b", "B", "b"))
    # Original pack untouched.
    assert len(pack.verticals) == 1
