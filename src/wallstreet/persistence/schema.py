"""SQLite schema definitions."""

SCHEMA_VERSION = 2

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    player_name TEXT NOT NULL,
    seed INTEGER NOT NULL,
    starting_cash REAL NOT NULL,
    total_weeks INTEGER NOT NULL,
    current_week INTEGER NOT NULL DEFAULT 0,
    is_complete INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    final_value REAL,
    cagr REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    annualized_vol REAL,
    config_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    week INTEGER NOT NULL,
    regime TEXT NOT NULL,
    volatility_state TEXT NOT NULL,
    rate_direction TEXT NOT NULL,
    portfolio_value REAL NOT NULL,
    allocation_json TEXT NOT NULL,
    sector_returns_json TEXT NOT NULL,
    adjusted_returns_json TEXT NOT NULL,
    portfolio_return REAL NOT NULL,
    risk_score INTEGER,
    risk_critique TEXT,
    week_result_json TEXT NOT NULL,
    UNIQUE(game_id, week)
);

CREATE TABLE IF NOT EXISTS events_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    week INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_description TEXT NOT NULL,
    sector_effects_json TEXT NOT NULL,
    vol_impact REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS career_profiles (
    player_name TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    seasons_played INTEGER NOT NULL DEFAULT 0,
    lifetime_cagr REAL,
    best_sharpe REAL,
    worst_drawdown REAL,
    total_pnl REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rival_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    week INTEGER NOT NULL,
    rival_name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    allocation_json TEXT NOT NULL,
    portfolio_value REAL NOT NULL,
    portfolio_return REAL NOT NULL,
    UNIQUE(game_id, week)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_game_week
    ON weekly_snapshots(game_id, week);
CREATE INDEX IF NOT EXISTS idx_events_game_week
    ON events_log(game_id, week);
CREATE INDEX IF NOT EXISTS idx_rival_game_week
    ON rival_snapshots(game_id, week);
"""
