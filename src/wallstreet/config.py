"""Central constants and default parameters."""

import os

from wallstreet.models.enums import RateDirection, Regime, VolatilityState

# Game defaults
DEFAULT_STARTING_CASH: float = 1_000_000.0
DEFAULT_TOTAL_WEEKS: int = 26
QUICK_PLAY_WEEKS: int = 3

# Return clamping bounds
MIN_WEEKLY_RETURN: float = -0.30
MAX_WEEKLY_RETURN: float = 0.30

# Starting macro state
INITIAL_REGIME: Regime = Regime.BULL
INITIAL_VOL_STATE: VolatilityState = VolatilityState.NORMAL
INITIAL_RATE_DIR: RateDirection = RateDirection.STABLE

# Persistence
DEFAULT_DB_PATH: str = os.environ.get("DATABASE_PATH", "wallstreet.db")
