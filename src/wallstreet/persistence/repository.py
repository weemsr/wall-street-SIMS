"""CRUD operations for game persistence in SQLite."""

import json
import sqlite3
from datetime import datetime

from wallstreet.agents.base import RiskAssessment
from wallstreet.config import DEFAULT_DB_PATH
from wallstreet.models.career import CareerProfile, CareerTitle
from wallstreet.models.game import GameState, WeekResult
from wallstreet.models.narrative import RivalWeekResult
from wallstreet.models.scoring import ScoreCard
from wallstreet.persistence.schema import CREATE_TABLES, SCHEMA_VERSION


class GameRepository:
    """SQLite-backed storage for game state and history."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Create connection and ensure schema exists."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(CREATE_TABLES)
        # Check / insert schema version
        cursor = self.conn.execute("SELECT COUNT(*) FROM schema_version")
        if cursor.fetchone()[0] == 0:
            self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )
        self.conn.commit()

    def _ensure_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("Repository not initialized. Call initialize() first.")
        return self.conn

    def save_game(self, game_state: GameState) -> None:
        """Upsert the game record."""
        conn = self._ensure_conn()
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO games (
                game_id, player_name, seed, starting_cash, total_weeks,
                current_week, is_complete, created_at, updated_at, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                current_week = excluded.current_week,
                is_complete = excluded.is_complete,
                updated_at = excluded.updated_at
            """,
            (
                game_state.game_id,
                game_state.config.player_name,
                game_state.config.seed,
                game_state.config.starting_cash,
                game_state.config.total_weeks,
                game_state.current_week,
                1 if game_state.is_complete else 0,
                game_state.created_at.isoformat(),
                now,
                game_state.config.model_dump_json(),
            ),
        )
        conn.commit()

    def save_week(
        self,
        game_id: str,
        week_result: WeekResult,
        risk: RiskAssessment | None = None,
    ) -> None:
        """Insert a weekly snapshot and associated events."""
        conn = self._ensure_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO weekly_snapshots (
                game_id, week, regime, volatility_state, rate_direction,
                portfolio_value, allocation_json, sector_returns_json,
                adjusted_returns_json, portfolio_return,
                risk_score, risk_critique, week_result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                week_result.week,
                week_result.macro_state.regime.value,
                week_result.macro_state.volatility_state.value,
                week_result.macro_state.rate_direction.value,
                week_result.portfolio_value_after,
                week_result.allocation.model_dump_json(),
                week_result.sector_returns.model_dump_json(),
                week_result.adjusted_returns.model_dump_json(),
                week_result.portfolio_return,
                risk.risk_score if risk else None,
                risk.critique if risk else None,
                week_result.model_dump_json(),
            ),
        )
        # Log events
        for event in week_result.events:
            conn.execute(
                """
                INSERT INTO events_log (
                    game_id, week, event_name, event_description,
                    sector_effects_json, vol_impact
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    game_id,
                    week_result.week,
                    event.template_name,
                    event.description,
                    json.dumps(
                        {s.value: v for s, v in event.sector_effects.items()}
                    ),
                    event.vol_impact,
                ),
            )
        conn.commit()

    def save_scorecard(self, game_id: str, scorecard: ScoreCard) -> None:
        """Write final scores to the games table."""
        conn = self._ensure_conn()
        conn.execute(
            """
            UPDATE games SET
                final_value = ?,
                cagr = ?,
                max_drawdown = ?,
                sharpe_ratio = ?,
                annualized_vol = ?,
                is_complete = 1
            WHERE game_id = ?
            """,
            (
                scorecard.final_value,
                scorecard.cagr,
                scorecard.max_drawdown,
                scorecard.sharpe_ratio,
                scorecard.annualized_volatility,
                game_id,
            ),
        )
        conn.commit()

    def list_games(self) -> list[dict]:
        """List all saved games with summary info."""
        conn = self._ensure_conn()
        cursor = conn.execute(
            """
            SELECT game_id, player_name, seed, total_weeks, current_week,
                   is_complete, created_at, final_value, sharpe_ratio
            FROM games ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def save_career(self, profile: CareerProfile) -> None:
        """Upsert a career profile."""
        conn = self._ensure_conn()
        conn.execute(
            """
            INSERT INTO career_profiles (
                player_name, title, seasons_played, lifetime_cagr,
                best_sharpe, worst_drawdown, total_pnl, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_name) DO UPDATE SET
                title = excluded.title,
                seasons_played = excluded.seasons_played,
                lifetime_cagr = excluded.lifetime_cagr,
                best_sharpe = excluded.best_sharpe,
                worst_drawdown = excluded.worst_drawdown,
                total_pnl = excluded.total_pnl,
                updated_at = excluded.updated_at
            """,
            (
                profile.player_name,
                profile.title.value,
                profile.seasons_played,
                profile.lifetime_cagr,
                profile.best_sharpe,
                profile.worst_drawdown,
                profile.total_pnl,
                profile.updated_at.isoformat(),
            ),
        )
        conn.commit()

    def load_career(self, player_name: str) -> CareerProfile | None:
        """Load a career profile by player name. Returns None if not found."""
        conn = self._ensure_conn()
        cursor = conn.execute(
            "SELECT * FROM career_profiles WHERE player_name = ?",
            (player_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return CareerProfile(
            player_name=row["player_name"],
            title=CareerTitle(row["title"]),
            seasons_played=row["seasons_played"],
            lifetime_cagr=row["lifetime_cagr"] or 0.0,
            best_sharpe=row["best_sharpe"] or 0.0,
            worst_drawdown=row["worst_drawdown"] or 0.0,
            total_pnl=row["total_pnl"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def save_rival_week(
        self, game_id: str, week: int, result: RivalWeekResult
    ) -> None:
        """Save a rival PM's weekly snapshot."""
        conn = self._ensure_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO rival_snapshots (
                game_id, week, rival_name, strategy_type,
                allocation_json, portfolio_value, portfolio_return
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                week,
                result.rival_name,
                result.strategy_type,
                result.allocation.model_dump_json(),
                result.portfolio_value,
                result.portfolio_return,
            ),
        )
        conn.commit()

    def close(self) -> None:
        """Close the DB connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
