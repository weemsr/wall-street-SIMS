"""Portfolio and allocation data models."""

from pydantic import BaseModel, Field, model_validator

from wallstreet.config import MAX_GROSS_EXPOSURE, MAX_SHORT_PER_SECTOR
from wallstreet.models.enums import Sector


class Allocation(BaseModel):
    """Player's chosen allocation across sectors.

    Percentages must sum to 0-100% (net exposure). The remainder is
    held as cash earning 0%. Negative weights represent short positions.
    Gross exposure (sum of absolute weights) is capped at
    MAX_GROSS_EXPOSURE (200%). Individual shorts are capped at
    MAX_SHORT_PER_SECTOR (-50%).
    """

    weights: dict[Sector, float]

    @model_validator(mode="after")
    def validate_weights(self) -> "Allocation":
        total = sum(self.weights.values())
        if total < -0.01 or total > 100.01:
            raise ValueError(
                f"Allocation must sum to 0-100%, got {total:.2f}%"
            )
        for sector, weight in self.weights.items():
            if weight < MAX_SHORT_PER_SECTOR:
                raise ValueError(
                    f"Short position too large for {sector.value}: {weight}% "
                    f"(max short is {MAX_SHORT_PER_SECTOR}%)"
                )
        gross = sum(abs(w) for w in self.weights.values())
        if gross > MAX_GROSS_EXPOSURE + 0.01:
            raise ValueError(
                f"Gross exposure {gross:.1f}% exceeds {MAX_GROSS_EXPOSURE:.0f}% limit"
            )
        if set(self.weights.keys()) != set(Sector):
            raise ValueError("Allocation must include all 5 sectors")
        return self

    @property
    def as_fractions(self) -> dict[Sector, float]:
        """Return weights as decimal fractions (can be negative for shorts)."""
        return {s: w / 100.0 for s, w in self.weights.items()}

    @property
    def gross_exposure(self) -> float:
        """Gross exposure as a fraction (1.0 = long-only, 2.0 = max leverage)."""
        return sum(abs(w) for w in self.weights.values()) / 100.0

    @property
    def cash_weight(self) -> float:
        """Fraction of portfolio held as cash (0.0 = fully invested)."""
        return (100.0 - sum(self.weights.values())) / 100.0

    @property
    def has_shorts(self) -> bool:
        """Whether the allocation contains any short positions."""
        return any(w < 0 for w in self.weights.values())


class Holdings(BaseModel):
    """Dollar-denominated holdings per sector."""

    positions: dict[Sector, float]


class PortfolioState(BaseModel):
    """Full snapshot of portfolio at a point in time."""

    cash: float = Field(ge=0)
    holdings: Holdings
    total_value: float
    week: int = Field(ge=0, le=26)
