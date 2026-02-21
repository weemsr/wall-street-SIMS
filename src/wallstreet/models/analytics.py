"""Expanded analytics data models."""

from pydantic import BaseModel, Field


class ExpandedMetrics(BaseModel):
    """Rolling and expanded performance metrics."""

    rolling_volatility: list[float] = Field(default_factory=list)
    rolling_sharpe: list[float] = Field(default_factory=list)
    drawdown_series: list[float] = Field(default_factory=list)
    concentration_scores: list[float] = Field(default_factory=list)

    current_rolling_vol: float = 0.0
    current_rolling_sharpe: float = 0.0
    current_drawdown: float = 0.0
    current_concentration: float = 0.0
