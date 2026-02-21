"""Market-related data models."""

from pydantic import BaseModel, Field

from wallstreet.models.enums import Regime, RateDirection, Sector, VolatilityState


class MacroState(BaseModel):
    """Current macroeconomic environment."""

    regime: Regime
    volatility_state: VolatilityState
    rate_direction: RateDirection
    week: int = Field(ge=0, le=26)

    @property
    def description(self) -> str:
        """Human-readable summary of macro conditions."""
        regime_desc = {
            Regime.BULL: "The economy is expanding. Risk appetite is strong.",
            Regime.BEAR: "Markets are declining. Caution is warranted.",
            Regime.RECESSION: "Economic contraction underway. Defensive positioning advised.",
            Regime.RECOVERY: "Signs of recovery emerging. Opportunities abound.",
        }
        return regime_desc[self.regime]


class SectorReturns(BaseModel):
    """Weekly returns for all sectors."""

    returns: dict[Sector, float]
