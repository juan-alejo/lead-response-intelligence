"""Pre-configured category packs — curated templates for new operators.

A `VerticalPack` is a bundled template: a named, described, language-and-
region-tagged list of `Vertical` rows. Packs ship with the repo under
`config/vertical_packs.yaml` and are read-only at runtime.

Operators apply a pack from the Settings tab: the pack's verticals
replace (or extend) the current `config/verticals.yaml`. This is the
"zero-to-useful" on-ramp — a new operator in Argentina picks
"Servicios locales Argentina" and has a demo-ready pipeline in one
click, instead of hand-typing 10 verticals in Spanish.

Why packs instead of a single huge default list:

1. Localization matters. `"small business"` in Google Places returns
   noise in Spanish-speaking markets because it doesn't match the
   Places taxonomy in any useful way; `"odontólogo"` or
   `"estudio jurídico"` matches cleanly. The packs encode this
   per-market knowledge.

2. Segmentation matters. A US agency selling to law firms doesn't
   want dentists in their report; a LatAm agency selling to all
   local services wants the broader list. The pack catalog lets each
   operator pick the relevant slice.

3. Upgrade path. New packs can ship with repo updates without
   blowing away the operator's current verticals — they explicitly
   opt in via "Apply pack".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger

from .verticals import Vertical

_DEFAULT_PATH = Path("config/vertical_packs.yaml")


@dataclass(frozen=True)
class VerticalPack:
    """A curated named bundle of `Vertical` rows.

    Immutable. Operators don't edit packs; they apply them. If an
    operator wants a custom pack, they generate one via the Category
    Generator (see `src/category_generator.py`) and the generator
    emits a `list[Vertical]` that can be applied directly to the
    vertical registry — no intermediate "save as pack" step.
    """

    name: str
    display_name: str
    description: str
    language: str  # ISO code (es, en, pt, …)
    region: str    # free-form label — "Argentina", "United States", etc.
    verticals: tuple[Vertical, ...]

    def as_vertical_list(self) -> list[Vertical]:
        """Return a fresh list of the pack's verticals — safe to hand to
        `VerticalRegistry.save()` without worrying about shared mutation."""
        return list(self.verticals)


class PackRegistry:
    """Reads packs from YAML. Read-only — packs ship with the repo."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_PATH
        self._by_name: dict[str, VerticalPack] = {}
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            logger.warning(
                f"[packs] config not found at {self.path} — using built-in defaults"
            )
            self._by_name = {p.name: p for p in _BUILTIN_DEFAULTS}
            return

        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        entries = raw.get("packs", [])
        loaded: list[VerticalPack] = []
        for entry in entries:
            try:
                loaded.append(_parse_pack(entry))
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(
                    f"[packs] skipping malformed pack {entry.get('name', '?')!r}: {e}"
                )
        if not loaded:
            loaded = list(_BUILTIN_DEFAULTS)
        self._by_name = {p.name: p for p in loaded}
        logger.info(f"[packs] loaded {len(loaded)} packs from {self.path}")

    def all(self) -> list[VerticalPack]:
        return list(self._by_name.values())

    def names(self) -> list[str]:
        return list(self._by_name.keys())

    def get(self, name: str) -> VerticalPack:
        if name not in self._by_name:
            raise KeyError(
                f"unknown pack {name!r} — known: {sorted(self._by_name)}"
            )
        return self._by_name[name]

    def contains(self, name: str) -> bool:
        return name in self._by_name


def _parse_pack(entry: dict) -> VerticalPack:
    """Turn one YAML dict into a frozen `VerticalPack` — rejects malformed
    rows loud instead of silently dropping a pack mid-load."""
    verticals_raw = entry.get("verticals") or []
    if not verticals_raw:
        raise ValueError("pack has no verticals")
    verticals = tuple(
        Vertical(
            name=v["name"],
            display_name=v["display_name"],
            query=v["query"],
        )
        for v in verticals_raw
    )
    return VerticalPack(
        name=entry["name"],
        display_name=entry["display_name"],
        description=entry.get("description", ""),
        language=entry.get("language", ""),
        region=entry.get("region", ""),
        verticals=verticals,
    )


# ---------------------------------------------------------------------------
# Fallback set — used when the bundled YAML is missing (shouldn't happen in
# a normal install, but CI / pip-install-from-sdist scenarios can strip
# non-Python files). Keeps the product functional without the YAML.
# ---------------------------------------------------------------------------

_BUILTIN_DEFAULTS: tuple[VerticalPack, ...] = (
    VerticalPack(
        name="us_local_services",
        display_name="🇺🇸 US Local Services (fallback)",
        description="Minimal English fallback if config/vertical_packs.yaml is missing.",
        language="en",
        region="United States",
        verticals=(
            Vertical("law_firm", "Law Firm", "law firm"),
            Vertical("dentist", "Dentist", "dentist"),
            Vertical("med_spa", "Med Spa", "med spa"),
            Vertical("real_estate_agent", "Real Estate Agency", "real estate agency"),
        ),
    ),
)


_registry: PackRegistry | None = None


def get_pack_registry() -> PackRegistry:
    """Module-level singleton. Call `.reload()` after a bundled YAML edit."""
    global _registry
    if _registry is None:
        _registry = PackRegistry()
    return _registry


# Convenience function used by the Settings UI and tests alike.
def apply_pack(pack_name: str, *, mode: str = "replace") -> int:
    """Apply a named pack to the vertical registry.

    `mode="replace"` (default): the registry's entire vertical list is
    replaced with the pack's verticals. Any custom verticals the operator
    had are lost.

    `mode="append"`: the pack's verticals are unioned with the current
    ones (by `name`). Duplicates prefer the pack's definition — the
    rationale being that a pack's query is the vetted version.

    Returns the number of verticals in the registry after the apply.
    """
    from .verticals import get_vertical_registry

    if mode not in ("replace", "append"):
        raise ValueError(f"mode must be 'replace' or 'append', got {mode!r}")

    pack = get_pack_registry().get(pack_name)
    registry = get_vertical_registry()

    if mode == "replace":
        merged = pack.as_vertical_list()
    else:  # append
        existing = {v.name: v for v in registry.all()}
        for v in pack.verticals:
            existing[v.name] = v  # pack wins on conflict
        merged = list(existing.values())

    registry.save(merged)
    return len(merged)
