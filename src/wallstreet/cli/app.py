"""Main game loop orchestrator."""

from __future__ import annotations

import random
from collections.abc import Callable

from rich.console import Console

from wallstreet.agents import create_risk_agent
from wallstreet.analytics.expanded import compute_expanded_metrics
from wallstreet.career.progression import (
    create_new_career,
    update_career_after_season,
)
from wallstreet.cli.display import (
    display_career_status,
    display_events,
    display_expanded_analytics,
    display_fed_statement,
    display_final_scorecard,
    display_headlines,
    display_intro,
    display_macro_state,
    display_portfolio,
    display_risk_assessment,
    display_rival_comparison,
    display_short_thesis,
    display_week_header,
    display_week_results,
)
from wallstreet.cli.prompts import prompt_allocation, prompt_revise_allocation
from wallstreet.config import INITIAL_RATE_DIR, INITIAL_REGIME, INITIAL_VOL_STATE
from wallstreet.event_engine.generator import generate_weekly_events
from wallstreet.layers.competition import GameCompetitionLayer
from wallstreet.layers.narrative import GameNarrativeLayer
from wallstreet.market_engine.regime import advance_macro_state
from wallstreet.market_engine.returns import apply_events, generate_sector_returns
from wallstreet.models.enums import Sector
from wallstreet.models.game import GameConfig, GameState, WeekResult
from wallstreet.models.market import MacroState, SectorReturns
from wallstreet.models.portfolio import Allocation, Holdings, PortfolioState
from wallstreet.persistence.repository import GameRepository
from wallstreet.scoring.calculator import compute_scorecard


def run_game(
    config: GameConfig,
    con: Console | None = None,
    input_fn: Callable[[str], str] | None = None,
    confirm_fn: Callable[[str], bool] | None = None,
    flush_fn: Callable[[], None] | None = None,
) -> None:
    """Run a complete game session.

    Parameters
    ----------
    config : GameConfig
        Game configuration (seed, player name, weeks).
    con : Console | None
        Rich Console to render into. Defaults to stdout console.
    input_fn : Callable | None
        Replacement for console.input() — used by WebSocket bridge.
    confirm_fn : Callable | None
        Replacement for Confirm.ask() — used by WebSocket bridge.
    flush_fn : Callable | None
        Called after every display block to push buffered output
        through the WebSocket. No-op for CLI mode.
    """
    _flush = flush_fn or (lambda: None)

    rng = random.Random(config.seed)
    repo = GameRepository()
    repo.initialize()
    risk_agent = create_risk_agent("rules")

    # Phase 2 layers
    narrative_layer = GameNarrativeLayer()
    competition_layer = GameCompetitionLayer("momentum")

    # Initialize game state
    initial_macro = MacroState(
        regime=INITIAL_REGIME,
        volatility_state=INITIAL_VOL_STATE,
        rate_direction=INITIAL_RATE_DIR,
        week=0,
    )
    portfolio = PortfolioState(
        cash=config.starting_cash,
        holdings=Holdings(positions={s: 0.0 for s in Sector}),
        total_value=config.starting_cash,
        week=0,
    )
    game_state = GameState(
        config=config,
        macro_state=initial_macro,
        portfolio=portfolio,
        weekly_values=[config.starting_cash],
    )
    repo.save_game(game_state)

    # Load or create career profile
    career = repo.load_career(config.player_name)
    if career is None:
        career = create_new_career(config.player_name)

    display_intro(game_state, con=con)
    display_career_status(career, con=con)
    _flush()

    # Track allocations for expanded analytics
    weekly_allocations: list[Allocation] = []

    try:
        # Weekly game loop
        for week in range(1, config.total_weeks + 1):
            game_state.current_week = week

            # Advance macro state
            new_macro = advance_macro_state(game_state.macro_state, rng)
            new_macro = MacroState(
                regime=new_macro.regime,
                volatility_state=new_macro.volatility_state,
                rate_direction=new_macro.rate_direction,
                week=week,
            )
            game_state.macro_state = new_macro

            # Generate events
            events = generate_weekly_events(new_macro, rng)

            # Display state to player
            display_week_header(week, config.total_weeks, con=con)

            # Phase 2: Headlines before macro state
            narrative = narrative_layer.generate_weekly_narrative(
                new_macro, events,
                _equal_allocation(),
                game_state, rng,
            )
            display_headlines(narrative.headlines, con=con)
            display_macro_state(new_macro, con=con)

            # Phase 2: Fed statement after macro state
            display_fed_statement(narrative.fed_statement, con=con)

            display_events(events, con=con)
            display_portfolio(game_state.portfolio, config.starting_cash, con=con)
            _flush()

            # Get allocation from player
            allocation = prompt_allocation(input_fn=input_fn, print_fn=con.print if con else None)

            # Risk committee evaluation
            risk = risk_agent.evaluate(
                allocation, new_macro, game_state.portfolio, game_state
            )
            display_risk_assessment(risk, con=con)
            _flush()

            # Option to revise after high-risk warning
            if risk.risk_score >= 7:
                if prompt_revise_allocation(confirm_fn=confirm_fn):
                    allocation = prompt_allocation(input_fn=input_fn, print_fn=con.print if con else None)
                    # Re-evaluate with new allocation
                    risk = risk_agent.evaluate(
                        allocation, new_macro, game_state.portfolio, game_state
                    )
                    display_risk_assessment(risk, con=con)
                    _flush()

            # Phase 2: Short seller analysis on actual allocation
            short_thesis = narrative_layer.short_seller.analyze(
                allocation, new_macro, game_state, rng
            )
            display_short_thesis(short_thesis, con=con)
            _flush()

            weekly_allocations.append(allocation)

            # Generate returns and apply events
            base_returns = generate_sector_returns(new_macro, rng)
            adjusted = apply_events(base_returns, events)

            # Calculate portfolio return
            fracs = allocation.as_fractions
            portfolio_return = sum(
                fracs[s] * adjusted[s] for s in Sector
            )

            # Update portfolio (floor at 0 — leverage wipeout)
            value_before = game_state.portfolio.total_value
            new_value = max(0.0, value_before * (1 + portfolio_return))
            new_cash = new_value * allocation.cash_weight
            new_holdings = Holdings(
                positions={s: new_value * fracs[s] for s in Sector}
            )
            game_state.portfolio = PortfolioState(
                cash=new_cash,
                holdings=new_holdings,
                total_value=new_value,
                week=week,
            )
            game_state.weekly_values.append(new_value)

            # Build week result
            week_result = WeekResult(
                week=week,
                macro_state=new_macro,
                allocation=allocation,
                sector_returns=SectorReturns(returns=base_returns),
                events=events,
                adjusted_returns=SectorReturns(returns=adjusted),
                portfolio_return=portfolio_return,
                portfolio_value_before=value_before,
                portfolio_value_after=new_value,
            )
            game_state.history.append(week_result)

            # Phase 2: Rival PM processes the same week
            rival_result = competition_layer.process_week(
                new_macro, adjusted, game_state, rng
            )

            # Persist
            repo.save_week(game_state.game_id, week_result, risk)
            repo.save_rival_week(game_state.game_id, week, rival_result)
            repo.save_game(game_state)

            # Display results
            display_week_results(week_result, con=con)

            # Phase 2: Rival comparison
            display_rival_comparison(
                portfolio_return, new_value, rival_result, con=con
            )
            _flush()

        # Game complete
        game_state.is_complete = True
        scorecard = compute_scorecard(game_state.weekly_values)
        repo.save_scorecard(game_state.game_id, scorecard)
        repo.save_game(game_state)
        display_final_scorecard(scorecard, con=con)

        # Phase 2: Expanded analytics
        weekly_returns = []
        for i in range(1, len(game_state.weekly_values)):
            prev = game_state.weekly_values[i - 1]
            curr = game_state.weekly_values[i]
            weekly_returns.append((curr - prev) / prev if prev > 0 else 0.0)

        if weekly_returns:
            expanded = compute_expanded_metrics(
                game_state.weekly_values, weekly_returns, weekly_allocations
            )
            display_expanded_analytics(expanded, con=con)

        # Phase 2: Career progression
        career = update_career_after_season(career, scorecard)
        repo.save_career(career)
        display_career_status(career, con=con)
        _flush()

    except KeyboardInterrupt:
        repo.save_game(game_state)
        c = con or Console()
        c.print("\n[yellow]Game paused. Progress saved.[/yellow]")
        _flush()

    finally:
        repo.close()


def _equal_allocation() -> Allocation:
    """Return a balanced 20% each allocation for narrative pre-generation."""
    return Allocation(weights={s: 20.0 for s in Sector})
