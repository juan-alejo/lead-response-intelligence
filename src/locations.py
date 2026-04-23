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
#
# The `query_suffix` uses the preposition matching the country's primary
# language:
#   - Spanish-speaking locales: "en" (e.g. "en Córdoba, Argentina")
#   - Portuguese (Brazil):       "em" (e.g. "em São Paulo, Brasil")
#   - English-speaking:          "in" (e.g. "in Manhattan, New York")
#
# Country names also match the local language ("España" not "Spain",
# "Brasil" not "Brazil", "México" not "Mexico") — Google Places handles
# accented characters fine and the UI looks consistent with the
# Spanish-first vertical packs.
_BUILTIN_DEFAULTS: tuple[Location, ...] = (
    # --- Argentina (LatAm-first default market) ---
    Location("caba", "CABA (Ciudad de Buenos Aires)", "en Ciudad Autónoma de Buenos Aires, Argentina"),
    Location("gba_norte", "GBA Norte", "en Gran Buenos Aires Norte, Argentina"),
    Location("cordoba_ar", "Córdoba, Argentina", "en Córdoba, Argentina"),
    Location("rosario", "Rosario, Argentina", "en Rosario, Santa Fe, Argentina"),
    Location("mendoza", "Mendoza, Argentina", "en Mendoza, Argentina"),
    Location("argentina_all", "Toda Argentina", "en Argentina"),
    # --- Resto de LatAm ---
    Location("cdmx", "CDMX (Ciudad de México)", "en Ciudad de México, México"),
    Location("mexico_all", "Todo México", "en México"),
    Location("santiago_cl", "Santiago de Chile", "en Santiago, Chile"),
    # --- Brasil (Portuguese prepositions) ---
    Location("sao_paulo", "São Paulo, Brasil", "em São Paulo, Brasil"),
    Location("brasil_all", "Todo Brasil", "em Brasil"),
    # --- España ---
    Location("madrid", "Madrid, España", "en Madrid, España"),
    Location("barcelona", "Barcelona, España", "en Barcelona, España"),
    # --- US / NYC presets (for English operators) ---
    Location("manhattan", "Manhattan, NY", "in Manhattan, New York"),
    Location("brooklyn", "Brooklyn, NY", "in Brooklyn, New York"),
    Location("queens", "Queens, NY", "in Queens, New York"),
    Location("bronx", "Bronx, NY", "in the Bronx, New York"),
    Location("staten_island", "Staten Island, NY", "in Staten Island, New York"),
    Location("usa_all", "All United States", "in the United States"),
)


_registry: LocationRegistry | None = None


def get_location_registry() -> LocationRegistry:
    """Module-level singleton."""
    global _registry
    if _registry is None:
        _registry = LocationRegistry()
    return _registry
