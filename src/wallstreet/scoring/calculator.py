"""Performance metric calculations."""

import math

from wallstreet.models.scoring import ScoreCard


def compute_cagr(initial: float, final: float, weeks: int) -> float:
    """Compute annualized return (CAGR).

    Annualizes using 12 months/year: (final/initial)^(12/periods) - 1
    """
    if initial <= 0 or final <= 0 or weeks <= 0:
        return -1.0
    years_fraction = weeks / 12.0
    return (final / initial) ** (1.0 / years_fraction) - 1.0


def compute_max_drawdown(weekly_values: list[float]) -> float:
    """Compute maximum peak-to-trough drawdown.

    Returns a negative number (e.g., -0.15 for 15% drawdown).
    Returns 0.0 if values only increase.
    """
    if len(weekly_values) < 2:
        return 0.0
    peak = weekly_values[0]
    max_dd = 0.0
    for value in weekly_values[1:]:
        if value > peak:
            peak = value
        dd = (value - peak) / peak
        if dd < max_dd:
            max_dd = dd
    return max_dd


def compute_annualized_volatility(weekly_returns: list[float]) -> float:
    """Annualized volatility from monthly returns.

    ann_vol = monthly_std * sqrt(12)
    Uses sample standard deviation (n-1 denominator).
    """
    if len(weekly_returns) < 2:
        return 0.0
    n = len(weekly_returns)
    mean = sum(weekly_returns) / n
    variance = sum((r - mean) ** 2 for r in weekly_returns) / (n - 1)
    weekly_std = math.sqrt(variance)
    return weekly_std * math.sqrt(12)


def compute_sharpe_ratio(
    weekly_returns: list[float], risk_free_rate: float = 0.0
) -> float:
    """Sharpe ratio (annualized return / annualized vol).

    Uses simple annualization: mean_monthly * 12 for return.
    """
    if len(weekly_returns) < 2:
        return 0.0
    ann_vol = compute_annualized_volatility(weekly_returns)
    if ann_vol < 1e-10:
        return 0.0
    mean_weekly = sum(weekly_returns) / len(weekly_returns)
    ann_return = mean_weekly * 12
    return (ann_return - risk_free_rate) / ann_vol


def compute_scorecard(weekly_values: list[float]) -> ScoreCard:
    """Compute all scoring metrics from weekly portfolio values.

    Args:
        weekly_values: List of portfolio values, length = total_weeks + 1
                       (index 0 = initial value).
    """
    initial = weekly_values[0]
    final = weekly_values[-1]
    weeks = len(weekly_values) - 1

    weekly_returns = [
        (weekly_values[i] - weekly_values[i - 1]) / weekly_values[i - 1]
        for i in range(1, len(weekly_values))
    ]

    return ScoreCard(
        initial_value=initial,
        final_value=final,
        total_return_pct=(final - initial) / initial * 100,
        cagr=compute_cagr(initial, final, weeks),
        max_drawdown=compute_max_drawdown(weekly_values),
        annualized_volatility=compute_annualized_volatility(weekly_returns),
        sharpe_ratio=compute_sharpe_ratio(weekly_returns),
        total_weeks=weeks,
    )
