"""Weekly shock event generation."""

import random

from wallstreet.event_engine.catalog import EVENT_CATALOG
from wallstreet.models.enums import VolatilityState
from wallstreet.models.events import ShockEvent, ShockEventTemplate
from wallstreet.models.market import MacroState

# Probability of [0, 1, 2] events per week, by volatility state
EVENT_COUNT_WEIGHTS: dict[VolatilityState, list[float]] = {
    VolatilityState.LOW:    [0.60, 0.30, 0.10],
    VolatilityState.NORMAL: [0.45, 0.40, 0.15],
    VolatilityState.HIGH:   [0.25, 0.45, 0.30],
    VolatilityState.CRISIS: [0.10, 0.40, 0.50],
}


def generate_weekly_events(
    macro_state: MacroState,
    rng: random.Random,
    catalog: list[ShockEventTemplate] | None = None,
) -> list[ShockEvent]:
    """Select 0-2 shock events for this week.

    Event count is weighted by volatility state.
    Event selection is weighted by regime affinity.
    Duplicate events in the same week are removed.
    """
    if catalog is None:
        catalog = EVENT_CATALOG

    weights = EVENT_COUNT_WEIGHTS[macro_state.volatility_state]
    num_events = rng.choices([0, 1, 2], weights=weights, k=1)[0]

    if num_events == 0:
        return []

    regime = macro_state.regime
    event_weights = [tmpl.regime_weights[regime] for tmpl in catalog]

    selected = rng.choices(catalog, weights=event_weights, k=num_events)

    # Deduplicate
    seen: set[str] = set()
    unique: list[ShockEventTemplate] = []
    for tmpl in selected:
        if tmpl.name not in seen:
            seen.add(tmpl.name)
            unique.append(tmpl)

    return [
        ShockEvent(
            template_name=tmpl.name,
            description=tmpl.description,
            sector_effects=tmpl.sector_effects,
            vol_impact=tmpl.vol_impact,
            week=macro_state.week,
        )
        for tmpl in unique
    ]
