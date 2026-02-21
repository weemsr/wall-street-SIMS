"""Correlation matrices and correlated normal sampling."""

import random

import numpy as np

from wallstreet.models.enums import Regime, Sector

# Sector ordering for correlation matrices
SECTOR_ORDER: list[Sector] = [
    Sector.TECH, Sector.ENERGY, Sector.FINANCIALS,
    Sector.CONSUMER, Sector.INDUSTRIALS,
]

# Per-regime correlation matrices (5x5, symmetric positive-definite)
# Order: Tech, Energy, Financials, Consumer, Industrials
CORRELATION_MATRICES: dict[Regime, list[list[float]]] = {
    Regime.BULL: [
        [1.00, 0.30, 0.40, 0.35, 0.45],
        [0.30, 1.00, 0.25, 0.20, 0.50],
        [0.40, 0.25, 1.00, 0.30, 0.35],
        [0.35, 0.20, 0.30, 1.00, 0.30],
        [0.45, 0.50, 0.35, 0.30, 1.00],
    ],
    Regime.BEAR: [
        [1.00, 0.50, 0.60, 0.55, 0.65],
        [0.50, 1.00, 0.45, 0.40, 0.60],
        [0.60, 0.45, 1.00, 0.50, 0.55],
        [0.55, 0.40, 0.50, 1.00, 0.50],
        [0.65, 0.60, 0.55, 0.50, 1.00],
    ],
    Regime.RECESSION: [
        [1.00, 0.65, 0.70, 0.60, 0.75],
        [0.65, 1.00, 0.60, 0.55, 0.70],
        [0.70, 0.60, 1.00, 0.65, 0.65],
        [0.60, 0.55, 0.65, 1.00, 0.60],
        [0.75, 0.70, 0.65, 0.60, 1.00],
    ],
    Regime.RECOVERY: [
        [1.00, 0.35, 0.45, 0.30, 0.40],
        [0.35, 1.00, 0.30, 0.25, 0.45],
        [0.45, 0.30, 1.00, 0.35, 0.40],
        [0.30, 0.25, 0.35, 1.00, 0.35],
        [0.40, 0.45, 0.40, 0.35, 1.00],
    ],
}

# Pre-compute Cholesky factors for each regime
_CHOLESKY_CACHE: dict[Regime, np.ndarray] = {}


def _get_cholesky(regime: Regime) -> np.ndarray:
    """Get (cached) Cholesky decomposition for a regime's correlation matrix."""
    if regime not in _CHOLESKY_CACHE:
        corr = np.array(CORRELATION_MATRICES[regime])
        _CHOLESKY_CACHE[regime] = np.linalg.cholesky(corr)
    return _CHOLESKY_CACHE[regime]


def sample_correlated_normals(
    regime: Regime, rng: random.Random
) -> dict[Sector, float]:
    """Generate 5 correlated standard normal samples using Cholesky decomposition.

    Uses the stdlib random.Random for reproducible seeding,
    then applies Cholesky factor for correlation structure.
    """
    L = _get_cholesky(regime)
    z_independent = np.array([rng.gauss(0, 1) for _ in range(5)])
    z_correlated = L @ z_independent
    return dict(zip(SECTOR_ORDER, z_correlated.tolist()))
