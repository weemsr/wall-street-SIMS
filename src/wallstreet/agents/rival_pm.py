"""Rival Portfolio Manager agent — 4 strategy types competing against the player."""

import random

from wallstreet.models.enums import Regime, Sector
from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.portfolio import Allocation

# Strategy type identifiers
MOMENTUM = "momentum"
DEFENSIVE = "defensive"
MACRO_TIMER = "macro_timer"
VALUE = "value"

ALL_STRATEGIES = [MOMENTUM, DEFENSIVE, MACRO_TIMER, VALUE]

# Rival names keyed by strategy type
RIVAL_NAMES: dict[str, str] = {
    MOMENTUM: "Velocity Capital",
    DEFENSIVE: "Fortress Fund",
    MACRO_TIMER: "Regime Alpha Partners",
    VALUE: "Contrarian Capital",
}

# ── Macro Timer target allocations by regime ───────────────────────────

_MACRO_TIMER_TARGETS: dict[Regime, dict[Sector, float]] = {
    Regime.BULL: {
        Sector.TECH: 25.0,
        Sector.ENERGY: 8.0,
        Sector.FINANCIALS: 12.0,
        Sector.CONSUMER: 8.0,
        Sector.CONSUMER_DISC: 18.0,
        Sector.INDUSTRIALS: 22.0,
        Sector.HEALTHCARE: 7.0,
    },
    Regime.BEAR: {
        Sector.TECH: 8.0,
        Sector.ENERGY: 8.0,
        Sector.FINANCIALS: 20.0,
        Sector.CONSUMER: 30.0,
        Sector.CONSUMER_DISC: 7.0,
        Sector.INDUSTRIALS: 10.0,
        Sector.HEALTHCARE: 17.0,
    },
    Regime.RECESSION: {
        Sector.TECH: 5.0,
        Sector.ENERGY: 5.0,
        Sector.FINANCIALS: 12.0,
        Sector.CONSUMER: 35.0,
        Sector.CONSUMER_DISC: 5.0,
        Sector.INDUSTRIALS: 13.0,
        Sector.HEALTHCARE: 25.0,
    },
    Regime.RECOVERY: {
        Sector.TECH: 12.0,
        Sector.ENERGY: 22.0,
        Sector.FINANCIALS: 20.0,
        Sector.CONSUMER: 8.0,
        Sector.CONSUMER_DISC: 12.0,
        Sector.INDUSTRIALS: 18.0,
        Sector.HEALTHCARE: 8.0,
    },
}

# ── Defensive base allocations by regime ───────────────────────────────

_DEFENSIVE_TARGETS: dict[Regime, dict[Sector, float]] = {
    Regime.BULL: {
        Sector.TECH: 8.0,
        Sector.ENERGY: 8.0,
        Sector.FINANCIALS: 15.0,
        Sector.CONSUMER: 28.0,
        Sector.CONSUMER_DISC: 8.0,
        Sector.INDUSTRIALS: 13.0,
        Sector.HEALTHCARE: 20.0,
    },
    Regime.BEAR: {
        Sector.TECH: 5.0,
        Sector.ENERGY: 5.0,
        Sector.FINANCIALS: 15.0,
        Sector.CONSUMER: 30.0,
        Sector.CONSUMER_DISC: 5.0,
        Sector.INDUSTRIALS: 13.0,
        Sector.HEALTHCARE: 27.0,
    },
    Regime.RECESSION: {
        Sector.TECH: 5.0,
        Sector.ENERGY: 5.0,
        Sector.FINANCIALS: 10.0,
        Sector.CONSUMER: 30.0,
        Sector.CONSUMER_DISC: 5.0,
        Sector.INDUSTRIALS: 13.0,
        Sector.HEALTHCARE: 32.0,
    },
    Regime.RECOVERY: {
        Sector.TECH: 10.0,
        Sector.ENERGY: 12.0,
        Sector.FINANCIALS: 15.0,
        Sector.CONSUMER: 22.0,
        Sector.CONSUMER_DISC: 10.0,
        Sector.INDUSTRIALS: 15.0,
        Sector.HEALTHCARE: 16.0,
    },
}


def _normalize_weights(raw: dict[Sector, float], min_pct: float = 5.0) -> dict[Sector, float]:
    """Normalize sector weights to sum to 100% with a per-sector minimum."""
    # Enforce minimum
    adjusted = {s: max(min_pct, w) for s, w in raw.items()}
    total = sum(adjusted.values())
    # Normalize to 100
    normalized = {s: round(w / total * 100.0, 2) for s, w in adjusted.items()}
    # Fix rounding residual
    residual = 100.0 - sum(normalized.values())
    if abs(residual) > 0.001:
        # Add residual to the largest sector
        largest = max(normalized, key=normalized.get)  # type: ignore[arg-type]
        normalized[largest] = round(normalized[largest] + residual, 2)
    return normalized


def _trailing_returns(game_state: GameState, window: int = 4) -> dict[Sector, float]:
    """Compute trailing cumulative return per sector over the last `window` weeks."""
    history = game_state.history[-window:] if game_state.history else []
    cumulative: dict[Sector, float] = {s: 0.0 for s in Sector}
    for week_result in history:
        for sector in Sector:
            cumulative[sector] += week_result.adjusted_returns.returns[sector]
    return cumulative


class RivalPM:
    """AI rival portfolio manager with a fixed strategy type.

    Deterministic allocation logic based on strategy rules + game state.
    """

    def __init__(self, strategy_type: str) -> None:
        if strategy_type not in ALL_STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy_type}. Must be one of {ALL_STRATEGIES}")
        self.strategy_type = strategy_type
        self.name = RIVAL_NAMES[strategy_type]

    def decide(
        self, macro: MacroState, game_state: GameState, rng: random.Random
    ) -> Allocation:
        """Decide sector allocation for this week based on strategy."""
        if self.strategy_type == MOMENTUM:
            weights = self._momentum_decide(game_state, rng)
        elif self.strategy_type == DEFENSIVE:
            weights = self._defensive_decide(macro, rng)
        elif self.strategy_type == MACRO_TIMER:
            weights = self._macro_timer_decide(macro, rng)
        elif self.strategy_type == VALUE:
            weights = self._value_decide(game_state, rng)
        else:
            weights = {s: 100.0 / len(Sector) for s in Sector}

        return Allocation(weights=weights)

    def _momentum_decide(
        self, game_state: GameState, rng: random.Random
    ) -> dict[Sector, float]:
        """Momentum: chase recent performance, overweight winners."""
        trailing = _trailing_returns(game_state, window=4)

        if not game_state.history or all(v == 0.0 for v in trailing.values()):
            # No history — equal weight with small noise
            return _normalize_weights(
                {s: 20.0 + rng.uniform(-2, 2) for s in Sector}, min_pct=5.0
            )

        # Shift returns so they're all positive for weighting
        min_ret = min(trailing.values())
        shifted = {s: trailing[s] - min_ret + 0.01 for s in Sector}
        total = sum(shifted.values())
        raw = {s: (shifted[s] / total) * 100.0 for s in Sector}
        return _normalize_weights(raw, min_pct=5.0)

    def _defensive_decide(
        self, macro: MacroState, rng: random.Random
    ) -> dict[Sector, float]:
        """Defensive: prioritize low-vol sectors, heavy Consumer."""
        base = dict(_DEFENSIVE_TARGETS[macro.regime])
        # Add slight randomness
        for s in Sector:
            base[s] += rng.uniform(-3, 3)
        return _normalize_weights(base, min_pct=5.0)

    def _macro_timer_decide(
        self, macro: MacroState, rng: random.Random
    ) -> dict[Sector, float]:
        """Macro Timer: read the regime and position accordingly."""
        base = dict(_MACRO_TIMER_TARGETS[macro.regime])
        # Add slight randomness
        for s in Sector:
            base[s] += rng.uniform(-3, 3)
        return _normalize_weights(base, min_pct=5.0)

    def _value_decide(
        self, game_state: GameState, rng: random.Random
    ) -> dict[Sector, float]:
        """Value: contrarian — buy beaten-down sectors, sell winners."""
        trailing = _trailing_returns(game_state, window=4)

        if not game_state.history or all(v == 0.0 for v in trailing.values()):
            # No history — equal weight with noise
            return _normalize_weights(
                {s: 20.0 + rng.uniform(-2, 2) for s in Sector}, min_pct=10.0
            )

        # Invert returns: worst performers get highest weight
        max_ret = max(trailing.values())
        inverted = {s: max_ret - trailing[s] + 0.01 for s in Sector}
        total = sum(inverted.values())
        raw = {s: (inverted[s] / total) * 100.0 for s in Sector}
        return _normalize_weights(raw, min_pct=10.0)
