"""Core enumerations for game state."""

from enum import Enum


class Sector(str, Enum):
    """Investable market sectors."""
    TECH = "Tech"
    ENERGY = "Energy"
    FINANCIALS = "Financials"
    CONSUMER = "Consumer Staples"
    CONSUMER_DISC = "Consumer Discretionary"
    INDUSTRIALS = "Industrials"
    HEALTHCARE = "Healthcare"


class Regime(str, Enum):
    """Macroeconomic regime states."""
    BULL = "bull"
    BEAR = "bear"
    RECESSION = "recession"
    RECOVERY = "recovery"


class VolatilityState(str, Enum):
    """Market volatility levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRISIS = "crisis"


class RateDirection(str, Enum):
    """Interest rate trajectory."""
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"
