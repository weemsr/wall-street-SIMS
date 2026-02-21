"""Abstract base class for risk assessment agents."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.portfolio import Allocation, PortfolioState


class RiskAssessment(BaseModel):
    """Output of a risk committee evaluation."""

    risk_score: int = Field(ge=1, le=10)
    critique: str
    warnings: list[str] = Field(default_factory=list)


class RiskAgent(ABC):
    """Abstract base class for risk assessment agents.

    Subclass this to create different risk evaluation strategies
    (rules-based, LLM-based, etc.).
    """

    @abstractmethod
    def evaluate(
        self,
        allocation: Allocation,
        macro_state: MacroState,
        portfolio: PortfolioState,
        game_state: GameState,
    ) -> RiskAssessment:
        """Evaluate a proposed allocation and return risk assessment."""
        ...
