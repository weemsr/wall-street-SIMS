"""Correlation matrices and correlated normal sampling."""

import random

import numpy as np

from wallstreet.models.enums import Regime, Sector

# Sector ordering for correlation matrices
SECTOR_ORDER: list[Sector] = [
    Sector.TECH, Sector.ENERGY, Sector.FINANCIALS,
    Sector.CONSUMER, Sector.CONSUMER_DISC, Sector.INDUSTRIALS,
    Sector.HEALTHCARE,
]

# Per-regime correlation matrices (7x7, symmetric positive-definite)
# Order: Tech, Energy, Financials, Consumer Staples, Consumer Disc, Industrials, Healthcare
CORRELATION_MATRICES: dict[Regime, list[list[float]]] = {
    Regime.BULL: [
        #  Tech   Energy  Fin    ConSt  ConDis Indust Health
        [1.00,  0.30,  0.40,  0.35,  0.55,  0.45,  0.25],  # Tech
        [0.30,  1.00,  0.25,  0.20,  0.25,  0.50,  0.15],  # Energy
        [0.40,  0.25,  1.00,  0.30,  0.35,  0.35,  0.20],  # Financials
        [0.35,  0.20,  0.30,  1.00,  0.40,  0.30,  0.30],  # Consumer Staples
        [0.55,  0.25,  0.35,  0.40,  1.00,  0.45,  0.25],  # Consumer Disc
        [0.45,  0.50,  0.35,  0.30,  0.45,  1.00,  0.20],  # Industrials
        [0.25,  0.15,  0.20,  0.30,  0.25,  0.20,  1.00],  # Healthcare
    ],
    Regime.BEAR: [
        #  Tech   Energy  Fin    ConSt  ConDis Indust Health
        [1.00,  0.50,  0.60,  0.55,  0.70,  0.65,  0.40],  # Tech
        [0.50,  1.00,  0.45,  0.40,  0.45,  0.60,  0.30],  # Energy
        [0.60,  0.45,  1.00,  0.50,  0.55,  0.55,  0.35],  # Financials
        [0.55,  0.40,  0.50,  1.00,  0.55,  0.50,  0.45],  # Consumer Staples
        [0.70,  0.45,  0.55,  0.55,  1.00,  0.65,  0.40],  # Consumer Disc
        [0.65,  0.60,  0.55,  0.50,  0.65,  1.00,  0.35],  # Industrials
        [0.40,  0.30,  0.35,  0.45,  0.40,  0.35,  1.00],  # Healthcare
    ],
    Regime.RECESSION: [
        #  Tech   Energy  Fin    ConSt  ConDis Indust Health
        [1.00,  0.65,  0.70,  0.60,  0.75,  0.75,  0.45],  # Tech
        [0.65,  1.00,  0.60,  0.55,  0.60,  0.70,  0.40],  # Energy
        [0.70,  0.60,  1.00,  0.65,  0.70,  0.65,  0.45],  # Financials
        [0.60,  0.55,  0.65,  1.00,  0.60,  0.60,  0.50],  # Consumer Staples
        [0.75,  0.60,  0.70,  0.60,  1.00,  0.75,  0.45],  # Consumer Disc
        [0.75,  0.70,  0.65,  0.60,  0.75,  1.00,  0.40],  # Industrials
        [0.45,  0.40,  0.45,  0.50,  0.45,  0.40,  1.00],  # Healthcare
    ],
    Regime.RECOVERY: [
        #  Tech   Energy  Fin    ConSt  ConDis Indust Health
        [1.00,  0.35,  0.45,  0.30,  0.50,  0.40,  0.20],  # Tech
        [0.35,  1.00,  0.30,  0.25,  0.30,  0.45,  0.15],  # Energy
        [0.45,  0.30,  1.00,  0.35,  0.40,  0.40,  0.25],  # Financials
        [0.30,  0.25,  0.35,  1.00,  0.35,  0.35,  0.30],  # Consumer Staples
        [0.50,  0.30,  0.40,  0.35,  1.00,  0.45,  0.20],  # Consumer Disc
        [0.40,  0.45,  0.40,  0.35,  0.45,  1.00,  0.20],  # Industrials
        [0.20,  0.15,  0.25,  0.30,  0.20,  0.20,  1.00],  # Healthcare
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
    """Generate 7 correlated standard normal samples using Cholesky decomposition.

    Uses the stdlib random.Random for reproducible seeding,
    then applies Cholesky factor for correlation structure.
    """
    L = _get_cholesky(regime)
    z_independent = np.array([rng.gauss(0, 1) for _ in range(len(SECTOR_ORDER))])
    z_correlated = L @ z_independent
    return dict(zip(SECTOR_ORDER, z_correlated.tolist()))
