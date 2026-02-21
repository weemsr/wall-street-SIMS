"""Tests for event engine: event generation and selection."""

import random

import pytest

from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.market import MacroState
from wallstreet.event_engine.generator import generate_weekly_events


class TestEventGeneration:
    def test_event_count_range(self, sample_macro_bull: MacroState) -> None:
        """Always 0-2 events per week."""
        for seed in range(200):
            rng = random.Random(seed)
            events = generate_weekly_events(sample_macro_bull, rng)
            assert 0 <= len(events) <= 2

    def test_reproducible(self, sample_macro_bull: MacroState) -> None:
        """Same seed produces same events."""
        rng1 = random.Random(42)
        events1 = generate_weekly_events(sample_macro_bull, rng1)

        rng2 = random.Random(42)
        events2 = generate_weekly_events(sample_macro_bull, rng2)

        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1.template_name == e2.template_name

    def test_no_duplicates(self, sample_macro_bull: MacroState) -> None:
        """No duplicate event names in same week."""
        for seed in range(200):
            rng = random.Random(seed)
            events = generate_weekly_events(sample_macro_bull, rng)
            names = [e.template_name for e in events]
            assert len(names) == len(set(names))

    def test_events_have_sector_effects(self, sample_macro_bull: MacroState) -> None:
        """All generated events have sector effects."""
        rng = random.Random(42)
        events = generate_weekly_events(sample_macro_bull, rng)
        for event in events:
            assert len(event.sector_effects) > 0

    def test_crisis_produces_more_events(self) -> None:
        """Higher volatility should average more events."""
        low_vol = MacroState(
            regime=Regime.BULL,
            volatility_state=VolatilityState.LOW,
            rate_direction=RateDirection.STABLE,
            week=1,
        )
        crisis_vol = MacroState(
            regime=Regime.RECESSION,
            volatility_state=VolatilityState.CRISIS,
            rate_direction=RateDirection.FALLING,
            week=1,
        )
        low_total = 0
        crisis_total = 0
        n = 500
        for seed in range(n):
            rng_low = random.Random(seed)
            rng_crisis = random.Random(seed + 10000)
            low_total += len(generate_weekly_events(low_vol, rng_low))
            crisis_total += len(generate_weekly_events(crisis_vol, rng_crisis))

        # Crisis should average significantly more events
        assert crisis_total / n > low_total / n
