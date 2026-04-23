"""Dynamic vertical registry — replaces the old hard-coded Vertical enum.

Verticals are user-editable at runtime (via the dashboard's Settings tab,
which writes to config/verticals.yaml). The pipeline, CLI, and storage
layer treat a vertical as a plain `str`; this module is the single
source of truth for validation, display names, and Google Places queries.

Why a registry instead of an enum:
- A sellable version of this tool needs to support arbitrary client
  verticals (dentists in LA, real-estate agents in Miami, whatever).
- Hardcoding them required a code change + redeploy per client. A YAML
  file + a reload-on-next-run model gets us 90% of multi-tenant ergonomics
  without actual multi-tenancy infra.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger

_DEFAULT_PATH = Path("config/verticals.yaml")


@dataclass(frozen=True)
class Vertical:
    """A single prospect category — name is the stable id; display + query are editable."""

    name: str
    display_name: str
    query: str


class VerticalRegistry:
    """Loads verticals from YAML; provides lookup + validation."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_PATH
        self._by_name: dict[str, Vertical] = {}
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            logger.warning(
                f"vertical config not found at {self.path} — using built-in defaults"
            )
            self._by_name = {v.name: v for v in _BUILTIN_DEFAULTS}
            return
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        entries = raw.get("verticals", [])
        loaded = [Vertical(**entry) for entry in entries]
        if not loaded:
            loaded = list(_BUILTIN_DEFAULTS)
        self._by_name = {v.name: v for v in loaded}
        logger.info(f"[verticals] loaded {len(loaded)} verticals from {self.path}")

    def save(self, verticals: list[Vertical]) -> None:
        """Persist a new set of verticals to disk and reload."""
        payload = {
            "verticals": [
                {"name": v.name, "display_name": v.display_name, "query": v.query}
                for v in verticals
            ]
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        self.reload()

    def all(self) -> list[Vertical]:
        return list(self._by_name.values())

    def names(self) -> list[str]:
        return list(self._by_name.keys())

    def get(self, name: str) -> Vertical:
        if name not in self._by_name:
            raise KeyError(
                f"unknown vertical {name!r} — known: {sorted(self._by_name)}"
            )
        return self._by_name[name]

    def contains(self, name: str) -> bool:
        return name in self._by_name


# Fallback set used when the YAML is missing (first-run / CI).
#
# Since the dashboard's default UI language is Spanish (LatAm is the
# primary market), we ship Spanish defaults by default. An operator
# targeting the US market can apply the "US Local Services" pack from
# Settings to switch to English verticals in one click.
_BUILTIN_DEFAULTS: tuple[Vertical, ...] = (
    Vertical("abogados", "Abogados / Estudios jurídicos", "estudio jurídico"),
    Vertical("dentistas", "Dentistas / Odontólogos", "odontólogo"),
    Vertical("inmobiliarias", "Inmobiliarias", "inmobiliaria"),
    Vertical("contadores", "Contadores públicos", "contador público"),
    Vertical("peluquerias", "Peluquerías", "peluquería"),
)


_registry: VerticalRegistry | None = None


def get_vertical_registry() -> VerticalRegistry:
    """Module-level singleton. Call `.reload()` on it after edits."""
    global _registry
    if _registry is None:
        _registry = VerticalRegistry()
    return _registry


# Backward-compat alias so existing imports (`from .verticals import
# get_registry`) keep working while the rename percolates through the codebase.
get_registry = get_vertical_registry
