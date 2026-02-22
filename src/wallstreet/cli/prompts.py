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

            # Show running total after entry
            running_sum = sum(values[: i + 1])
            rem_after = 100.0 - running_sum
            if running_sum <= 100:
                color = "green"
            elif running_sum <= 200:
                color = "yellow"
            else:
                color = "red"
            _print(
                f"[{color}]         Total: {running_sum:g}%[/{color}]"
                f"  [dim]Remaining: {rem_after:g}%[/dim]"
            )

            i += 1

        # Show summary
        total = sum(values)
        cash = max(0.0, 100.0 - total)
        _print()
        _print("[bold]Allocation Summary:[/bold]")
        parts = []
        for idx, sector in enumerate(SECTOR_ORDER):
            parts.append(f"{SHORT_NAMES[sector]}: {values[idx]:g}%")
        _print(f"  {' | '.join(parts)}")
        total_color = "green" if total <= 100 else "yellow"
        _print(
            f"  [{total_color}]Total invested: {total:g}%[/{total_color}]"
            f"  [dim]Cash: {cash:g}%[/dim]"
        )

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
