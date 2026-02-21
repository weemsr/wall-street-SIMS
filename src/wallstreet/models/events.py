"""Shock event data models."""

from pydantic import BaseModel, Field

from wallstreet.models.enums import Regime, Sector


class ShockEventTemplate(BaseModel):
    """Definition of a possible shock event in the catalog."""

    name: str
    description: str
    sector_effects: dict[Sector, float]
    vol_impact: float = Field(default=0.0)
    regime_weights: dict[Regime, float]


class ShockEvent(BaseModel):
    """An instantiated shock event that occurred in a specific week."""

    template_name: str
    description: str
    sector_effects: dict[Sector, float]
    vol_impact: float
    week: int
