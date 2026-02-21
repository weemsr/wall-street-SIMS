"""Tests for Headline Engine."""

import random

import pytest

from wallstreet.agents.headline_engine import generate_headlines
from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.events import ShockEvent
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import Headline


class TestHeadlineEngine:
    def test_generates_headlines(self, sample_macro_bull: MacroState) -> None:
        """Always produces at least 2 headlines."""
        rng = random.Random(42)
        headlines = generate_headlines(sample_macro_bull, [], rng)
        assert len(headlines) >= 2

    def test_headline_count_range(self, sample_macro_bull: MacroState) -> None:
        """Always 2-4 headlines."""
        for seed in range(100):
            rng = random.Random(seed)
            headlines = generate_headlines(sample_macro_bull, [], rng)
            assert 2 <= len(headlines) <= 4

    def test_headline_structure(self, sample_macro_bull: MacroState) -> None:
        """Each headline has text and valid sentiment."""
        rng = random.Random(42)
        headlines = generate_headlines(sample_macro_bull, [], rng)
        for hl in headlines:
            assert isinstance(hl, Headline)
            assert len(hl.text) > 0
            assert hl.sentiment in ("bullish", "bearish", "mixed")

    def test_event_triggers_headline(self) -> None:
        """Shock events produce event-specific headlines."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        event = ShockEvent(
            template_name="Oil Price Spike",
            description="Oil prices surge on supply concerns.",
            sector_effects={Sector.ENERGY: 0.05, Sector.CONSUMER: -0.02},
            vol_impact=0.1,
            week=1,
        )
        rng = random.Random(42)
        headlines = generate_headlines(macro, [event], rng)
        texts = [h.text.lower() for h in headlines]
        # At least one headline should mention oil or energy
        assert any("oil" in t or "crude" in t or "energy" in t for t in texts)

    def test_crisis_vol_headline(self) -> None:
        """Crisis volatility should generate crisis-specific headlines."""
        macro = MacroState(
            regime=Regime.BEAR,
            volatility_state=VolatilityState.CRISIS,
            rate_direction=RateDirection.FALLING,
            week=1,
        )
        rng = random.Random(42)
        headlines = generate_headlines(macro, [], rng)
        texts = " ".join(h.text.lower() for h in headlines)
        # Should contain panic, fear, or circuit breaker related language
        assert any(word in texts for word in ["panic", "fear", "vix", "circuit", "historic"])

    def test_all_regimes_produce_headlines(self) -> None:
        """Every regime produces valid headlines."""
        for regime in Regime:
            macro = MacroState(
                regime=regime,
                volatility_state=VolatilityState.NORMAL,
                rate_direction=RateDirection.STABLE,
                week=1,
            )
            rng = random.Random(42)
            headlines = generate_headlines(macro, [], rng)
            assert len(headlines) >= 2

    def test_reproducible(self, sample_macro_bull: MacroState) -> None:
        """Same seed produces same headlines."""
        h1 = generate_headlines(sample_macro_bull, [], random.Random(42))
        h2 = generate_headlines(sample_macro_bull, [], random.Random(42))
        assert len(h1) == len(h2)
        for a, b in zip(h1, h2):
            assert a.text == b.text
