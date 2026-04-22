"""Claude-powered category generator — the Settings-tab "magic" button.

Operator describes their market in free text (country + sector) and the
generator returns a list of `Vertical` rows with queries in the right
language and the right nomenclature for Google Places in that country.

Why this is a selling point, not an afterthought:

- The packs (`config/vertical_packs.yaml`) cover the major LatAm + US + BR
  markets, but there's a long tail — Colombia, Chile, Spain-specific
  flavors of Spanish, Peru, India in English-for-English-queries. Hand-
  coding every regional pack is waste.
- Claude knows the local nomenclature. "Small business" isn't a good
  Google Places query anywhere; "escribanías" is a great one in
  Argentina but meaningless in Mexico; "tintorería" works in both Mexico
  and Argentina but "lavandería" is better in Brazil. Claude picks
  correctly when prompted.
- It demonstrates the LLM value prop at configuration time, not just
  at classification time. Operators say "oh, so Claude helps me set
  this up too" — that's a moment a product-oriented buyer remembers.

Two implementations behind the ABC:

- `MockCategoryGenerator`: returns a pre-baked, language-aware reply. Used
  in demo mode and CI. No API calls. Deterministic.
- `ClaudeCategoryGenerator`: real Claude call. Uses the same `Anthropic`
  client pattern the classifier already uses — so the dependency is
  already in the repo.

Fail-safe behavior: if the Claude call errors (bad key, timeout, rate
limit, JSON parse failure), the UI never gets a partial list — it gets
a `GeneratorError` with a human-readable message that the Settings tab
renders in red. No silent degradation; operators need to know the
"magic button" failed so they don't apply garbage to their config.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger

from .verticals import Vertical

_SYSTEM_PROMPT = """\
You generate search categories for Google Places API queries targeting small
businesses in a specific country and sector.

Requirements for each category you return:
1. `name`: a stable snake_case identifier, lowercase ASCII only, no spaces.
   Use the local-language noun in its shortest form (e.g. `abogados`,
   `dentistas`, `imobiliarias`, `law_firm`).
2. `display_name`: human-friendly label in the operator's language (Spanish
   for Spanish-speaking markets, Portuguese for Brazil, English for US/UK).
3. `query`: the text the operator will send to Google Places API. This MUST
   be a term Google's taxonomy recognizes in that country — don't use
   generic English like "small business" for a Spanish market. Prefer short
   nouns: "abogado", "dentista", "inmobiliaria", "hair salon", "law firm".

Return STRICT JSON in this exact shape, no commentary, no markdown:

    {
      "categories": [
        {"name": "...", "display_name": "...", "query": "..."},
        ...
      ]
    }

Generate between 8 and 15 categories. Err toward more categories when the
sector hint is broad ("servicios profesionales"), fewer when narrow
("consultorios médicos especializados").\
"""


# ---- public types ---------------------------------------------------------


class GeneratorError(RuntimeError):
    """Typed error for generator failures — the Settings tab matches on
    the class, not on the message, so message text can evolve without
    breaking UI branches."""


@dataclass(frozen=True)
class GenerationRequest:
    """Free-text description of what the operator wants. Both fields
    matter: country drives the language, sector drives breadth."""

    country: str          # e.g. "Argentina", "Mexico", "United States"
    sector_hint: str      # e.g. "servicios profesionales", "retail minorista"
    target_count: int = 12


class CategoryGenerator(ABC):
    @abstractmethod
    def generate(self, request: GenerationRequest) -> list[Vertical]:
        """Turn a natural-language request into a validated list of
        `Vertical` rows. Raises `GeneratorError` on any failure."""


# ---- validation utilities -------------------------------------------------

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,60}$")


def _validate_and_dedupe(rows: list[dict]) -> list[Vertical]:
    """Enforce the same invariants the Settings verticals editor enforces.

    - `name` must match the snake_case regex.
    - All three fields must be non-empty strings.
    - Duplicate names dropped (first wins).

    We validate the LLM's output rather than trusting it — even with a
    strict JSON prompt, models occasionally emit a name like "Law Firm"
    or skip a field entirely, and either one would blow up the verticals
    YAML writer.
    """
    cleaned: list[Vertical] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row.get("name", "")).strip()
        display = str(row.get("display_name", "")).strip()
        query = str(row.get("query", "")).strip()
        if not (name and display and query):
            continue
        if not _NAME_RE.match(name):
            continue
        if name in seen:
            continue
        seen.add(name)
        cleaned.append(Vertical(name=name, display_name=display, query=query))
    return cleaned


# ---- mock implementation --------------------------------------------------


class MockCategoryGenerator(CategoryGenerator):
    """Deterministic, offline generator keyed on the country string.

    Returns a language-appropriate sample so demos of the "generate"
    button feel real without any Claude spend. Covers the markets that
    the bundled packs cover (AR / LatAm / US / BR) plus a couple extras
    (Mexico, Spain, Colombia) so the button still looks alive outside
    the pre-baked packs.
    """

    def generate(self, request: GenerationRequest) -> list[Vertical]:
        country_lower = request.country.lower().strip()
        tokens = set(re.split(r"[\s,/;-]+", country_lower))

        # Match on whole-token equality rather than substring so "united states"
        # doesn't match Spain on the "es" substring inside "states".
        for keywords, rows in _MOCK_RESPONSES:
            if any(k in tokens or k == country_lower for k in keywords):
                logger.info(
                    f"[mock-generator] matched country={request.country!r} "
                    f"sector={request.sector_hint!r} → {len(rows)} categories"
                )
                return [Vertical(*r) for r in rows]

        # Unknown country → fall back to a generic English set so the
        # button always produces something (never a GeneratorError in mock).
        logger.info(
            f"[mock-generator] no preset for {request.country!r}, using English fallback"
        )
        return [Vertical(*r) for r in _MOCK_RESPONSES[-1][1]]


_MOCK_RESPONSES: list[tuple[tuple[str, ...], list[tuple[str, str, str]]]] = [
    # --- Argentina ---
    (
        ("argentina", "ar"),
        [
            ("abogados", "Abogados / Estudios jurídicos", "estudio jurídico"),
            ("escribanias", "Escribanías", "escribanía"),
            ("dentistas", "Dentistas / Odontólogos", "odontólogo"),
            ("contadores", "Contadores públicos", "contador público"),
            ("arquitectos", "Arquitectos", "estudio de arquitectura"),
            ("inmobiliarias", "Inmobiliarias", "inmobiliaria"),
            ("esteticas", "Centros de estética", "centro de estética"),
            ("gimnasios", "Gimnasios", "gimnasio"),
            ("veterinarias", "Veterinarias", "veterinaria"),
            ("plomeros", "Plomeros / Gasistas matriculados", "plomero matriculado"),
            ("academias_ingles", "Academias de inglés", "academia de inglés"),
            ("escuelas_conducir", "Escuelas de conducir", "escuela de manejo"),
        ],
    ),
    # --- Mexico ---
    (
        ("mexico", "méxico", "mx"),
        [
            ("abogados", "Abogados", "abogado"),
            ("dentistas", "Dentistas", "dentista"),
            ("notarios", "Notarios públicos", "notario público"),
            ("contadores", "Contadores", "contador"),
            ("arquitectos", "Arquitectos", "arquitecto"),
            ("bienes_raices", "Bienes raíces", "bienes raíces"),
            ("salones_belleza", "Salones de belleza", "salón de belleza"),
            ("gimnasios", "Gimnasios", "gimnasio"),
            ("clinicas_medicas", "Clínicas médicas", "clínica médica"),
            ("veterinarias", "Veterinarias", "veterinaria"),
            ("restaurantes", "Restaurantes", "restaurante"),
        ],
    ),
    # --- Spain ---
    (
        ("spain", "españa", "es"),
        [
            ("abogados", "Abogados / Despachos", "despacho de abogados"),
            ("dentistas", "Dentistas / Clínicas dentales", "clínica dental"),
            ("asesorias", "Asesorías fiscales", "asesoría fiscal"),
            ("arquitectos", "Arquitectos", "estudio de arquitectura"),
            ("inmobiliarias", "Inmobiliarias", "inmobiliaria"),
            ("peluquerias", "Peluquerías", "peluquería"),
            ("gimnasios", "Gimnasios", "gimnasio"),
            ("academias", "Academias de formación", "academia"),
            ("veterinarios", "Clínicas veterinarias", "clínica veterinaria"),
            ("fontaneros", "Fontaneros", "fontanero"),
        ],
    ),
    # --- Brazil ---
    (
        ("brazil", "brasil", "br"),
        [
            ("advogados", "Escritórios de advocacia", "escritório de advocacia"),
            ("dentistas", "Consultórios odontológicos", "consultório odontológico"),
            ("contadores", "Contadores", "contador"),
            ("arquitetos", "Arquitetos", "arquiteto"),
            ("imobiliarias", "Imobiliárias", "imobiliária"),
            ("saloes_beleza", "Salões de beleza", "salão de beleza"),
            ("academias", "Academias", "academia"),
            ("clinicas_medicas", "Clínicas médicas", "clínica médica"),
            ("pet_shops", "Pet shops / Veterinários", "pet shop"),
            ("restaurantes", "Restaurantes", "restaurante"),
            ("escolas_ingles", "Escolas de inglês", "escola de inglês"),
        ],
    ),
    # --- Colombia ---
    (
        ("colombia", "co"),
        [
            ("abogados", "Abogados / Firmas jurídicas", "firma de abogados"),
            ("odontologos", "Odontólogos", "odontólogo"),
            ("contadores", "Contadores", "contador público"),
            ("arquitectos", "Arquitectos", "arquitecto"),
            ("inmobiliarias", "Inmobiliarias", "inmobiliaria"),
            ("peluquerias", "Peluquerías", "peluquería"),
            ("gimnasios", "Gimnasios", "gimnasio"),
            ("veterinarias", "Veterinarias", "veterinaria"),
            ("clinicas_esteticas", "Clínicas estéticas", "clínica estética"),
            ("restaurantes", "Restaurantes", "restaurante"),
        ],
    ),
    # --- English fallback (US/UK/CA/AU) — also the default for unknowns ---
    (
        ("united states", "usa", "us", "united kingdom", "uk", "canada", "australia"),
        [
            ("law_firm", "Law Firm", "law firm"),
            ("dentist", "Dentist", "dentist"),
            ("med_spa", "Med Spa", "med spa"),
            ("chiropractor", "Chiropractor", "chiropractor"),
            ("real_estate_agent", "Real Estate Agency", "real estate agency"),
            ("hair_salon", "Hair Salon", "hair salon"),
            ("accountant", "Accountant", "accountant"),
            ("plumber", "Plumber", "plumber"),
            ("electrician", "Electrician", "electrician"),
            ("veterinarian", "Veterinarian", "veterinarian"),
            ("insurance_agent", "Insurance Agency", "insurance agency"),
            ("hvac", "HVAC Contractor", "hvac contractor"),
        ],
    ),
]


# ---- Claude implementation ------------------------------------------------


class ClaudeCategoryGenerator(CategoryGenerator):
    """Live generator backed by Claude — the actual "magic button".

    Uses the Anthropic SDK the repo already depends on. Failure modes all
    surface as `GeneratorError` with a message the UI can render verbatim.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1200,
    ) -> None:
        if not api_key:
            raise GeneratorError(
                "ANTHROPIC_API_KEY is empty — fill it in Settings → Claude."
            )
        # Lazy import so mock-mode installs don't have to have `anthropic`
        # installed just for the generator module to be importable. In
        # practice Phase 1 pulls the SDK in as a hard dep, but this keeps
        # the boundary clean.
        try:
            from anthropic import Anthropic
        except ImportError as e:  # pragma: no cover
            raise GeneratorError(
                "anthropic SDK not installed; run pip install anthropic"
            ) from e
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, request: GenerationRequest) -> list[Vertical]:
        user_prompt = (
            f"Country: {request.country}\n"
            f"Sector hint: {request.sector_hint}\n"
            f"Target count: {request.target_count} (soft target, 8-15 acceptable)"
        )
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as e:  # noqa: BLE001
            raise GeneratorError(
                f"Claude API call failed: {type(e).__name__}: {e}"
            ) from e

        raw = _extract_text(message)
        if not raw:
            raise GeneratorError("Claude returned an empty response.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            raise GeneratorError(
                f"Claude returned non-JSON output: {e.msg} (position {e.pos})"
            ) from e

        rows = parsed.get("categories")
        if not isinstance(rows, list) or not rows:
            raise GeneratorError(
                "Claude response missing non-empty 'categories' array."
            )

        verticals = _validate_and_dedupe(rows)
        if not verticals:
            raise GeneratorError(
                "Claude returned categories but none passed validation "
                "(bad names / empty fields). Try rephrasing your sector."
            )
        return verticals


def _extract_text(message) -> str:
    """Pull the first text block out of an Anthropic Message — handles the
    list-of-content-blocks shape the SDK returns without leaking SDK types
    into the rest of the module."""
    try:
        parts = message.content  # type: ignore[attr-defined]
    except AttributeError:
        return ""
    for block in parts:
        if getattr(block, "type", None) == "text":
            return block.text.strip()
        text = getattr(block, "text", None)
        if text:
            return text.strip()
    return ""


# ---- factory --------------------------------------------------------------


def build_generator(
    *, mode: str, api_key: str = "", model: str = "claude-sonnet-4-6"
) -> CategoryGenerator:
    """Mode-driven factory. `mode` mirrors every other integration's pattern.

    - `mock`  → `MockCategoryGenerator` (offline, deterministic)
    - `real`  → `ClaudeCategoryGenerator` (live API)
    - `disabled` → a no-op generator that raises — prevents a silent fail
      from a typo in `.env`.
    """
    if mode == "real":
        return ClaudeCategoryGenerator(api_key=api_key, model=model)
    if mode == "mock":
        return MockCategoryGenerator()
    if mode == "disabled":
        raise GeneratorError(
            "Category generator is disabled (CLAUDE_MODE=disabled). "
            "Enable it in Settings → Claude to use this feature."
        )
    raise GeneratorError(f"Unknown generator mode: {mode!r}")
