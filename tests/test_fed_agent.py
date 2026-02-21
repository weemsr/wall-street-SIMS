"""Tests for Fed Chair agent."""

import random

import pytest

from wallstreet.agents.fed_agent import FedChairAgent
from wallstreet.models.enums import RateDirection, Regime, VolatilityState
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import FedStatement


class TestFedChairAgent:
    def setup_method(self) -> None:
        self.agent = FedChairAgent()

    def test_generates_fed_statement(self, sample_macro_bull: MacroState) -> None:
        """Agent produces a FedStatement."""
        rng = random.Random(42)
        result = self.agent.generate(sample_macro_bull, rng)
        assert isinstance(result, FedStatement)

    def test_statement_not_empty(self, sample_macro_bull: MacroState) -> None:
        """Statement text is non-empty."""
        rng = random.Random(42)
        result = self.agent.generate(sample_macro_bull, rng)
        assert len(result.statement) > 0

    def test_policy_bias_values(self) -> None:
        """Policy bias matches rate direction."""
        rng = random.Random(42)
        for rate_dir, expected_bias in [
            (RateDirection.RISING, "tightening"),
            (RateDirection.STABLE, "neutral"),
            (RateDirection.FALLING, "easing"),
        ]:
            macro = MacroState(
                regime=Regime.BULL,
                volatility_state=VolatilityState.NORMAL,
                rate_direction=rate_dir,
                week=1,
            )
            result = self.agent.generate(macro, rng)
            assert result.policy_bias == expected_bias

    def test_confidence_in_range(self) -> None:
        """Confidence level is always 0-1."""
        for regime in Regime:
            for rate_dir in RateDirection:
                for vol in VolatilityState:
                    macro = MacroState(
                        regime=regime,
                        volatility_state=vol,
                        rate_direction=rate_dir,
                        week=1,
                    )
                    rng = random.Random(42)
                    result = self.agent.generate(macro, rng)
                    assert 0.0 <= result.confidence_level <= 1.0

    def test_crisis_lower_confidence(self) -> None:
        """Crisis vol should yield lower confidence than low vol on average."""
        low_confs = []
        crisis_confs = []
        for seed in range(100):
            for regime in [Regime.BULL, Regime.BEAR]:
                macro_low = MacroState(
                    regime=regime,
                    volatility_state=VolatilityState.LOW,
                    rate_direction=RateDirection.STABLE,
                    week=1,
                )
                macro_crisis = MacroState(
                    regime=regime,
                    volatility_state=VolatilityState.CRISIS,
                    rate_direction=RateDirection.STABLE,
                    week=1,
                )
                low_confs.append(self.agent.generate(macro_low, random.Random(seed)).confidence_level)
                crisis_confs.append(self.agent.generate(macro_crisis, random.Random(seed)).confidence_level)

        assert sum(low_confs) / len(low_confs) > sum(crisis_confs) / len(crisis_confs)

    def test_reproducible(self, sample_macro_bull: MacroState) -> None:
        """Same seed produces same statement."""
        r1 = self.agent.generate(sample_macro_bull, random.Random(99))
        r2 = self.agent.generate(sample_macro_bull, random.Random(99))
        assert r1.statement == r2.statement
        assert r1.confidence_level == r2.confidence_level

    def test_all_regime_rate_combos_work(self) -> None:
        """Every regime + rate direction combo produces a statement."""
        rng = random.Random(42)
        for regime in Regime:
            for rate_dir in RateDirection:
                macro = MacroState(
                    regime=regime,
                    volatility_state=VolatilityState.NORMAL,
                    rate_direction=rate_dir,
                    week=1,
                )
                result = self.agent.generate(macro, rng)
                assert isinstance(result, FedStatement)
