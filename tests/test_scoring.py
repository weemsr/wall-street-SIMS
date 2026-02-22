"""Tests for scoring calculation functions."""

import math

import pytest

from wallstreet.scoring.calculator import (
    compute_annualized_volatility,
    compute_cagr,
    compute_max_drawdown,
    compute_scorecard,
    compute_sharpe_ratio,
)


class TestCAGR:
    def test_doubling_in_26_months(self) -> None:
        # (2)^(12/26) - 1 ≈ 0.369 (36.9% annualized)
        cagr = compute_cagr(1_000_000, 2_000_000, 26)
        expected = (2.0 ** (12.0 / 26.0)) - 1.0
        assert cagr == pytest.approx(expected, rel=1e-6)

    def test_no_change(self) -> None:
        cagr = compute_cagr(1_000_000, 1_000_000, 26)
        assert cagr == pytest.approx(0.0, abs=1e-10)

    def test_loss(self) -> None:
        cagr = compute_cagr(1_000_000, 500_000, 26)
        assert cagr < 0

    def test_total_loss_returns_negative(self) -> None:
        cagr = compute_cagr(1_000_000, 0, 26)
        assert cagr == -1.0

    def test_zero_initial(self) -> None:
        cagr = compute_cagr(0, 1_000_000, 26)
        assert cagr == -1.0


class TestMaxDrawdown:
    def test_monotonic_increase(self) -> None:
        values = [100, 110, 120, 130, 140]
        assert compute_max_drawdown(values) == pytest.approx(0.0)

    def test_known_drawdown(self) -> None:
        values = [100, 110, 90, 95]
        # Peak = 110, trough = 90, dd = (90-110)/110 = -0.1818...
        dd = compute_max_drawdown(values)
        assert dd == pytest.approx(-20 / 110, rel=1e-6)

    def test_single_value(self) -> None:
        assert compute_max_drawdown([100]) == 0.0

    def test_deep_drawdown(self) -> None:
        values = [1000, 1200, 800, 600, 900]
        # Peak = 1200, trough = 600, dd = -600/1200 = -0.50
        dd = compute_max_drawdown(values)
        assert dd == pytest.approx(-0.50)


class TestAnnualizedVolatility:
    def test_constant_returns(self) -> None:
        returns = [0.01] * 10
        vol = compute_annualized_volatility(returns)
        assert vol == pytest.approx(0.0, abs=1e-10)

    def test_known_value(self) -> None:
        returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        n = len(returns)
        mean = sum(returns) / n
        var = sum((r - mean) ** 2 for r in returns) / (n - 1)
        expected = math.sqrt(var) * math.sqrt(12)
        vol = compute_annualized_volatility(returns)
        assert vol == pytest.approx(expected, rel=1e-6)

    def test_single_return(self) -> None:
        assert compute_annualized_volatility([0.01]) == 0.0


class TestSharpeRatio:
    def test_positive_returns(self) -> None:
        returns = [0.01, 0.02, 0.01, 0.015, 0.005]
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe > 0

    def test_negative_returns(self) -> None:
        returns = [-0.01, -0.02, -0.01, -0.015, -0.005]
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe < 0

    def test_zero_vol(self) -> None:
        returns = [0.01] * 10
        sharpe = compute_sharpe_ratio(returns)
        assert sharpe == 0.0


class TestScoreCard:
    def test_integration(self) -> None:
        # 5 weeks: start at 1M, end at 1.1M
        values = [1_000_000, 1_020_000, 1_010_000, 1_050_000, 1_080_000, 1_100_000]
        sc = compute_scorecard(values)
        assert sc.initial_value == 1_000_000
        assert sc.final_value == 1_100_000
        assert sc.total_return_pct == pytest.approx(10.0)
        assert sc.total_weeks == 5
        assert sc.cagr > 0
        assert sc.max_drawdown <= 0
        assert sc.annualized_volatility > 0
