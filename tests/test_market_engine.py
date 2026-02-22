"""Tests for market engine: regime transitions and return generation."""

import random

import pytest

from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.market import MacroState
from wallstreet.market_engine.regime import advance_macro_state
from wallstreet.market_engine.returns import generate_sector_returns, apply_events
from wallstreet.models.events import ShockEvent


class TestRegimeTransition:
    def test_reproducible(self) -> None:
        """Same seed produces same regime sequence."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        results1 = []
        rng1 = random.Random(42)
        state = macro
        for _ in range(20):
            state = advance_macro_state(state, rng1)
            results1.append(state.regime)

        results2 = []
        rng2 = random.Random(42)
        state = macro
        for _ in range(20):
            state = advance_macro_state(state, rng2)
            results2.append(state.regime)

        assert results1 == results2

    def test_valid_states(self) -> None:
        """All transitions produce valid enum values."""
        rng = random.Random(99)
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        for _ in range(100):
            macro = advance_macro_state(macro, rng)
            assert macro.regime in Regime
            assert macro.volatility_state in VolatilityState
            assert macro.rate_direction in RateDirection

    def test_transitions_from_all_regimes(self) -> None:
        """Transitions work from every starting regime."""
        rng = random.Random(42)
        for regime in Regime:
            macro = MacroState(
                regime=regime,
                volatility_state=VolatilityState.NORMAL,
                rate_direction=RateDirection.STABLE,
                week=1,
            )
            new_macro = advance_macro_state(macro, rng)
            assert new_macro.regime in Regime


class TestSectorReturns:
    def test_reproducible(self, sample_macro_bull: MacroState) -> None:
        """Same seed, same state produces identical returns."""
        rng1 = random.Random(42)
        ret1 = generate_sector_returns(sample_macro_bull, rng1)

        rng2 = random.Random(42)
        ret2 = generate_sector_returns(sample_macro_bull, rng2)

        for sector in Sector:
            assert ret1[sector] == pytest.approx(ret2[sector])

    def test_all_sectors_present(self, sample_macro_bull: MacroState) -> None:
        rng = random.Random(42)
        ret = generate_sector_returns(sample_macro_bull, rng)
        assert set(ret.keys()) == set(Sector)

    def test_returns_clamped(self) -> None:
        """Returns never exceed +/- 30%."""
        rng = random.Random(42)
        # Use crisis volatility to push returns toward extremes
        macro = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.CRISIS,
            rate_direction=RateDirection.FALLING,
            week=1,
        )
        for i in range(100):
            rng_iter = random.Random(i)
            ret = generate_sector_returns(macro, rng_iter)
            for sector, val in ret.items():
                assert -0.30 <= val <= 0.30, f"Return out of bounds: {sector}={val}"


class TestApplyEvents:
    def test_additive(self) -> None:
        base = {s: 0.01 for s in Sector}
        event = ShockEvent(
            template_name="Test",
            description="test",
            sector_effects={
                Sector.TECH: 0.05, Sector.ENERGY: -0.03,
                Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
                Sector.CONSUMER_DISC: 0.0, Sector.INDUSTRIALS: 0.0,
                Sector.HEALTHCARE: 0.0,
            },
            vol_impact=0.0,
            week=1,
        )
        adjusted = apply_events(base, [event])
        assert adjusted[Sector.TECH] == pytest.approx(0.06)
        assert adjusted[Sector.ENERGY] == pytest.approx(-0.02)
        assert adjusted[Sector.CONSUMER] == pytest.approx(0.01)

    def test_clamping_after_events(self) -> None:
        base = {s: 0.28 for s in Sector}
        event = ShockEvent(
            template_name="Huge",
            description="test",
            sector_effects={
                Sector.TECH: 0.10, Sector.ENERGY: 0.0,
                Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
                Sector.CONSUMER_DISC: 0.0, Sector.INDUSTRIALS: 0.0,
                Sector.HEALTHCARE: 0.0,
            },
            vol_impact=0.0,
            week=1,
        )
        adjusted = apply_events(base, [event])
        assert adjusted[Sector.TECH] == pytest.approx(0.30)  # clamped
