"""Category generator tests.

Covers:
1. MockCategoryGenerator returns language-appropriate rows per country.
2. Validation drops LLM output that would corrupt verticals.yaml.
3. build_generator dispatches mode → implementation correctly.
4. ClaudeCategoryGenerator fails loudly (not silently) on bad responses.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.category_generator import (
    CategoryGenerator,
    ClaudeCategoryGenerator,
    GenerationRequest,
    GeneratorError,
    MockCategoryGenerator,
    _validate_and_dedupe,
    build_generator,
)

# ----------------------------------------------------------------- mock generator


def test_mock_generator_knows_argentina() -> None:
    gen = MockCategoryGenerator()
    verticals = gen.generate(
        GenerationRequest(country="Argentina", sector_hint="servicios profesionales")
    )
    names = {v.name for v in verticals}
    # These exist in the Argentine preset but NOT in the English fallback.
    assert "escribanias" in names
    assert "abogados" in names
    # Queries must be in Spanish.
    abogados = next(v for v in verticals if v.name == "abogados")
    assert "jurídico" in abogados.query or "abogado" in abogados.query


def test_mock_generator_knows_brazil() -> None:
    gen = MockCategoryGenerator()
    verticals = gen.generate(
        GenerationRequest(country="Brasil", sector_hint="serviços profissionais")
    )
    names = {v.name for v in verticals}
    assert "advogados" in names
    assert any("advocacia" in v.query or "advogado" in v.query for v in verticals)


def test_mock_generator_knows_us() -> None:
    gen = MockCategoryGenerator()
    verticals = gen.generate(
        GenerationRequest(country="United States", sector_hint="local services")
    )
    names = {v.name for v in verticals}
    assert "law_firm" in names
    assert "med_spa" in names


def test_mock_generator_falls_back_for_unknown_country() -> None:
    """Generator should never raise in mock mode — unknown country gets English."""
    gen = MockCategoryGenerator()
    verticals = gen.generate(
        GenerationRequest(country="Atlantis", sector_hint="whatever")
    )
    assert len(verticals) >= 5
    # Fallback is English.
    assert any(v.name == "law_firm" for v in verticals)


# ----------------------------------------------------------------- validator


def test_validator_drops_invalid_names() -> None:
    rows = [
        {"name": "Law Firm", "display_name": "Law Firm", "query": "law firm"},  # spaces/caps
        {"name": "123_start_with_digit", "display_name": "X", "query": "x"},
        {"name": "abogados", "display_name": "Abogados", "query": "abogado"},
    ]
    out = _validate_and_dedupe(rows)
    assert [v.name for v in out] == ["abogados"]


def test_validator_drops_empty_fields() -> None:
    rows = [
        {"name": "a", "display_name": "", "query": "x"},
        {"name": "b", "display_name": "B", "query": ""},
        {"name": "c", "display_name": "C", "query": "c-q"},
    ]
    out = _validate_and_dedupe(rows)
    assert [v.name for v in out] == ["c"]


def test_validator_dedupes_by_name() -> None:
    rows = [
        {"name": "abogados", "display_name": "Abogados 1", "query": "q1"},
        {"name": "abogados", "display_name": "Abogados 2", "query": "q2"},
    ]
    out = _validate_and_dedupe(rows)
    assert len(out) == 1
    assert out[0].display_name == "Abogados 1"


# ----------------------------------------------------------------- factory


def test_build_generator_mock() -> None:
    gen = build_generator(mode="mock")
    assert isinstance(gen, MockCategoryGenerator)


def test_build_generator_disabled_raises() -> None:
    with pytest.raises(GeneratorError, match="disabled"):
        build_generator(mode="disabled")


def test_build_generator_unknown_raises() -> None:
    with pytest.raises(GeneratorError, match="Unknown"):
        build_generator(mode="wtf")


def test_build_generator_real_needs_key() -> None:
    """`real` with empty key fails immediately — protects against silently
    running in mock when the operator meant live."""
    with pytest.raises(GeneratorError, match="ANTHROPIC_API_KEY"):
        build_generator(mode="real", api_key="")


# ----------------------------------------------------------------- Claude parser


@dataclass
class _FakeBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeMessage:
    content: list


class _StubAnthropicClient:
    def __init__(self, response_text: str = "", raise_exc: Exception | None = None):
        self._response_text = response_text
        self._raise = raise_exc
        self.messages = self

    def create(self, **kwargs):
        if self._raise:
            raise self._raise
        return _FakeMessage(content=[_FakeBlock(text=self._response_text)])


def _claude_gen_with_stub(stub: _StubAnthropicClient) -> ClaudeCategoryGenerator:
    """Build a real `ClaudeCategoryGenerator` and swap its client for a stub."""
    gen = ClaudeCategoryGenerator.__new__(ClaudeCategoryGenerator)
    gen._client = stub
    gen._model = "claude-sonnet-4-6"
    gen._max_tokens = 1200
    return gen


def test_claude_generator_parses_valid_json() -> None:
    stub = _StubAnthropicClient(
        response_text=(
            '{"categories":['
            '{"name":"abogados","display_name":"Abogados","query":"abogado"},'
            '{"name":"dentistas","display_name":"Dentistas","query":"dentista"}'
            "]}"
        )
    )
    gen = _claude_gen_with_stub(stub)
    verticals = gen.generate(
        GenerationRequest(country="AR", sector_hint="servicios")
    )
    assert [v.name for v in verticals] == ["abogados", "dentistas"]


def test_claude_generator_fails_on_bad_json() -> None:
    stub = _StubAnthropicClient(response_text="not json at all")
    gen = _claude_gen_with_stub(stub)
    with pytest.raises(GeneratorError, match="non-JSON"):
        gen.generate(GenerationRequest(country="AR", sector_hint="x"))


def test_claude_generator_fails_on_empty_categories() -> None:
    stub = _StubAnthropicClient(response_text='{"categories":[]}')
    gen = _claude_gen_with_stub(stub)
    with pytest.raises(GeneratorError, match="categories"):
        gen.generate(GenerationRequest(country="AR", sector_hint="x"))


def test_claude_generator_fails_when_all_rows_invalid() -> None:
    """All rows have invalid names → validator drops everything → loud error."""
    stub = _StubAnthropicClient(
        response_text=(
            '{"categories":['
            '{"name":"Bad Name","display_name":"X","query":"x"},'
            '{"name":"Also Bad","display_name":"Y","query":"y"}'
            "]}"
        )
    )
    gen = _claude_gen_with_stub(stub)
    with pytest.raises(GeneratorError, match="passed validation"):
        gen.generate(GenerationRequest(country="AR", sector_hint="x"))


def test_claude_generator_wraps_api_errors() -> None:
    stub = _StubAnthropicClient(raise_exc=RuntimeError("network down"))
    gen = _claude_gen_with_stub(stub)
    with pytest.raises(GeneratorError, match="Claude API"):
        gen.generate(GenerationRequest(country="AR", sector_hint="x"))


# ----------------------------------------------------------------- ABC conformance


def test_mock_is_a_category_generator() -> None:
    """Sanity — both implementations satisfy the ABC contract."""
    assert isinstance(MockCategoryGenerator(), CategoryGenerator)
