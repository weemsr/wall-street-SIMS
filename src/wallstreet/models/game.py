"""Game state and configuration models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from wallstreet.models.enums import Sector
from wallstreet.models.events import ShockEvent
from wallstreet.models.market import MacroState, SectorReturns
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState


class GameConfig(BaseModel):
    """Configuration for a game session."""

    seed: int
    starting_cash: float = 1_000_000.0
    total_weeks: int = 26
    player_name: str = "Player"


class WeekResult(BaseModel):
    """Complete result of one week of play."""

    week: int
    macro_state: MacroState
    allocation: Allocation
    sector_returns: SectorReturns
    events: list[ShockEvent]
    adjusted_returns: SectorReturns
    portfolio_return: float
    portfolio_value_before: float
    portfolio_value_after: float


class GameState(BaseModel):
    """Full cumulative game state."""

    game_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    config: GameConfig
    current_week: int = 0
    macro_state: MacroState
    portfolio: PortfolioState
    history: list[WeekResult] = Field(default_factory=list)
    weekly_values: list[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    is_complete: bool = False
