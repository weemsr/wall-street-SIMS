"""GameNarrativeLayer — orchestrates Fed, Headlines, and Short Seller per week."""

import random

from wallstreet.agents.fed_agent import FedChairAgent
from wallstreet.agents.headline_engine import generate_headlines
from wallstreet.agents.short_seller import ShortSellerAgent
from wallstreet.models.events import ShockEvent
from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import FedStatement, Headline, ShortThesis, WeeklyNarrative
from wallstreet.models.portfolio import Allocation


class GameNarrativeLayer:
    """Orchestrates all narrative agents for a game session."""

    def __init__(self) -> None:
        self.fed = FedChairAgent()
        self.short_seller = ShortSellerAgent()

    def generate_weekly_narrative(
        self,
        macro: MacroState,
        events: list[ShockEvent],
        allocation: Allocation,
        game_state: GameState,
        rng: random.Random,
    ) -> WeeklyNarrative:
        """Generate all narrative elements for one week.

        Called after player has submitted allocation but before returns are calculated.
        """
        fed_statement = self.fed.generate(macro, rng)
        headlines = generate_headlines(macro, events, rng)
        short_thesis = self.short_seller.analyze(allocation, macro, game_state, rng)

        return WeeklyNarrative(
            fed_statement=fed_statement,
            headlines=headlines,
            short_thesis=short_thesis,
        )
