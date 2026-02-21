"""Sector return generation with regime/rate/vol modifiers."""

import random

from wallstreet.config import MAX_WEEKLY_RETURN, MIN_WEEKLY_RETURN
from wallstreet.market_engine.correlation import sample_correlated_normals
from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.events import ShockEvent
from wallstreet.models.market import MacroState

# SECTOR_PARAMS[regime][sector] = (weekly_mean, weekly_std)
SECTOR_PARAMS: dict[Regime, dict[Sector, tuple[float, float]]] = {
    Regime.BULL: {
        Sector.TECH:        (0.020, 0.035),
        Sector.ENERGY:      (0.012, 0.040),
        Sector.FINANCIALS:  (0.015, 0.030),
        Sector.CONSUMER:    (0.010, 0.020),
        Sector.INDUSTRIALS: (0.013, 0.025),
    },
    Regime.BEAR: {
        Sector.TECH:        (-0.015, 0.045),
        Sector.ENERGY:      (-0.010, 0.050),
        Sector.FINANCIALS:  (-0.020, 0.040),
        Sector.CONSUMER:    (-0.005, 0.025),
        Sector.INDUSTRIALS: (-0.012, 0.035),
    },
    Regime.RECESSION: {
        Sector.TECH:        (-0.025, 0.055),
        Sector.ENERGY:      (-0.020, 0.060),
        Sector.FINANCIALS:  (-0.030, 0.050),
        Sector.CONSUMER:    (-0.008, 0.030),
        Sector.INDUSTRIALS: (-0.022, 0.045),
    },
    Regime.RECOVERY: {
        Sector.TECH:        (0.015, 0.040),
        Sector.ENERGY:      (0.018, 0.045),
        Sector.FINANCIALS:  (0.020, 0.035),
        Sector.CONSUMER:    (0.008, 0.022),
        Sector.INDUSTRIALS: (0.016, 0.030),
    },
}

# RATE_MODIFIERS[rate_direction][sector] = (mean_additive, std_multiplier)
RATE_MODIFIERS: dict[RateDirection, dict[Sector, tuple[float, float]]] = {
    RateDirection.RISING: {
        Sector.TECH:        (-0.003, 1.10),
        Sector.ENERGY:      (0.002, 1.00),
        Sector.FINANCIALS:  (0.005, 0.90),
        Sector.CONSUMER:    (-0.002, 1.05),
        Sector.INDUSTRIALS: (-0.001, 1.05),
    },
    RateDirection.STABLE: {
        Sector.TECH:        (0.000, 1.00),
        Sector.ENERGY:      (0.000, 1.00),
        Sector.FINANCIALS:  (0.000, 1.00),
        Sector.CONSUMER:    (0.000, 1.00),
        Sector.INDUSTRIALS: (0.000, 1.00),
    },
    RateDirection.FALLING: {
        Sector.TECH:        (0.004, 0.95),
        Sector.ENERGY:      (-0.001, 1.05),
        Sector.FINANCIALS:  (-0.004, 1.10),
        Sector.CONSUMER:    (0.002, 0.95),
        Sector.INDUSTRIALS: (0.001, 0.98),
    },
}

# Volatility state scaling factors applied to standard deviation
VOL_SCALING: dict[VolatilityState, float] = {
    VolatilityState.LOW:    0.60,
    VolatilityState.NORMAL: 1.00,
    VolatilityState.HIGH:   1.50,
    VolatilityState.CRISIS: 2.20,
}


def generate_sector_returns(
    macro: MacroState, rng: random.Random
) -> dict[Sector, float]:
    """Generate one week of sector returns based on macro state.

    1. Look up base (mean, std) for regime + sector
    2. Apply rate direction modifiers
    3. Scale std by volatility state
    4. Sample correlated normals
    5. Compute: return = effective_mean + effective_std * z
    6. Clamp to [-30%, +30%]
    """
    z_values = sample_correlated_normals(macro.regime, rng)
    vol_scale = VOL_SCALING[macro.volatility_state]
    returns: dict[Sector, float] = {}

    for sector in Sector:
        mean_base, std_base = SECTOR_PARAMS[macro.regime][sector]
        mean_add, std_mult = RATE_MODIFIERS[macro.rate_direction][sector]

        effective_mean = mean_base + mean_add
        effective_std = std_base * std_mult * vol_scale

        raw_return = effective_mean + effective_std * z_values[sector]
        returns[sector] = max(MIN_WEEKLY_RETURN, min(MAX_WEEKLY_RETURN, raw_return))

    return returns


def apply_events(
    base_returns: dict[Sector, float],
    events: list[ShockEvent],
) -> dict[Sector, float]:
    """Additively apply shock event effects to base sector returns.

    Clamps final returns to [-30%, +30%].
    """
    adjusted = dict(base_returns)
    for event in events:
        for sector, effect in event.sector_effects.items():
            adjusted[sector] = adjusted.get(sector, 0.0) + effect
    return {
        s: max(MIN_WEEKLY_RETURN, min(MAX_WEEKLY_RETURN, r))
        for s, r in adjusted.items()
    }
