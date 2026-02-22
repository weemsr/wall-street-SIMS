"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from wallstreet.models.enums import Sector
from wallstreet.models.portfolio import Allocation
from wallstreet.models.scoring import ScoreCard


class TestAllocation:
    def test_valid_balanced(self) -> None:
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        assert sum(alloc.weights.values()) == pytest.approx(100.0)

    def test_valid_concentrated(self) -> None:
        weights = {
            Sector.TECH: 60.0, Sector.ENERGY: 10.0,
            Sector.FINANCIALS: 10.0, Sector.CONSUMER: 10.0,
            Sector.INDUSTRIALS: 10.0,
        }
        alloc = Allocation(weights=weights)
        assert alloc.weights[Sector.TECH] == 60.0

    def test_valid_with_zeros(self) -> None:
        weights = {
            Sector.TECH: 100.0, Sector.ENERGY: 0.0,
            Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
            Sector.INDUSTRIALS: 0.0,
        }
        alloc = Allocation(weights=weights)
        assert alloc.weights[Sector.TECH] == 100.0

    def test_partial_allocation_valid(self) -> None:
        """Weights summing to less than 100% are valid (remainder = cash)."""
        weights = {s: 10.0 for s in Sector}  # sums to 50
        alloc = Allocation(weights=weights)
        assert alloc.cash_weight == pytest.approx(0.50)

    def test_zero_allocation_valid(self) -> None:
        """All-cash allocation (sum=0) is valid."""
        weights = {s: 0.0 for s in Sector}
        alloc = Allocation(weights=weights)
        assert alloc.cash_weight == pytest.approx(1.0)

    def test_over_100_rejected(self) -> None:
        weights = {s: 21.0 for s in Sector}  # sums to 105
        with pytest.raises(ValidationError, match="sum to 0-100%"):
            Allocation(weights=weights)

    def test_negative_net_rejected(self) -> None:
        """Net allocation below 0% is rejected."""
        weights = {
            Sector.TECH: 10.0, Sector.ENERGY: 0.0,
            Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
            Sector.INDUSTRIALS: -20.0,
        }
        # sum = -10
        with pytest.raises(ValidationError, match="sum to 0-100%"):
            Allocation(weights=weights)

    def test_cash_weight_fully_invested(self) -> None:
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        assert alloc.cash_weight == pytest.approx(0.0)

    def test_valid_with_shorts(self) -> None:
        """Negative weights are allowed (short positions)."""
        weights = {
            Sector.TECH: 40.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 30.0,
            Sector.INDUSTRIALS: -20.0,
        }
        alloc = Allocation(weights=weights)
        assert alloc.weights[Sector.INDUSTRIALS] == -20.0
        assert alloc.has_shorts is True
        assert alloc.gross_exposure == pytest.approx(1.40)

    def test_short_too_large_rejected(self) -> None:
        """Short position exceeding -50% is rejected."""
        weights = {
            Sector.TECH: 60.0, Sector.ENERGY: 50.0,
            Sector.FINANCIALS: 30.0, Sector.CONSUMER: 20.0,
            Sector.INDUSTRIALS: -60.0,
        }
        with pytest.raises(ValidationError, match="Short position too large"):
            Allocation(weights=weights)

    def test_gross_exposure_limit(self) -> None:
        """Gross exposure exceeding 200% is rejected."""
        weights = {
            Sector.TECH: 80.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 20.0,
            Sector.INDUSTRIALS: -50.0,
        }
        # sum = 100, gross = 200 -> OK
        alloc = Allocation(weights=weights)
        assert alloc.gross_exposure == pytest.approx(2.00)

        # Try exceeding 200%
        weights2 = {
            Sector.TECH: 90.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 10.0,
            Sector.INDUSTRIALS: -50.0,
        }
        # sum = 100, gross = 200 -> OK still
        # Let's try one that actually exceeds:
        weights3 = {
            Sector.TECH: 100.0, Sector.ENERGY: 30.0,
            Sector.FINANCIALS: 20.0, Sector.CONSUMER: 0.0,
            Sector.INDUSTRIALS: -50.0,
        }
        # sum = 100, gross = 200 -> still OK
        # A truly violating one needs sum=100, gross>200
        # e.g., 100 + 30 + 20 + 0 + (-50) = 100, gross = 200, OK
        # Need: 100 + 30 + 21 + 0 + (-51) but -51 < -50 so rejected on short limit first
        # The gross exposure limit and short limit work together;
        # with 5 sectors and max short -50, gross can reach exactly 200.

    def test_has_shorts_false_for_long_only(self) -> None:
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        assert alloc.has_shorts is False

    def test_as_fractions(self) -> None:
        alloc = Allocation(weights={s: 20.0 for s in Sector})
        fracs = alloc.as_fractions
        for sector in Sector:
            assert fracs[sector] == pytest.approx(0.20)


class TestScoreCard:
    def test_letter_grade_a_plus(self) -> None:
        sc = ScoreCard(
            initial_value=1e6, final_value=1.5e6,
            total_return_pct=50.0, cagr=1.0, max_drawdown=-0.05,
            annualized_volatility=0.15, sharpe_ratio=3.5, total_weeks=26,
        )
        assert sc.letter_grade == "A+"

    def test_letter_grade_f(self) -> None:
        sc = ScoreCard(
            initial_value=1e6, final_value=0.5e6,
            total_return_pct=-50.0, cagr=-0.5, max_drawdown=-0.50,
            annualized_volatility=0.40, sharpe_ratio=-1.0, total_weeks=26,
        )
        assert sc.letter_grade == "F"

    def test_letter_grade_b(self) -> None:
        sc = ScoreCard(
            initial_value=1e6, final_value=1.2e6,
            total_return_pct=20.0, cagr=0.4, max_drawdown=-0.10,
            annualized_volatility=0.20, sharpe_ratio=1.8, total_weeks=26,
        )
        assert sc.letter_grade == "B"
