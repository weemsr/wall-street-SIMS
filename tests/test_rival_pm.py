"""Tests for Rival PM agent — 4 strategy types."""

import random

import pytest

from wallstreet.agents.rival_pm import (
    ALL_STRATEGIES,
    DEFENSIVE,
    MACRO_TIMER,
    MOMENTUM,
    RIVAL_NAMES,
    VALUE,
    RivalPM,
)
from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.game import GameConfig, GameState, WeekResult
from wallstreet.models.market import MacroState, SectorReturns
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


def _make_week_result(week: int, returns: dict[Sector, float]) -> WeekResult:
    macro = MacroState(
        regime=Regime.BULL,
        volatility_state=VolatilityState.NORMAL,
        rate_direction=RateDirection.STABLE,
        week=week,
    )
    alloc = Allocation(weights={s: 20.0 for s in Sector})
    return WeekResult(
        week=week,
        macro_state=macro,
        allocation=alloc,
        sector_returns=SectorReturns(returns=returns),
        events=[],
        adjusted_returns=SectorReturns(returns=returns),
        portfolio_return=sum(returns.values()) / len(returns),
        portfolio_value_before=1_000_000.0,
        portfolio_value_after=1_000_000.0,
    )


class TestRivalPMAllStrategies:
    def test_all_strategies_exist(self) -> None:
        """All 4 strategy types are available."""
        assert len(ALL_STRATEGIES) == 4
        for s in [MOMENTUM, DEFENSIVE, MACRO_TIMER, VALUE]:
            assert s in ALL_STRATEGIES

    def test_invalid_strategy_raises(self) -> None:
        """Unknown strategy type raises ValueError."""
        with pytest.raises(ValueError):
            RivalPM("unknown_strategy")

    def test_each_strategy_produces_allocation(self) -> None:
        """Every strategy returns a valid Allocation."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        game = _make_game_state(macro)
        for strategy in ALL_STRATEGIES:
            rival = RivalPM(strategy)
            alloc = rival.decide(macro, game, random.Random(42))
            assert isinstance(alloc, Allocation)
            # Sum to 100
            total = sum(alloc.weights.values())
            assert abs(total - 100.0) < 0.1
            # All sectors present
            assert set(alloc.weights.keys()) == set(Sector)

    def test_all_sectors_covered(self) -> None:
        """Each strategy allocates to all 5 sectors."""
        macro = MacroState(
            regime=Regime.BEAR,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.FALLING,
            week=5,
        )
        game = _make_game_state(macro)
        for strategy in ALL_STRATEGIES:
            rival = RivalPM(strategy)
            alloc = rival.decide(macro, game, random.Random(42))
            for sector in Sector:
                assert alloc.weights[sector] > 0

    def test_names_assigned(self) -> None:
        """Each strategy has a unique rival name."""
        for strategy in ALL_STRATEGIES:
            rival = RivalPM(strategy)
            assert rival.name == RIVAL_NAMES[strategy]
            assert len(rival.name) > 0

    def test_reproducible(self) -> None:
        """Same seed produces same allocation."""
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        game = _make_game_state(macro)
        for strategy in ALL_STRATEGIES:
            rival = RivalPM(strategy)
            a1 = rival.decide(macro, game, random.Random(42))
            a2 = rival.decide(macro, game, random.Random(42))
            for sector in Sector:
                assert abs(a1.weights[sector] - a2.weights[sector]) < 0.01


class TestMomentumStrategy:
    def test_overweights_winners(self) -> None:
        """Momentum strategy should overweight sectors with positive trailing returns."""
        # Create history where Tech outperformed
        returns_week1 = {s: 0.01 for s in Sector}
        returns_week1[Sector.TECH] = 0.05
        returns_week2 = dict(returns_week1)

        history = [
            _make_week_result(1, returns_week1),
            _make_week_result(2, returns_week2),
        ]
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        game = _make_game_state(macro, history)
        rival = RivalPM(MOMENTUM)
        alloc = rival.decide(macro, game, random.Random(42))
        # Tech should have the highest weight
        assert alloc.weights[Sector.TECH] == max(alloc.weights.values())


class TestValueStrategy:
    def test_overweights_losers(self) -> None:
        """Value strategy should overweight sectors with negative trailing returns."""
        returns_week1 = {s: 0.01 for s in Sector}
        returns_week1[Sector.ENERGY] = -0.05

        history = [
            _make_week_result(1, returns_week1),
            _make_week_result(2, returns_week1),
        ]
        macro = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.NORMAL,
            rate_direction=RateDirection.STABLE,
            week=3,
        )
        game = _make_game_state(macro, history)
        rival = RivalPM(VALUE)
        alloc = rival.decide(macro, game, random.Random(42))
        # Energy (worst performer) should have the highest weight
        assert alloc.weights[Sector.ENERGY] == max(alloc.weights.values())


class TestMacroTimerStrategy:
    def test_recession_overweights_consumer(self) -> None:
        """Macro timer in recession should overweight Consumer."""
        macro = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.HIGH,
            rate_direction=RateDirection.FALLING,
            week=5,
        )
        game = _make_game_state(macro)
        rival = RivalPM(MACRO_TIMER)
        alloc = rival.decide(macro, game, random.Random(42))
        # Consumer should be the largest allocation in recession
        assert alloc.weights[Sector.CONSUMER] == max(alloc.weights.values())
