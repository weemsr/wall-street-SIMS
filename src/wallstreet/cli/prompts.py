"""User input handling and validation for the CLI."""

from __future__ import annotations

from collections.abc import Callable

from rich.console import Console
from rich.prompt import Confirm

from wallstreet.models.enums import Sector
from wallstreet.models.portfolio import Allocation

console = Console()

SECTOR_ORDER: list[Sector] = [
    Sector.TECH, Sector.ENERGY, Sector.FINANCIALS,
    Sector.CONSUMER, Sector.CONSUMER_DISC, Sector.INDUSTRIALS,
    Sector.HEALTHCARE,
]

SHORT_NAMES: dict[Sector, str] = {
    Sector.TECH: "Tech",
    Sector.ENERGY: "Energy",
    Sector.FINANCIALS: "Financials",
    Sector.CONSUMER: "Con Staples",
    Sector.CONSUMER_DISC: "Con Disc",
    Sector.INDUSTRIALS: "Industrials",
    Sector.HEALTHCARE: "Healthcare",
}


def prompt_allocation(
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[..., None] | None = None,
) -> Allocation:
    """Prompt user for sector allocation percentages one sector at a time.

    Features:
    - Sector-by-sector entry with running total and remaining budget
    - Auto-complete suggestion for the last sector
    - Type 'b' to go back one sector, 'r' to reset all
    - Summary confirmation before submitting
    """
    _input = input_fn or console.input
    _print = print_fn or console.print

    n = len(SECTOR_ORDER)
    max_label = max(len(SHORT_NAMES[s]) for s in SECTOR_ORDER)

    while True:
        _print("[bold]Enter allocation (% for each sector, 0-100% total):[/bold]")
        _print("[dim]  Negative = short. Max short: -50%/sector. Gross cap: 200%.[/dim]")
        _print("[dim]  Type 'b' to go back, 'r' to reset.[/dim]")

        values: list[float] = [0.0] * n
        i = 0

        while i < n:
            sector = SECTOR_ORDER[i]
            label = SHORT_NAMES[sector].ljust(max_label)
            current_sum = sum(values[:i])
            remaining = 100.0 - current_sum

            # Build the prompt string
            if i == n - 1:
                # Last sector: show auto-complete suggestion
                suggestion = remaining
                prompt = (
                    f"[bold cyan]  [{i+1}/{n}] {label} : [/bold cyan]"
                    f"[dim](Enter={suggestion:g}) [/dim]"
                )
            else:
                prompt = f"[bold cyan]  [{i+1}/{n}] {label} : [/bold cyan]"

            raw = _input(prompt).strip()

            # Navigation commands
            if raw.lower() in ("b", "back"):
                if i > 0:
                    i -= 1
                continue
            if raw.lower() in ("r", "reset"):
                values = [0.0] * n
                i = 0
                _print("[yellow]  Reset — starting over.[/yellow]")
                continue

            # Auto-complete on last sector if empty
            if raw == "" and i == n - 1:
                values[i] = remaining
            elif raw == "":
                _print("[red]  Enter a number.[/red]")
                continue
            else:
                try:
                    values[i] = float(raw)
                except ValueError:
                    _print("[red]  Invalid number. Try again.[/red]")
                    continue

            # Show portfolio breakdown after entry
            entered = values[: i + 1]
            longs = sum(v for v in entered if v > 0)
            shorts = sum(abs(v) for v in entered if v < 0)
            net = sum(entered)
            cash = 100.0 - net
            has_shorts = any(v < 0 for v in entered)

            status_parts: list[str] = [f"[green]Longs: {longs:g}%[/green]"]
            if has_shorts:
                status_parts.append(f"[red]Shorts: {shorts:g}%[/red]")
            if cash >= 0:
                status_parts.append(f"[dim]Cash: {cash:g}%[/dim]")
            else:
                status_parts.append(f"[red]Cash: {cash:g}%[/red]")
            if has_shorts:
                gross = longs + shorts
                status_parts.append(f"[dim]Gross: {gross:g}%/200%[/dim]")

            _print(f"         {'  '.join(status_parts)}")

            i += 1

        # Show summary
        longs_total = sum(v for v in values if v > 0)
        shorts_total = sum(abs(v) for v in values if v < 0)
        net_total = sum(values)
        cash_total = 100.0 - net_total
        any_shorts = any(v < 0 for v in values)

        _print()
        _print("[bold]Allocation Summary:[/bold]")
        summary_parts = []
        for idx, sector in enumerate(SECTOR_ORDER):
            summary_parts.append(f"{SHORT_NAMES[sector]}: {values[idx]:g}%")
        _print(f"  {' | '.join(summary_parts)}")

        breakdown = [f"[green]Longs: {longs_total:g}%[/green]"]
        if any_shorts:
            breakdown.append(f"[red]Shorts: {shorts_total:g}%[/red]")
        if cash_total >= 0:
            breakdown.append(f"Cash: {cash_total:g}%")
        else:
            breakdown.append(f"[red]Cash: {cash_total:g}%[/red]")
        if any_shorts:
            gross_total = longs_total + shorts_total
            breakdown.append(f"Gross: {gross_total:g}%/200%")
        _print(f"  {'  '.join(breakdown)}")

        # Try to create and validate the allocation
        weights = dict(zip(SECTOR_ORDER, values))
        try:
            allocation = Allocation(weights=weights)
        except ValueError as e:
            _print(f"[red]{e}[/red]")
            _print("[yellow]Please re-enter your allocation.[/yellow]")
            continue

        # Confirm
        answer = _input("[bold cyan]  Confirm? (Enter=yes, e=edit) [/bold cyan]").strip().lower()
        if answer in ("e", "edit"):
            continue

        return allocation


def prompt_revise_allocation(
    confirm_fn: Callable[[str], bool] | None = None,
) -> bool:
    """Ask if the player wants to revise their allocation after a risk warning."""
    if confirm_fn is not None:
        return confirm_fn(
            "[yellow]The Risk Committee flagged significant concerns. "
            "Revise your allocation?[/yellow]"
        )
    return Confirm.ask(
        "[yellow]The Risk Committee flagged significant concerns. "
        "Revise your allocation?[/yellow]"
    )
