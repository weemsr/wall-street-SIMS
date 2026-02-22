"""Rich-based terminal rendering for the game UI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from wallstreet.agents.base import RiskAssessment
from wallstreet.models.analytics import ExpandedMetrics
from wallstreet.models.career import CareerProfile
from wallstreet.models.enums import Regime, Sector, VolatilityState
from wallstreet.models.events import ShockEvent
from wallstreet.models.game import GameState, WeekResult
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import (
    FedStatement,
    Headline,
    RivalWeekResult,
    ShortThesis,
)
from wallstreet.models.portfolio import PortfolioState
from wallstreet.models.scoring import ScoreCard

console = Console()

REGIME_COLORS: dict[Regime, str] = {
    Regime.BULL: "green",
    Regime.BEAR: "red",
    Regime.RECESSION: "bright_red",
    Regime.RECOVERY: "yellow",
}

VOL_INDICATORS: dict[VolatilityState, str] = {
    VolatilityState.LOW: "Calm",
    VolatilityState.NORMAL: "Normal",
    VolatilityState.HIGH: "Elevated",
    VolatilityState.CRISIS: "STORM",
}


def display_intro(game_state: GameState, con: Console | None = None) -> None:
    """Show game introduction screen."""
    c = con or console
    banner = Text()
    banner.append("WALL STREET WAR ROOM\n", style="bold white")
    banner.append("Portfolio Management Roguelike\n\n", style="dim")
    banner.append(f"Player: {game_state.config.player_name}\n")
    banner.append(f"Starting Capital: ${game_state.config.starting_cash:,.0f}\n")
    banner.append(f"Season Length: {game_state.config.total_weeks} months\n")
    banner.append(f"Seed: {game_state.config.seed}\n")

    c.print(Panel(banner, title="[bold]NEW GAME[/bold]", border_style="blue"))
    c.print()


def display_week_header(week: int, total_weeks: int, con: Console | None = None) -> None:
    """Show month divider."""
    c = con or console
    c.print()
    c.print(Rule(f"[bold] MONTH {week} of {total_weeks} [/bold]"))
    c.print()


def display_macro_state(macro: MacroState, con: Console | None = None) -> None:
    """Show current macro environment."""
    c = con or console
    table = Table(title="Macro Environment", show_header=True)
    table.add_column("Indicator", style="bold")
    table.add_column("Status")

    regime_color = REGIME_COLORS[macro.regime]
    table.add_row("Regime", f"[{regime_color}]{macro.regime.value.upper()}[/{regime_color}]")
    table.add_row("Interest Rates", macro.rate_direction.value.capitalize())

    vol_label = VOL_INDICATORS[macro.volatility_state]
    vol_color = "green" if macro.volatility_state == VolatilityState.LOW else (
        "white" if macro.volatility_state == VolatilityState.NORMAL else (
            "yellow" if macro.volatility_state == VolatilityState.HIGH else "red"
        )
    )
    table.add_row("Volatility", f"[{vol_color}]{vol_label}[/{vol_color}]")

    c.print(table)
    c.print(f"  [dim]{macro.description}[/dim]")
    c.print()


def display_events(events: list[ShockEvent], con: Console | None = None) -> None:
    """Show weekly shock events."""
    c = con or console
    if not events:
        c.print("[dim]No major events this month.[/dim]")
        c.print()
        return

    for event in events:
        effects_parts: list[str] = []
        for sector, effect in event.sector_effects.items():
            if abs(effect) < 0.001:
                continue
            color = "green" if effect > 0 else "red"
            sign = "+" if effect > 0 else ""
            effects_parts.append(
                f"[{color}]{sector.value}: {sign}{effect * 100:.1f}%[/{color}]"
            )

        body = f"{event.description}\n\n{' | '.join(effects_parts)}"
        style = "red" if any(e < -0.03 for e in event.sector_effects.values()) else (
            "green" if any(e > 0.03 for e in event.sector_effects.values()) else "yellow"
        )
        c.print(Panel(body, title=f"[bold]{event.template_name}[/bold]", border_style=style))

    c.print()


def display_portfolio(
    portfolio: PortfolioState,
    initial_value: float = 1_000_000.0,
    con: Console | None = None,
) -> None:
    """Show current portfolio status."""
    c = con or console
    table = Table(title="Portfolio Status")
    table.add_column("Sector", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Weight", justify="right")

    for sector in Sector:
        value = portfolio.holdings.positions.get(sector, 0.0)
        weight = (value / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0
        label = sector.value
        if value < 0:
            label += " [red](SHORT)[/red]"
        table.add_row(label, f"${value:,.0f}", f"{weight:.1f}%")

    if portfolio.cash > 0.01:
        cash_pct = (portfolio.cash / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0
        table.add_row("[dim]Cash[/dim]", f"[dim]${portfolio.cash:,.0f}[/dim]", f"[dim]{cash_pct:.1f}%[/dim]")

    table.add_section()
    pnl = portfolio.total_value - initial_value
    pnl_pct = (pnl / initial_value) * 100 if initial_value > 0 else 0
    pnl_color = "green" if pnl >= 0 else "red"
    sign = "+" if pnl >= 0 else ""

    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]${portfolio.total_value:,.0f}[/bold]",
        f"[{pnl_color}]{sign}{pnl_pct:.1f}%[/{pnl_color}]",
    )
    c.print(table)
    c.print()


def display_risk_assessment(risk: RiskAssessment, con: Console | None = None) -> None:
    """Show risk committee evaluation."""
    c = con or console
    if risk.risk_score <= 3:
        color = "green"
    elif risk.risk_score <= 6:
        color = "yellow"
    else:
        color = "red"

    score_bar = "#" * risk.risk_score + "." * (10 - risk.risk_score)
    body = f"Risk Score: [{color}][{score_bar}] {risk.risk_score}/10[/{color}]\n\n"
    body += risk.critique

    c.print(
        Panel(body, title="[bold]Risk Committee[/bold]", border_style=color)
    )
    c.print()


def display_week_results(week_result: WeekResult, con: Console | None = None) -> None:
    """Show results after a week of play."""
    c = con or console
    table = Table(title=f"Month {week_result.week} Results")
    table.add_column("Sector", style="bold")
    table.add_column("Return", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Contribution", justify="right")

    fracs = week_result.allocation.as_fractions
    for sector in Sector:
        ret = week_result.adjusted_returns.returns[sector]
        weight = fracs[sector]
        contrib = ret * weight
        ret_color = "green" if ret >= 0 else "red"
        contrib_color = "green" if contrib >= 0 else "red"
        sign_r = "+" if ret >= 0 else ""
        sign_c = "+" if contrib >= 0 else ""
        weight_label = f"{weight * 100:.0f}%"
        if weight < 0:
            weight_label += " [red](S)[/red]"

        table.add_row(
            sector.value,
            f"[{ret_color}]{sign_r}{ret * 100:.2f}%[/{ret_color}]",
            weight_label,
            f"[{contrib_color}]{sign_c}{contrib * 100:.2f}%[/{contrib_color}]",
        )

    cash_w = week_result.allocation.cash_weight
    if cash_w > 0.001:
        table.add_row(
            "[dim]Cash[/dim]",
            "[dim]+0.00%[/dim]",
            f"[dim]{cash_w * 100:.0f}%[/dim]",
            "[dim]+0.00%[/dim]",
        )

    table.add_section()
    port_ret = week_result.portfolio_return
    port_color = "green" if port_ret >= 0 else "red"
    port_sign = "+" if port_ret >= 0 else ""
    table.add_row(
        "[bold]Portfolio[/bold]",
        f"[bold {port_color}]{port_sign}{port_ret * 100:.2f}%[/bold {port_color}]",
        "",
        "",
    )

    c.print(table)

    value_change = week_result.portfolio_value_after - week_result.portfolio_value_before
    v_color = "green" if value_change >= 0 else "red"
    v_sign = "+" if value_change >= 0 else ""
    c.print(
        f"  Portfolio: ${week_result.portfolio_value_before:,.0f} -> "
        f"[{v_color}]${week_result.portfolio_value_after:,.0f} "
        f"({v_sign}${value_change:,.0f})[/{v_color}]"
    )
    c.print()


def display_final_scorecard(scorecard: ScoreCard, con: Console | None = None) -> None:
    """Show final game scorecard."""
    c = con or console
    c.print()
    c.print(Rule("[bold] FINAL SCORECARD [/bold]"))
    c.print()

    table = Table(show_header=False, title="Performance Summary")
    table.add_column("Metric", style="bold", width=25)
    table.add_column("Value", justify="right")

    table.add_row("Initial Value", f"${scorecard.initial_value:,.0f}")
    table.add_row("Final Value", f"${scorecard.final_value:,.0f}")

    ret_color = "green" if scorecard.total_return_pct >= 0 else "red"
    sign = "+" if scorecard.total_return_pct >= 0 else ""
    table.add_row(
        "Total Return",
        f"[{ret_color}]{sign}{scorecard.total_return_pct:.2f}%[/{ret_color}]",
    )

    cagr_color = "green" if scorecard.cagr >= 0 else "red"
    cagr_sign = "+" if scorecard.cagr >= 0 else ""
    table.add_row(
        "CAGR (annualized)",
        f"[{cagr_color}]{cagr_sign}{scorecard.cagr * 100:.2f}%[/{cagr_color}]",
    )

    table.add_row(
        "Max Drawdown",
        f"[red]{scorecard.max_drawdown * 100:.2f}%[/red]",
    )
    table.add_row(
        "Annualized Volatility",
        f"{scorecard.annualized_volatility * 100:.2f}%",
    )

    sharpe_color = "green" if scorecard.sharpe_ratio >= 1.0 else (
        "yellow" if scorecard.sharpe_ratio >= 0 else "red"
    )
    table.add_row(
        "Sharpe Ratio",
        f"[{sharpe_color}]{scorecard.sharpe_ratio:.3f}[/{sharpe_color}]",
    )
    table.add_row("Season Length", f"{scorecard.total_weeks} months")

    c.print(table)
    c.print()

    # Letter grade
    grade = scorecard.letter_grade
    grade_color = {
        "A+": "bold green", "A": "green", "B": "cyan",
        "C": "yellow", "D": "bright_red", "F": "bold red",
    }.get(grade, "white")

    c.print(
        Panel(
            f"[{grade_color}]  {grade}  [/{grade_color}]",
            title="[bold]Final Grade[/bold]",
            border_style="blue",
        )
    )
    c.print()


def display_game_list(games: list[dict], con: Console | None = None) -> None:
    """Display list of saved games."""
    c = con or console
    if not games:
        c.print("[dim]No saved games found.[/dim]")
        return

    table = Table(title="Saved Games")
    table.add_column("Game ID", style="bold")
    table.add_column("Player")
    table.add_column("Months")
    table.add_column("Status")
    table.add_column("Final Value", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Created")

    for g in games:
        status = "Complete" if g["is_complete"] else f"Month {g['current_week']}/{g['total_weeks']}"
        final_val = f"${g['final_value']:,.0f}" if g["final_value"] else "-"
        sharpe = f"{g['sharpe_ratio']:.3f}" if g["sharpe_ratio"] is not None else "-"
        table.add_row(
            g["game_id"],
            g["player_name"],
            str(g["total_weeks"]),
            status,
            final_val,
            sharpe,
            g["created_at"][:19],
        )

    c.print(table)


# ── Phase 2 Display Functions ──────────────────────────────────────────


def display_headlines(headlines: list[Headline], con: Console | None = None) -> None:
    """Display weekly news headlines as a styled ticker."""
    c = con or console
    if not headlines:
        return

    body_parts: list[str] = []
    for hl in headlines:
        sentiment_icon = {
            "bullish": "[green]+[/green]",
            "bearish": "[red]-[/red]",
            "mixed": "[yellow]~[/yellow]",
        }.get(hl.sentiment, "~")
        body_parts.append(f"  {sentiment_icon} {hl.text}")

    body = "\n".join(body_parts)
    c.print(Panel(body, title="[bold]MARKET HEADLINES[/bold]", border_style="cyan"))
    c.print()


def display_fed_statement(fed: FedStatement, con: Console | None = None) -> None:
    """Display the weekly Fed Chair policy statement."""
    c = con or console
    bias_style = {
        "tightening": "[red]TIGHTENING[/red]",
        "easing": "[green]EASING[/green]",
        "neutral": "[yellow]NEUTRAL[/yellow]",
    }.get(fed.policy_bias, fed.policy_bias)

    conf_bar_len = int(fed.confidence_level * 10)
    conf_bar = "#" * conf_bar_len + "." * (10 - conf_bar_len)
    conf_pct = fed.confidence_level * 100

    body = f"{fed.statement}\n\n"
    body += f"Policy Bias: {bias_style}  |  "
    body += f"Confidence: [{conf_bar}] {conf_pct:.0f}%"

    c.print(
        Panel(body, title="[bold]FEDERAL RESERVE STATEMENT[/bold]", border_style="blue")
    )
    c.print()


def display_short_thesis(thesis: ShortThesis | None, con: Console | None = None) -> None:
    """Display the short seller's attack, if any."""
    c = con or console
    if thesis is None:
        return

    conv_bar_len = int(thesis.conviction * 10)
    conv_bar = "#" * conv_bar_len + "." * (10 - conv_bar_len)
    conv_pct = thesis.conviction * 100

    body = f"[bold]Target: {thesis.target_sector.value}[/bold]\n\n"
    body += f"{thesis.critique}\n\n"
    body += f"Conviction: [{conv_bar}] {conv_pct:.0f}%"

    c.print(
        Panel(body, title="[bold red]SHORT SELLER ALERT[/bold red]", border_style="red")
    )
    c.print()


def display_rival_comparison(
    player_return: float,
    player_value: float,
    rival_result: RivalWeekResult,
    con: Console | None = None,
) -> None:
    """Display side-by-side comparison of player vs rival PM."""
    c = con or console
    table = Table(title=f"vs {rival_result.rival_name} ({rival_result.strategy_type})")
    table.add_column("", style="bold")
    table.add_column("You", justify="right")
    table.add_column(rival_result.rival_name, justify="right")

    # Weekly return
    p_color = "green" if player_return >= 0 else "red"
    p_sign = "+" if player_return >= 0 else ""
    r_color = "green" if rival_result.portfolio_return >= 0 else "red"
    r_sign = "+" if rival_result.portfolio_return >= 0 else ""
    table.add_row(
        "Monthly Return",
        f"[{p_color}]{p_sign}{player_return * 100:.2f}%[/{p_color}]",
        f"[{r_color}]{r_sign}{rival_result.portfolio_return * 100:.2f}%[/{r_color}]",
    )

    # Portfolio value
    table.add_row(
        "Portfolio Value",
        f"${player_value:,.0f}",
        f"${rival_result.portfolio_value:,.0f}",
    )

    # Who's winning
    if player_value > rival_result.portfolio_value:
        lead = player_value - rival_result.portfolio_value
        table.add_row("Leader", f"[green]+${lead:,.0f}[/green]", "")
    elif rival_result.portfolio_value > player_value:
        lead = rival_result.portfolio_value - player_value
        table.add_row("Leader", "", f"[red]+${lead:,.0f}[/red]")
    else:
        table.add_row("Leader", "[yellow]TIE[/yellow]", "[yellow]TIE[/yellow]")

    c.print(table)
    c.print()


def display_career_status(profile: CareerProfile, con: Console | None = None) -> None:
    """Display career title and lifetime stats."""
    c = con or console
    title_colors = {
        "Retail Speculator": "dim",
        "Junior PM": "cyan",
        "Macro Operator": "yellow",
        "Institutional Strategist": "green",
        "Legendary Allocator": "bold magenta",
    }
    color = title_colors.get(profile.title.value, "white")

    table = Table(show_header=False, title="Career Profile")
    table.add_column("Stat", style="bold", width=20)
    table.add_column("Value", justify="right")

    table.add_row("Title", f"[{color}]{profile.title.value}[/{color}]")
    table.add_row("Seasons Played", str(profile.seasons_played))

    cagr_color = "green" if profile.lifetime_cagr > 0 else "red"
    table.add_row(
        "Lifetime CAGR",
        f"[{cagr_color}]{profile.lifetime_cagr * 100:.2f}%[/{cagr_color}]",
    )
    table.add_row("Best Sharpe", f"{profile.best_sharpe:.3f}")
    table.add_row("Worst Drawdown", f"{profile.worst_drawdown * 100:.2f}%")

    pnl_color = "green" if profile.total_pnl >= 0 else "red"
    pnl_sign = "+" if profile.total_pnl >= 0 else ""
    table.add_row(
        "Total P&L",
        f"[{pnl_color}]{pnl_sign}${profile.total_pnl:,.0f}[/{pnl_color}]",
    )

    c.print(table)
    c.print()


def display_expanded_analytics(metrics: ExpandedMetrics, con: Console | None = None) -> None:
    """Display rolling metrics summary."""
    c = con or console
    table = Table(title="Expanded Analytics")
    table.add_column("Metric", style="bold")
    table.add_column("Current", justify="right")

    table.add_row(
        "Rolling Volatility (4m ann.)",
        f"{metrics.current_rolling_vol * 100:.2f}%",
    )

    sharpe_color = "green" if metrics.current_rolling_sharpe >= 0 else "red"
    table.add_row(
        "Rolling Sharpe (4m ann.)",
        f"[{sharpe_color}]{metrics.current_rolling_sharpe:.3f}[/{sharpe_color}]",
    )

    dd_color = "red" if metrics.current_drawdown < -0.05 else (
        "yellow" if metrics.current_drawdown < 0 else "green"
    )
    table.add_row(
        "Current Drawdown",
        f"[{dd_color}]{metrics.current_drawdown * 100:.2f}%[/{dd_color}]",
    )

    # Concentration: HHI. 0.20 = perfectly balanced, 1.0 = fully concentrated
    conc_color = "green" if metrics.current_concentration < 0.25 else (
        "yellow" if metrics.current_concentration < 0.35 else "red"
    )
    table.add_row(
        "Concentration (HHI)",
        f"[{conc_color}]{metrics.current_concentration:.3f}[/{conc_color}]",
    )

    # Gross exposure: 1.0 = long only, >1.0 = leveraged
    ge = metrics.current_gross_exposure
    ge_color = "green" if ge <= 1.01 else (
        "yellow" if ge <= 1.50 else "red"
    )
    table.add_row(
        "Gross Exposure",
        f"[{ge_color}]{ge * 100:.0f}%[/{ge_color}]",
    )

    c.print(table)
    c.print()
