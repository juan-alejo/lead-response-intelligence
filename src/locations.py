"""Dynamic location registry — user-editable targeting zones.

Mirrors the design of `src.verticals`: every searchable location is
defined in a YAML file that the operator can edit through the dashboard's
Settings tab. That unlocks the product for clients anywhere in the
world without a code change — an Argentine operator adds "CABA" and
"Córdoba", a Brazilian client adds "São Paulo" and "Rio", an
enterprise client adds "All of the United States" at country granularity.

Each `Location` has three fields:
- `name`: stable id (snake_case, used by storage + CLI).
- `display_name`: human-friendly label shown in dropdowns.
- `query_suffix`: the string appended to Google Places queries, after
  the vertical query. E.g., vertical="law firm" + suffix="in Manhattan,
  New York" → "law firm in Manhattan, New York".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger

_DEFAULT_PATH = Path("config/locations.yaml")


@dataclass(frozen=True)
class Location:
    name: str
    display_name: str
    query_suffix: str


class LocationRegistry:
    """Loads locations from YAML; provides lookup + validation."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_PATH
        self._by_name: dict[str, Location] = {}
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            logger.warning(
                f"location config not found at {self.path} — using built-in defaults"
            )
            self._by_name = {loc.name: loc for loc in _BUILTIN_DEFAULTS}
            return
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        entries = raw.get("locations", [])
        loaded = [Location(**entry) for entry in entries]
        if not loaded:
            loaded = list(_BUILTIN_DEFAULTS)
        self._by_name = {loc.name: loc for loc in loaded}
        logger.info(f"[locations] loaded {len(loaded)} locations from {self.path}")

    def save(self, locations: list[Location]) -> None:
        """Persist a new set of locations and reload in place."""
        payload = {
            "locations": [
                {
                    "name": loc.name,
                    "display_name": loc.display_name,
                    "query_suffix": loc.query_suffix,
                }
                for loc in locations
            ]
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        self.reload()

    def all(self) -> list[Location]:
        return list(self._by_name.values())

    def names(self) -> list[str]:
        return list(self._by_name.keys())

    def get(self, name: str) -> Location:
        if name not in self._by_name:
            raise KeyError(
                f"unknown location {name!r} — known: {sorted(self._by_name)}"
            )
        return self._by_name[name]

    def contains(self, name: str) -> bool:
        return name in self._by_name


# Fallback defaults — curated so the YAML being missing still produces
# a credible demo set covering both hemispheres.
_BUILTIN_DEFAULTS: tuple[Location, ...] = (
    # --- NYC (original defaults) ---
    Location("manhattan", "Manhattan, NY", "in Manhattan, New York"),
    Location("brooklyn", "Brooklyn, NY", "in Brooklyn, New York"),
    Location("queens", "Queens, NY", "in Queens, New York"),
    Location("bronx", "Bronx, NY", "in the Bronx, New York"),
    Location("staten_island", "Staten Island, NY", "in Staten Island, New York"),
    # --- Argentina ---
    Location("caba", "CABA (Ciudad de Buenos Aires)", "in Ciudad Autónoma de Buenos Aires, Argentina"),
    Location("gba_norte", "GBA Norte", "in Gran Buenos Aires Norte, Argentina"),
    Location("cordoba_ar", "Córdoba, Argentina", "in Córdoba, Argentina"),
    Location("rosario", "Rosario, Argentina", "in Rosario, Santa Fe, Argentina"),
    Location("mendoza", "Mendoza, Argentina", "in Mendoza, Argentina"),
    Location("argentina_all", "Toda Argentina", "in Argentina"),
    # --- LatAm presets ---
    Location("cdmx", "CDMX (Ciudad de México)", "in Ciudad de México, Mexico"),
    Location("sao_paulo", "São Paulo, Brasil", "in São Paulo, Brazil"),
    Location("santiago_cl", "Santiago de Chile", "in Santiago, Chile"),
    # --- Europa ---
    Location("madrid", "Madrid, España", "in Madrid, Spain"),
    Location("barcelona", "Barcelona, España", "in Barcelona, Spain"),
    # --- Country-level ---
    Location("mexico_all", "Todo México", "in Mexico"),
    Location("usa_all", "All United States", "in the United States"),
)


_registry: LocationRegistry | None = None


def get_location_registry() -> LocationRegistry:
    """Module-level singleton."""
    global _registry
    if _registry is None:
        _registry = LocationRegistry()
    return _registry
