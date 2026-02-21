"""Markov chain regime transitions for macro state."""

import random

from wallstreet.models.enums import RateDirection, Regime, VolatilityState
from wallstreet.models.market import MacroState

# Regime transition matrix: probability of moving FROM row TO column
REGIME_TRANSITION: dict[Regime, dict[Regime, float]] = {
    Regime.BULL: {
        Regime.BULL: 0.60, Regime.BEAR: 0.20,
        Regime.RECESSION: 0.05, Regime.RECOVERY: 0.15,
    },
    Regime.BEAR: {
        Regime.BULL: 0.10, Regime.BEAR: 0.50,
        Regime.RECESSION: 0.30, Regime.RECOVERY: 0.10,
    },
    Regime.RECESSION: {
        Regime.BULL: 0.05, Regime.BEAR: 0.15,
        Regime.RECESSION: 0.50, Regime.RECOVERY: 0.30,
    },
    Regime.RECOVERY: {
        Regime.BULL: 0.35, Regime.BEAR: 0.10,
        Regime.RECESSION: 0.05, Regime.RECOVERY: 0.50,
    },
}

# Rate direction distribution conditioned on regime
RATE_DIRECTION_BY_REGIME: dict[Regime, dict[RateDirection, float]] = {
    Regime.BULL: {
        RateDirection.RISING: 0.50, RateDirection.STABLE: 0.35,
        RateDirection.FALLING: 0.15,
    },
    Regime.BEAR: {
        RateDirection.RISING: 0.20, RateDirection.STABLE: 0.30,
        RateDirection.FALLING: 0.50,
    },
    Regime.RECESSION: {
        RateDirection.RISING: 0.05, RateDirection.STABLE: 0.25,
        RateDirection.FALLING: 0.70,
    },
    Regime.RECOVERY: {
        RateDirection.RISING: 0.35, RateDirection.STABLE: 0.45,
        RateDirection.FALLING: 0.20,
    },
}

# Volatility state distribution conditioned on regime
VOL_STATE_BY_REGIME: dict[Regime, dict[VolatilityState, float]] = {
    Regime.BULL: {
        VolatilityState.LOW: 0.40, VolatilityState.NORMAL: 0.45,
        VolatilityState.HIGH: 0.12, VolatilityState.CRISIS: 0.03,
    },
    Regime.BEAR: {
        VolatilityState.LOW: 0.05, VolatilityState.NORMAL: 0.30,
        VolatilityState.HIGH: 0.45, VolatilityState.CRISIS: 0.20,
    },
    Regime.RECESSION: {
        VolatilityState.LOW: 0.02, VolatilityState.NORMAL: 0.18,
        VolatilityState.HIGH: 0.40, VolatilityState.CRISIS: 0.40,
    },
    Regime.RECOVERY: {
        VolatilityState.LOW: 0.25, VolatilityState.NORMAL: 0.50,
        VolatilityState.HIGH: 0.20, VolatilityState.CRISIS: 0.05,
    },
}


def _weighted_choice(
    options: dict[str, float], rng: random.Random
) -> str:
    """Pick from a dict of {value: probability} using the seeded RNG."""
    keys = list(options.keys())
    weights = [options[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def advance_macro_state(
    current: MacroState, rng: random.Random
) -> MacroState:
    """Transition to the next week's macro state via Markov chain.

    Returns a new MacroState with updated regime, rate direction,
    and volatility state. The week field is NOT incremented here
    (caller is responsible for setting the week).
    """
    new_regime = Regime(_weighted_choice(REGIME_TRANSITION[current.regime], rng))
    new_rate = RateDirection(
        _weighted_choice(RATE_DIRECTION_BY_REGIME[new_regime], rng)
    )
    new_vol = VolatilityState(
        _weighted_choice(VOL_STATE_BY_REGIME[new_regime], rng)
    )
    return MacroState(
        regime=new_regime,
        volatility_state=new_vol,
        rate_direction=new_rate,
        week=current.week,
    )
