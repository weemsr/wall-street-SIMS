"""Tests for SQLite persistence round-trips."""

import pytest

from wallstreet.agents.base import RiskAssessment
from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.events import ShockEvent
from wallstreet.models.game import GameConfig, GameState, WeekResult
from wallstreet.models.market import MacroState, SectorReturns
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState
from wallstreet.models.scoring import ScoreCard
from wallstreet.persistence.repository import GameRepository


@pytest.fixture
def repo() -> GameRepository:
    """In-memory SQLite repository for testing."""
    r = GameRepository(db_path=":memory:")
    r.initialize()
    yield r
    r.close()


@pytest.fixture
def sample_game() -> GameState:
    config = GameConfig(seed=42, starting_cash=1_000_000.0, total_weeks=26)
    macro = MacroState(
        regime=Regime.BULL,
        volatility_state=VolatilityState.NORMAL,
        rate_direction=RateDirection.STABLE,
        week=0,
    )
    portfolio = PortfolioState(
        cash=1_000_000.0,
        holdings=Holdings(positions={s: 0.0 for s in Sector}),
        total_value=1_000_000.0,
        week=0,
    )
    return GameState(
        config=config,
        macro_state=macro,
        portfolio=portfolio,
        weekly_values=[1_000_000.0],
    )


@pytest.fixture
def sample_week_result() -> WeekResult:
    macro = MacroState(
        regime=Regime.BULL,
        volatility_state=VolatilityState.NORMAL,
        rate_direction=RateDirection.STABLE,
        week=1,
    )
    alloc = Allocation(weights={s: 20.0 for s in Sector})
    returns = SectorReturns(returns={s: 0.01 for s in Sector})
    event = ShockEvent(
        template_name="Test Event",
        description="A test event occurred.",
        sector_effects={Sector.TECH: 0.02, Sector.ENERGY: -0.01,
                        Sector.FINANCIALS: 0.0, Sector.CONSUMER: 0.0,
                        Sector.INDUSTRIALS: 0.0},
        vol_impact=0.1,
        week=1,
    )
    adjusted = SectorReturns(returns={
        Sector.TECH: 0.03, Sector.ENERGY: 0.00,
        Sector.FINANCIALS: 0.01, Sector.CONSUMER: 0.01,
        Sector.INDUSTRIALS: 0.01,
    })
    return WeekResult(
        week=1,
        macro_state=macro,
        allocation=alloc,
        sector_returns=returns,
        events=[event],
        adjusted_returns=adjusted,
        portfolio_return=0.012,
        portfolio_value_before=1_000_000.0,
        portfolio_value_after=1_012_000.0,
    )


class TestGameRepository:
    def test_save_and_list(self, repo: GameRepository, sample_game: GameState) -> None:
        repo.save_game(sample_game)
        games = repo.list_games()
        assert len(games) >= 1
        assert any(g["game_id"] == sample_game.game_id for g in games)

    def test_save_week(
        self,
        repo: GameRepository,
        sample_game: GameState,
        sample_week_result: WeekResult,
    ) -> None:
        repo.save_game(sample_game)
        risk = RiskAssessment(risk_score=3, critique="Looks fine.", warnings=[])
        repo.save_week(sample_game.game_id, sample_week_result, risk)

        # Verify by querying directly
        conn = repo._ensure_conn()
        row = conn.execute(
            "SELECT * FROM weekly_snapshots WHERE game_id = ? AND week = ?",
            (sample_game.game_id, 1),
        ).fetchone()
        assert row is not None
        assert row["risk_score"] == 3

    def test_save_scorecard(
        self, repo: GameRepository, sample_game: GameState,
    ) -> None:
        repo.save_game(sample_game)
        sc = ScoreCard(
            initial_value=1e6, final_value=1.1e6,
            total_return_pct=10.0, cagr=0.2,
            max_drawdown=-0.05, annualized_volatility=0.15,
            sharpe_ratio=1.2, total_weeks=26,
        )
        repo.save_scorecard(sample_game.game_id, sc)

        games = repo.list_games()
        game = next(g for g in games if g["game_id"] == sample_game.game_id)
        assert game["sharpe_ratio"] == pytest.approx(1.2)
        assert game["is_complete"] == 1

    def test_events_logged(
        self,
        repo: GameRepository,
        sample_game: GameState,
        sample_week_result: WeekResult,
    ) -> None:
        repo.save_game(sample_game)
        repo.save_week(sample_game.game_id, sample_week_result, None)

        conn = repo._ensure_conn()
        rows = conn.execute(
            "SELECT * FROM events_log WHERE game_id = ?",
            (sample_game.game_id,),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["event_name"] == "Test Event"
