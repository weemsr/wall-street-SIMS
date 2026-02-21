"""GameCompetitionLayer — orchestrates rival PM tracking throughout the game."""

import random

from wallstreet.agents.rival_pm import RIVAL_NAMES, RivalPM
from wallstreet.models.enums import Sector
from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import RivalWeekResult


class GameCompetitionLayer:
    """Tracks a rival PM's performance over the course of a game."""

    def __init__(self, strategy_type: str) -> None:
        self.rival = RivalPM(strategy_type)
        self.rival_value: float = 1_000_000.0
        self.rival_values: list[float] = [1_000_000.0]

    @property
    def rival_name(self) -> str:
        return self.rival.name

    @property
    def strategy_type(self) -> str:
        return self.rival.strategy_type

    def process_week(
        self,
        macro: MacroState,
        adjusted_returns: dict[Sector, float],
        game_state: GameState,
        rng: random.Random,
    ) -> RivalWeekResult:
        """Process one week for the rival PM.

        Uses the same adjusted returns (base + events) that the player faces.
        """
        rival_alloc = self.rival.decide(macro, game_state, rng)

        # Compute rival's portfolio return
        portfolio_return = sum(
            rival_alloc.as_fractions[s] * adjusted_returns[s]
            for s in Sector
        )

        value_before = self.rival_value
        self.rival_value *= (1 + portfolio_return)
        self.rival_values.append(self.rival_value)

        return RivalWeekResult(
            rival_name=self.rival.name,
            strategy_type=self.rival.strategy_type,
            allocation=rival_alloc,
            portfolio_return=round(portfolio_return, 6),
            portfolio_value=round(self.rival_value, 2),
            portfolio_value_before=round(value_before, 2),
        )
