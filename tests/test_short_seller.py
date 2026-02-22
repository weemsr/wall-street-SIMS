"""Tests for Short Seller agent."""

import random

import pytest

from wallstreet.agents.short_seller import ShortSellerAgent
from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.game import GameConfig, GameState, WeekResult
from wallstreet.models.market import MacroState, SectorReturns
from wallstreet.models.narrative import ShortThesis
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState


def _make_game_state(
    macro: MacroState,
    history: list[WeekResult] | None = None,
) -> GameState:
    portfolio = PortfolioState(
        cash=0.0,
        holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
        total_value=1_000_000.0,
        week=macro.week,
    )
    return GameState(
        config=GameConfig(seed=42, starting_cash=1_000_000.0, total_weeks=26),
        macro_state=macro,
        portfolio=portfolio,
        weekly_values=[1_000_000.0],
        history=history or [],
    )


class TestShortSellerAgent:
    def setup_method(self) -> None:
        self.agent = ShortSellerAgent()
        self.bull_macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )

    def test_concentration_attack(self) -> None:
        """Sector > 40% triggers concentration attack."""
        alloc = Allocation(weights={
            Sector.TECH: 60.0, Sector.ENERGY: 8.0,
            Sector.FINANCIALS: 8.0, Sector.CONSUMER: 8.0,
            Sector.CONSUMER_DISC: 8.0, Sector.INDUSTRIALS: 4.0,
            Sector.HEALTHCARE: 4.0,
        })
        game = _make_game_state(self.bull_macro)
        result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
        assert result is not None
        assert result.target_sector == Sector.TECH
        assert result.conviction >= 0.60

    def test_no_attack_balanced(self) -> None:
        """Balanced allocation in bull market yields no attack."""
        alloc = Allocation(weights={s: 100.0 / len(Sector) for s in Sector})
        game = _make_game_state(self.bull_macro)
        result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
        assert result is None

    def test_regime_misalignment_attack(self) -> None:
        """Cyclicals overweight in recession triggers attack."""
        recession_macro = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.FALLING,
            week=5,
        )
        # Use weights below 40% to avoid concentration firing first,
        # but above 25% for at least one cyclical to trigger regime misalignment
        alloc = Allocation(weights={
            Sector.TECH: 28.0, Sector.ENERGY: 22.0,
            Sector.FINANCIALS: 8.0, Sector.CONSUMER: 8.0,
            Sector.CONSUMER_DISC: 14.0, Sector.INDUSTRIALS: 15.0,
            Sector.HEALTHCARE: 5.0,
        })
        game = _make_game_state(recession_macro)
        result = self.agent.analyze(alloc, recession_macro, game, random.Random(42))
        assert result is not None
        assert result.target_sector in {
            Sector.TECH, Sector.ENERGY, Sector.INDUSTRIALS, Sector.CONSUMER_DISC
        }

    def test_rate_sensitivity_attack(self) -> None:
        """Tech overweight with rising rates triggers attack."""
        rising_macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.RISING,
            week=3,
        )
        alloc = Allocation(weights={
            Sector.TECH: 35.0, Sector.ENERGY: 15.0,
            Sector.FINANCIALS: 10.0, Sector.CONSUMER: 10.0,
            Sector.CONSUMER_DISC: 10.0, Sector.INDUSTRIALS: 10.0,
            Sector.HEALTHCARE: 10.0,
        })
        game = _make_game_state(rising_macro)
        result = self.agent.analyze(alloc, rising_macro, game, random.Random(42))
        assert result is not None
        assert result.target_sector == Sector.TECH

    def test_conviction_bounds(self) -> None:
        """Conviction is always 0-1."""
        for tech_pct in [45, 60, 80, 100]:
            remaining = 100 - tech_pct
            per_other = remaining / 6
            alloc = Allocation(weights={
                Sector.TECH: float(tech_pct),
                Sector.ENERGY: per_other,
                Sector.FINANCIALS: per_other,
                Sector.CONSUMER: per_other,
                Sector.CONSUMER_DISC: per_other,
                Sector.INDUSTRIALS: per_other,
                Sector.HEALTHCARE: per_other,
            })
            game = _make_game_state(self.bull_macro)
            result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
            if result:
                assert 0.0 <= result.conviction <= 1.0

    def test_player_short_in_bull_attack(self) -> None:
        """Player shorting a sector in bull market triggers squeeze attack."""
        alloc = Allocation(weights={
            Sector.TECH: 30.0, Sector.ENERGY: 25.0,
            Sector.FINANCIALS: 15.0, Sector.CONSUMER: 25.0,
            Sector.CONSUMER_DISC: 5.0, Sector.INDUSTRIALS: -15.0,
            Sector.HEALTHCARE: 15.0,
        })
        game = _make_game_state(self.bull_macro)
        result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
        assert result is not None
        assert result.target_sector == Sector.INDUSTRIALS

    def test_no_squeeze_attack_in_recession(self) -> None:
        """Player shorts in recession should NOT trigger squeeze attack."""
        recession_macro = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.FALLING,
            week=5,
        )
        alloc = Allocation(weights={
            Sector.TECH: 20.0, Sector.ENERGY: 15.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 25.0,
            Sector.CONSUMER_DISC: 5.0, Sector.INDUSTRIALS: -10.0,
            Sector.HEALTHCARE: 25.0,
        })
        game = _make_game_state(recession_macro)
        result = self.agent.analyze(alloc, recession_macro, game, random.Random(42))
        # Should not be a squeeze attack (may be None or different attack type)
        if result is not None:
            assert "squeeze" not in result.critique.lower()

    def test_concentration_on_large_short(self) -> None:
        """A large short position (|weight| > 40%) triggers concentration attack."""
        alloc = Allocation(weights={
            Sector.TECH: 80.0, Sector.ENERGY: 15.0,
            Sector.FINANCIALS: 15.0, Sector.CONSUMER: 20.0,
            Sector.CONSUMER_DISC: 10.0, Sector.INDUSTRIALS: -50.0,
            Sector.HEALTHCARE: 10.0,
        })
        game = _make_game_state(self.bull_macro)
        result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
        assert result is not None
        # Should trigger concentration on either TECH (80%) or INDUSTRIALS (|-50|=50%)
        assert result.conviction >= 0.60

    def test_critique_not_empty(self) -> None:
        """Critique is non-empty when attack fires."""
        alloc = Allocation(weights={
            Sector.TECH: 50.0, Sector.ENERGY: 8.0,
            Sector.FINANCIALS: 8.0, Sector.CONSUMER: 10.0,
            Sector.CONSUMER_DISC: 8.0, Sector.INDUSTRIALS: 8.0,
            Sector.HEALTHCARE: 8.0,
        })
        game = _make_game_state(self.bull_macro)
        result = self.agent.analyze(alloc, self.bull_macro, game, random.Random(42))
        assert result is not None
        assert len(result.critique) > 0
