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
    Sector.CONSUMER, Sector.INDUSTRIALS,
]


def prompt_allocation(
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[..., None] | None = None,
) -> Allocation:
    """Prompt user for sector allocation percentages.

    Accepts space-separated values in sector order:
      Tech Energy Financials Consumer Industrials

    Validates sum 0-100%. Remainder held as cash (earns 0%). Retries on error.
    """
    _input = input_fn or console.input
    _print = print_fn or console.print

    sector_names = " ".join(s.value for s in SECTOR_ORDER)
    _print(f"[bold]Enter allocation (% for each sector, 0-100% total):[/bold]")
    _print(f"[dim]  Order: {sector_names}[/dim]")
    _print(f"[dim]  Example: 20 20 20 20 20  (fully invested)[/dim]")
    _print(f"[dim]          10 10 10 10 10  (50% invested, 50% cash)[/dim]")
    _print(f"[dim]  Negative = short (e.g. 40 30 20 30 -20). Max short: -50% per sector.[/dim]")
    _print(f"[dim]  Gross exposure (sum of |weights|) capped at 200%.[/dim]")

    while True:
        try:
            raw = _input("[bold cyan]> [/bold cyan]").strip()
            if not raw:
                _print("[red]Please enter 5 space-separated numbers.[/red]")
                continue

            parts = raw.split()
            if len(parts) != 5:
                _print(
                    f"[red]Expected 5 values, got {len(parts)}. "
                    f"Enter percentages for: {sector_names}[/red]"
                )
                continue

            values = [float(p) for p in parts]
            weights = dict(zip(SECTOR_ORDER, values))
            allocation = Allocation(weights=weights)
            return allocation

        except ValueError as e:
            error_msg = str(e)
            if "could not convert" in error_msg.lower() or "invalid literal" in error_msg.lower():
                _print("[red]Invalid number. Enter numeric values only.[/red]")
            else:
                _print(f"[red]{error_msg}[/red]")


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
