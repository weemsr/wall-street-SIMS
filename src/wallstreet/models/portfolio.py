"""Portfolio and allocation data models."""

from pydantic import BaseModel, Field, model_validator

from wallstreet.models.enums import Sector


class Allocation(BaseModel):
    """Player's chosen allocation across sectors. Percentages must sum to 100."""

    weights: dict[Sector, float]

    @model_validator(mode="after")
    def validate_weights(self) -> "Allocation":
        total = sum(self.weights.values())
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Allocation must sum to 100%, got {total:.2f}%")
        for sector, weight in self.weights.items():
            if weight < 0:
                raise ValueError(f"Negative weight for {sector.value}: {weight}")
        if set(self.weights.keys()) != set(Sector):
            raise ValueError("Allocation must include all 5 sectors")
        return self

    @property
    def as_fractions(self) -> dict[Sector, float]:
        """Return weights as decimal fractions (0.0 to 1.0)."""
        return {s: w / 100.0 for s, w in self.weights.items()}


class Holdings(BaseModel):
    """Dollar-denominated holdings per sector."""

    positions: dict[Sector, float]


class PortfolioState(BaseModel):
    """Full snapshot of portfolio at a point in time."""

    cash: float = Field(ge=0)
    holdings: Holdings
    total_value: float
    week: int = Field(ge=0, le=26)
