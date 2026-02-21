"""Career progression data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CareerTitle(str, Enum):
    """Player career titles, earned through sustained performance."""

    RETAIL_SPECULATOR = "Retail Speculator"
    JUNIOR_PM = "Junior PM"
    MACRO_OPERATOR = "Macro Operator"
    INSTITUTIONAL_STRATEGIST = "Institutional Strategist"
    LEGENDARY_ALLOCATOR = "Legendary Allocator"


class CareerProfile(BaseModel):
    """Long-term player career stats persisted across seasons."""

    player_name: str
    title: CareerTitle = CareerTitle.RETAIL_SPECULATOR
    seasons_played: int = 0
    lifetime_cagr: float = 0.0
    best_sharpe: float = 0.0
    worst_drawdown: float = 0.0
    total_pnl: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.now)
