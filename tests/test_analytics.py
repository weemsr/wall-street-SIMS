"""Tests for expanded analytics module."""

import pytest

from wallstreet.analytics.expanded import (
    compute_concentration_score,
    compute_drawdown_series,
    compute_expanded_metrics,
    compute_rolling_sharpe,
    compute_rolling_volatility,
)
from wallstreet.models.enums import Sector
from wallstreet.models.portfolio import Allocation


class TestRollingVolatility:
    def test_empty_returns(self) -> None:
        assert compute_rolling_volatility([]) == []

    def test_single_return(self) -> None:
        result = compute_rolling_volatility([0.01])
        assert result == [0.0]  # Can't compute vol from 1 point

    def test_constant_returns_zero_vol(self) -> None:
        """Constant returns yield zero volatility."""
        result = compute_rolling_volatility([0.01, 0.01, 0.01, 0.01])
        assert all(v == 0.0 for v in result)

    def test_increasing_length(self) -> None:
        """Output length matches input."""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        result = compute_rolling_volatility(returns, window=4)
        assert len(result) == len(returns)

    def test_positive_values(self) -> None:
        """Vol is non-negative."""
        returns = [0.05, -0.03, 0.02, -0.04, 0.01]
        result = compute_rolling_volatility(returns)
        assert all(v >= 0 for v in result)


class TestRollingSharpe:
    def test_empty_returns(self) -> None:
        assert compute_rolling_sharpe([]) == []

    def test_constant_returns(self) -> None:
        """Zero vol yields zero Sharpe."""
        result = compute_rolling_sharpe([0.01, 0.01, 0.01])
        assert all(v == 0.0 for v in result)

    def test_positive_sharpe_for_positive_returns(self) -> None:
        """Positive average returns with some vol should yield positive Sharpe."""
        returns = [0.02, 0.03, 0.01, 0.04]
        result = compute_rolling_sharpe(returns)
        # All returns are positive, so Sharpe should be positive
        assert result[-1] > 0

    def test_output_length(self) -> None:
        returns = [0.01, -0.02, 0.03, -0.01]
        result = compute_rolling_sharpe(returns)
        assert len(result) == len(returns)


class TestDrawdownSeries:
    def test_empty_values(self) -> None:
        assert compute_drawdown_series([]) == []

    def test_always_increasing(self) -> None:
        """Monotonically increasing values have zero drawdown."""
        values = [100, 110, 120, 130]
        result = compute_drawdown_series(values)
        assert all(dd == 0.0 for dd in result)

    def test_drawdown_after_peak(self) -> None:
        """Drop after peak shows negative drawdown."""
        values = [100, 120, 100]
        result = compute_drawdown_series(values)
        assert result[0] == 0.0
        assert result[1] == 0.0
        # 100/120 - 1 ≈ -0.1667
        assert result[2] < 0
        assert abs(result[2] - (-1 / 6)) < 0.01

    def test_deep_drawdown(self) -> None:
        """50% drop shows -0.5 drawdown."""
        values = [1000, 1000, 500]
        result = compute_drawdown_series(values)
        assert abs(result[2] - (-0.5)) < 0.001

    def test_recovery(self) -> None:
        """Recovery back to peak shows 0 drawdown."""
        values = [100, 120, 100, 120]
        result = compute_drawdown_series(values)
        assert result[3] == 0.0


class TestConcentrationScore:
    def test_equal_weight(self) -> None:
        """Equal weight across 5 sectors: HHI = 5 * 0.2^2 = 0.20."""
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        hhi = compute_concentration_score(alloc)
        assert abs(hhi - 0.2) < 0.001

    def test_concentrated(self) -> None:
        """100% in one sector: HHI = 1.0."""
        alloc = Allocation(weights={
            Sector.TECH: 100.0,
            Sector.ENERGY: 0.0,
            Sector.FINANCIALS: 0.0,
            Sector.CONSUMER: 0.0,
            Sector.INDUSTRIALS: 0.0,
        })
        hhi = compute_concentration_score(alloc)
        assert abs(hhi - 1.0) < 0.001

    def test_moderate_concentration(self) -> None:
        """50/12.5/12.5/12.5/12.5 allocation."""
        alloc = Allocation(weights={
            Sector.TECH: 50.0,
            Sector.ENERGY: 12.5,
            Sector.FINANCIALS: 12.5,
            Sector.CONSUMER: 12.5,
            Sector.INDUSTRIALS: 12.5,
        })
        hhi = compute_concentration_score(alloc)
        # 0.5^2 + 4*0.125^2 = 0.25 + 0.0625 = 0.3125
        assert abs(hhi - 0.3125) < 0.001


class TestExpandedMetrics:
    def test_integration(self) -> None:
        """Full metrics computation produces valid output."""
        values = [1_000_000, 1_020_000, 990_000, 1_010_000, 1_050_000]
        returns = [0.02, -0.0294, 0.0202, 0.0396]
        allocs = [
            Allocation(weights={s: 20.0 for s in Sector})
            for _ in returns
        ]
        metrics = compute_expanded_metrics(values, returns, allocs)

        assert len(metrics.rolling_volatility) == len(returns)
        assert len(metrics.rolling_sharpe) == len(returns)
        assert len(metrics.drawdown_series) == len(values)
        assert len(metrics.concentration_scores) == len(allocs)
        assert metrics.current_concentration == 0.2  # equal weight
