"""Expanded analytics — rolling metrics, drawdown series, concentration."""

import math

from wallstreet.models.analytics import ExpandedMetrics
from wallstreet.models.portfolio import Allocation


def compute_rolling_volatility(
    weekly_returns: list[float], window: int = 4
) -> list[float]:
    """Compute rolling annualized volatility over a sliding window.

    Returns one value per week starting from week 1 (first window may be smaller).
    """
    if not weekly_returns:
        return []

    result: list[float] = []
    for i in range(len(weekly_returns)):
        start = max(0, i - window + 1)
        segment = weekly_returns[start : i + 1]
        if len(segment) < 2:
            result.append(0.0)
            continue
        mean = sum(segment) / len(segment)
        variance = sum((r - mean) ** 2 for r in segment) / (len(segment) - 1)
        weekly_vol = math.sqrt(variance)
        annualized = weekly_vol * math.sqrt(12)
        result.append(round(annualized, 6))
    return result


def compute_rolling_sharpe(
    weekly_returns: list[float], window: int = 4, risk_free: float = 0.0
) -> list[float]:
    """Compute rolling annualized Sharpe ratio over a sliding window.

    Returns one value per week. Sharpe = 0 if volatility is zero.
    """
    if not weekly_returns:
        return []

    result: list[float] = []
    for i in range(len(weekly_returns)):
        start = max(0, i - window + 1)
        segment = weekly_returns[start : i + 1]
        if len(segment) < 2:
            result.append(0.0)
            continue
        mean = sum(segment) / len(segment)
        variance = sum((r - mean) ** 2 for r in segment) / (len(segment) - 1)
        weekly_vol = math.sqrt(variance)
        if weekly_vol < 1e-10:
            result.append(0.0)
            continue
        weekly_sharpe = (mean - risk_free) / weekly_vol
        annualized = weekly_sharpe * math.sqrt(12)
        result.append(round(annualized, 6))
    return result


def compute_drawdown_series(weekly_values: list[float]) -> list[float]:
    """Compute drawdown at each point as a percentage from peak.

    Returns negative values (e.g., -0.15 means 15% below peak).
    Returns 0.0 at or above the peak.
    """
    if not weekly_values:
        return []

    result: list[float] = []
    peak = weekly_values[0]
    for value in weekly_values:
        peak = max(peak, value)
        if peak > 0:
            dd = (value - peak) / peak
        else:
            dd = 0.0
        result.append(round(dd, 6))
    return result


def compute_concentration_score(allocation: Allocation) -> float:
    """Compute the Herfindahl-Hirschman Index for portfolio concentration.

    Uses absolute values normalized by gross exposure so HHI stays
    in the 0.20–1.0 range regardless of short positions.
    """
    fractions = allocation.as_fractions
    gross = sum(abs(f) for f in fractions.values())
    if gross < 1e-10:
        return 0.0
    normalized = {s: abs(f) / gross for s, f in fractions.items()}
    hhi = sum(f ** 2 for f in normalized.values())
    return round(hhi, 6)


def compute_expanded_metrics(
    weekly_values: list[float],
    weekly_returns: list[float],
    weekly_allocations: list[Allocation],
) -> ExpandedMetrics:
    """Compute all expanded metrics from game history."""
    rolling_vol = compute_rolling_volatility(weekly_returns)
    rolling_sharpe = compute_rolling_sharpe(weekly_returns)
    drawdown_series = compute_drawdown_series(weekly_values)
    concentration_scores = [
        compute_concentration_score(alloc) for alloc in weekly_allocations
    ]
    gross_exposure_series = [alloc.gross_exposure for alloc in weekly_allocations]

    return ExpandedMetrics(
        rolling_volatility=rolling_vol,
        rolling_sharpe=rolling_sharpe,
        drawdown_series=drawdown_series,
        concentration_scores=concentration_scores,
        gross_exposure_series=gross_exposure_series,
        current_rolling_vol=rolling_vol[-1] if rolling_vol else 0.0,
        current_rolling_sharpe=rolling_sharpe[-1] if rolling_sharpe else 0.0,
        current_drawdown=drawdown_series[-1] if drawdown_series else 0.0,
        current_concentration=concentration_scores[-1] if concentration_scores else 0.0,
        current_gross_exposure=gross_exposure_series[-1] if gross_exposure_series else 1.0,
    )
