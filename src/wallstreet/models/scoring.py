"""Scorecard data model for final game results."""

from pydantic import BaseModel


class ScoreCard(BaseModel):
    """Final performance metrics for a completed game."""

    initial_value: float
    final_value: float
    total_return_pct: float
    cagr: float
    max_drawdown: float
    annualized_volatility: float
    sharpe_ratio: float
    total_weeks: int

    @property
    def letter_grade(self) -> str:
        """A-F grade based on Sharpe ratio (annualized from monthly data)."""
        if self.sharpe_ratio >= 3.0:
            return "A+"
        elif self.sharpe_ratio >= 2.0:
            return "A"
        elif self.sharpe_ratio >= 1.5:
            return "B"
        elif self.sharpe_ratio >= 0.8:
            return "C"
        elif self.sharpe_ratio >= 0.0:
            return "D"
        else:
            return "F"
