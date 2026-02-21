"""Output models for narrative agents (Fed, Short Seller, Headlines, Rival)."""

from pydantic import BaseModel, Field

from wallstreet.models.enums import Sector
from wallstreet.models.portfolio import Allocation


class FedStatement(BaseModel):
    """Weekly Federal Reserve policy statement."""

    statement: str
    policy_bias: str  # "tightening", "easing", "neutral"
    confidence_level: float = Field(ge=0.0, le=1.0)


class ShortThesis(BaseModel):
    """Short seller attack on a player's vulnerable position."""

    target_sector: Sector
    critique: str
    conviction: float = Field(ge=0.0, le=1.0)


class Headline(BaseModel):
    """A single market headline."""

    text: str
    sentiment: str  # "bullish", "bearish", "mixed"
    impact_summary: dict[str, str] = Field(default_factory=dict)


class RivalWeekResult(BaseModel):
    """Result of the rival PM's weekly performance."""

    rival_name: str
    strategy_type: str
    allocation: Allocation
    portfolio_return: float
    portfolio_value: float
    portfolio_value_before: float


class WeeklyNarrative(BaseModel):
    """Combined narrative output for a single week."""

    fed_statement: FedStatement
    headlines: list[Headline]
    short_thesis: ShortThesis | None = None
