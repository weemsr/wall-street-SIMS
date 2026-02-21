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

    def test_must_sum_to_100(self) -> None:
        weights = {s: 19.0 for s in Sector}  # sums to 95
        with pytest.raises(ValidationError, match="sum to 100%"):
            Allocation(weights=weights)

    def test_over_100_rejected(self) -> None:
        weights = {s: 21.0 for s in Sector}  # sums to 105
        with pytest.raises(ValidationError, match="sum to 100%"):
            Allocation(weights=weights)

    def test_no_negative_weights(self) -> None:
        weights = {
            Sector.TECH: 120.0, Sector.ENERGY: -20.0,
            Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
            Sector.INDUSTRIALS: 0.0,
        }
        with pytest.raises(ValidationError, match="Negative weight"):
            Allocation(weights=weights)

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
            annualized_volatility=0.15, sharpe_ratio=2.5, total_weeks=26,
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
            annualized_volatility=0.20, sharpe_ratio=1.2, total_weeks=26,
        )
        assert sc.letter_grade == "B"
