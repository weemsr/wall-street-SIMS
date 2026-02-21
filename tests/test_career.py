"""Tests for career progression system."""

import pytest

from wallstreet.career.progression import (
    compute_title,
    create_new_career,
    update_career_after_season,
)
from wallstreet.models.career import CareerProfile, CareerTitle
from wallstreet.models.scoring import ScoreCard


class TestCareerCreation:
    def test_new_career_defaults(self) -> None:
        """New career starts with default values."""
        career = create_new_career("Test Player")
        assert career.player_name == "Test Player"
        assert career.title == CareerTitle.RETAIL_SPECULATOR
        assert career.seasons_played == 0
        assert career.lifetime_cagr == 0.0
        assert career.best_sharpe == 0.0
        assert career.total_pnl == 0.0


class TestTitleComputation:
    def test_retail_speculator(self) -> None:
        """Default title with no seasons."""
        career = create_new_career("Test")
        assert compute_title(career) == CareerTitle.RETAIL_SPECULATOR

    def test_junior_pm(self) -> None:
        """1+ season gets Junior PM."""
        career = CareerProfile(
            player_name="Test",
            seasons_played=1,
            lifetime_cagr=-0.05,
            best_sharpe=0.3,
            worst_drawdown=-0.20,
            total_pnl=-50000.0,
        )
        assert compute_title(career) == CareerTitle.JUNIOR_PM

    def test_macro_operator(self) -> None:
        """3+ seasons with positive CAGR gets Macro Operator."""
        career = CareerProfile(
            player_name="Test",
            seasons_played=3,
            lifetime_cagr=0.05,
            best_sharpe=0.8,
            worst_drawdown=-0.15,
            total_pnl=100000.0,
        )
        assert compute_title(career) == CareerTitle.MACRO_OPERATOR

    def test_institutional_strategist(self) -> None:
        """5+ seasons with Sharpe > 1.0 gets Institutional Strategist."""
        career = CareerProfile(
            player_name="Test",
            seasons_played=5,
            lifetime_cagr=0.10,
            best_sharpe=1.2,
            worst_drawdown=-0.18,
            total_pnl=500000.0,
        )
        assert compute_title(career) == CareerTitle.INSTITUTIONAL_STRATEGIST

    def test_legendary_allocator(self) -> None:
        """10+ seasons, Sharpe > 1.5, drawdown > -25% gets Legendary."""
        career = CareerProfile(
            player_name="Test",
            seasons_played=10,
            lifetime_cagr=0.15,
            best_sharpe=1.8,
            worst_drawdown=-0.20,
            total_pnl=2000000.0,
        )
        assert compute_title(career) == CareerTitle.LEGENDARY_ALLOCATOR

    def test_legendary_fails_on_bad_drawdown(self) -> None:
        """Deep drawdown prevents Legendary title."""
        career = CareerProfile(
            player_name="Test",
            seasons_played=10,
            lifetime_cagr=0.15,
            best_sharpe=1.8,
            worst_drawdown=-0.30,  # Too bad
            total_pnl=2000000.0,
        )
        # Falls back to Institutional Strategist
        assert compute_title(career) == CareerTitle.INSTITUTIONAL_STRATEGIST


class TestCareerUpdate:
    def _make_scorecard(self, cagr: float, sharpe: float, max_dd: float, pnl: float) -> ScoreCard:
        return ScoreCard(
            initial_value=1_000_000.0,
            final_value=1_000_000.0 + pnl,
            total_return_pct=(pnl / 1_000_000.0) * 100,
            cagr=cagr,
            max_drawdown=max_dd,
            annualized_volatility=0.15,
            sharpe_ratio=sharpe,
            total_weeks=26,
        )

    def test_first_season_updates(self) -> None:
        """First season correctly updates all stats."""
        career = create_new_career("Test")
        scorecard = self._make_scorecard(
            cagr=0.10, sharpe=1.2, max_dd=-0.08, pnl=50000.0
        )
        updated = update_career_after_season(career, scorecard)
        assert updated.seasons_played == 1
        assert updated.lifetime_cagr == 0.10
        assert updated.best_sharpe == 1.2
        assert updated.worst_drawdown == -0.08
        assert updated.total_pnl == 50000.0
        assert updated.title == CareerTitle.JUNIOR_PM

    def test_multi_season_averaging(self) -> None:
        """CAGR averages across multiple seasons."""
        career = create_new_career("Test")
        sc1 = self._make_scorecard(cagr=0.10, sharpe=0.8, max_dd=-0.10, pnl=50000)
        sc2 = self._make_scorecard(cagr=0.20, sharpe=1.5, max_dd=-0.05, pnl=100000)

        career = update_career_after_season(career, sc1)
        career = update_career_after_season(career, sc2)

        assert career.seasons_played == 2
        assert abs(career.lifetime_cagr - 0.15) < 0.01  # average of 0.10 and 0.20
        assert career.best_sharpe == 1.5
        assert career.worst_drawdown == -0.10  # worst of -0.10 and -0.05
        assert career.total_pnl == 150000.0

    def test_title_progresses(self) -> None:
        """Title advances through seasons."""
        career = create_new_career("Test")
        sc = self._make_scorecard(cagr=0.10, sharpe=1.2, max_dd=-0.08, pnl=50000)
        for _ in range(5):
            career = update_career_after_season(career, sc)
        assert career.title == CareerTitle.INSTITUTIONAL_STRATEGIST
