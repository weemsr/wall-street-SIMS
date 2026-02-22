"""Shared test fixtures."""

import random

import pytest

from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.game import GameConfig, GameState
from wallstreet.models.market import MacroState
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState


@pytest.fixture
def seeded_rng() -> random.Random:
    return random.Random(42)


@pytest.fixture
def sample_macro_bull() -> MacroState:
    return MacroState(
        regime=Regime.BULL,
        volatility_state=VolatilityState.NORMAL,
        rate_direction=RateDirection.STABLE,
        week=1,
    )


@pytest.fixture
def sample_macro_recession() -> MacroState:
    return MacroState(
        regime=Regime.RECESSION,
        volatility_state=VolatilityState.HIGH,
        rate_direction=RateDirection.FALLING,
        week=5,
    )


@pytest.fixture
def sample_allocation_balanced() -> Allocation:
    return Allocation(weights={s: 20.0 for s in Sector})


@pytest.fixture
def sample_allocation_concentrated() -> Allocation:
    return Allocation(
        weights={
            Sector.TECH: 70.0,
            Sector.ENERGY: 10.0,
            Sector.FINANCIALS: 10.0,
            Sector.CONSUMER: 5.0,
            Sector.CONSUMER_DISC: 0.0,
            Sector.INDUSTRIALS: 5.0,
            Sector.HEALTHCARE: 0.0,
        }
    )


@pytest.fixture
def sample_portfolio() -> PortfolioState:
    return PortfolioState(
        cash=0.0,
        holdings=Holdings(positions={s: 200_000.0 for s in Sector}),
        total_value=1_000_000.0,
        week=1,
    )


@pytest.fixture
def sample_game_config() -> GameConfig:
    return GameConfig(seed=42, starting_cash=1_000_000.0, total_weeks=26)


@pytest.fixture
def sample_game_state(
    sample_game_config: GameConfig,
    sample_macro_bull: MacroState,
    sample_portfolio: PortfolioState,
) -> GameState:
    return GameState(
        config=sample_game_config,
        macro_state=sample_macro_bull,
        portfolio=sample_portfolio,
        weekly_values=[1_000_000.0],
    )
