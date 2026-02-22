"""Tests for risk committee agent."""

import pytest

from wallstreet.agents.risk_committee import RulesBasedRiskCommittee
from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.game import GameConfig, GameState
from wallstreet.models.market import MacroState
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState


def _make_game_state(
    macro: MacroState,
    portfolio: PortfolioState,
    weekly_values: list[float] | None = None,
) -> GameState:
    return GameState(
        config=GameConfig(seed=42, starting_cash=1_000_000.0, total_weeks=26),
        macro_state=macro,
        portfolio=portfolio,
        weekly_values=weekly_values or [1_000_000.0],
    )


class TestRulesBasedRiskCommittee:
    def setup_method(self) -> None:
        self.agent = RulesBasedRiskCommittee()

    def test_balanced_low_risk(
        self,
        sample_macro_bull: MacroState,
        sample_portfolio: PortfolioState,
    ) -> None:
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        game = _make_game_state(sample_macro_bull, sample_portfolio)
        risk = self.agent.evaluate(alloc, sample_macro_bull, sample_portfolio, game)
        assert 1 <= risk.risk_score <= 3

    def test_concentrated_high_risk(
        self,
        sample_macro_bull: MacroState,
        sample_portfolio: PortfolioState,
    ) -> None:
        alloc = Allocation(weights={
            Sector.TECH: 70.0, Sector.ENERGY: 10.0,
            Sector.FINANCIALS: 10.0, Sector.CONSUMER: 5.0,
            Sector.INDUSTRIALS: 5.0,
        })
        game = _make_game_state(sample_macro_bull, sample_portfolio)
        risk = self.agent.evaluate(alloc, sample_macro_bull, sample_portfolio, game)
        assert risk.risk_score >= 4

    def test_recession_cyclical_warning(self) -> None:
        macro = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.FALLING,
            week=5,
        )
        portfolio = PortfolioState(
            cash=0.0,
            holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=5,
        )
        # 70% in cyclicals (Tech + Industrials + Energy)
        alloc = Allocation(weights={
            Sector.TECH: 30.0, Sector.ENERGY: 25.0,
            Sector.FINANCIALS: 5.0, Sector.CONSUMER: 10.0,
            Sector.INDUSTRIALS: 30.0,
        })
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("cyclical" in w.lower() for w in risk.warnings)

    def test_rising_rates_tech_warning(self) -> None:
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.RISING,
            week=3,
        )
        portfolio = PortfolioState(
            cash=0.0,
            holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=3,
        )
        alloc = Allocation(weights={
            Sector.TECH: 50.0, Sector.ENERGY: 10.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 10.0,
            Sector.INDUSTRIALS: 10.0,
        })
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("tech" in w.lower() and "rising" in w.lower() for w in risk.warnings)

    def test_leverage_risk_warning(self) -> None:
        """High gross exposure triggers leverage warning."""
        macro = MacroState(
            regime=Regime.RECOVERY,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        portfolio = PortfolioState(
            cash=0.0,
            holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=3,
        )
        # gross = 80+30+20+20+50 = 200% -> extreme leverage
        alloc = Allocation(weights={
            Sector.TECH: 80.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 20.0,
            Sector.INDUSTRIALS: -50.0,
        })
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("gross exposure" in w.lower() or "leverage" in w.lower() for w in risk.warnings)

    def test_short_squeeze_warning_high_vol(self) -> None:
        """Short positions during high volatility trigger squeeze warning."""
        macro = MacroState(
            regime=Regime.RECOVERY,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        portfolio = PortfolioState(
            cash=0.0,
            holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=3,
        )
        alloc = Allocation(weights={
            Sector.TECH: 40.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 30.0,
            Sector.INDUSTRIALS: -20.0,
        })
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("squeeze" in w.lower() for w in risk.warnings)

    def test_counter_trend_short_warning_bull(self) -> None:
        """Shorting in bull market triggers counter-trend warning."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        portfolio = PortfolioState(
            cash=0.0,
            holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=3,
        )
        alloc = Allocation(weights={
            Sector.TECH: 40.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 30.0,
            Sector.INDUSTRIALS: -20.0,
        })
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("counter-trend" in w.lower() or "bull market" in w.lower() for w in risk.warnings)

    def test_high_cash_warning(self) -> None:
        """More than 50% cash triggers a warning."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        portfolio = PortfolioState(
            cash=500_000.0,
            holdings=Holdings(positions={s: 100_000.0 for s in Sector}),
            total_value=1_000_000.0,
            week=3,
        )
        # 8% per sector = 40% invested, 60% cash
        alloc = Allocation(weights={s: 8.0 for s in Sector})
        game = _make_game_state(macro, portfolio)
        risk = self.agent.evaluate(alloc, macro, portfolio, game)
        assert any("cash" in w.lower() for w in risk.warnings)

    def test_risk_score_bounds(
        self,
        sample_macro_bull: MacroState,
        sample_portfolio: PortfolioState,
    ) -> None:
        """Score always between 1 and 10."""
        for tech_pct in range(0, 101, 10):
            remaining = 100 - tech_pct
            per_other = remaining / 4
            alloc = Allocation(weights={
                Sector.TECH: float(tech_pct),
                Sector.ENERGY: per_other,
                Sector.FINANCIALS: per_other,
                Sector.CONSUMER: per_other,
                Sector.INDUSTRIALS: per_other,
            })
            game = _make_game_state(sample_macro_bull, sample_portfolio)
            risk = self.agent.evaluate(
                alloc, sample_macro_bull, sample_portfolio, game
            )
            assert 1 <= risk.risk_score <= 10
