"""Headline Engine — generates Bloomberg/WSJ-style weekly headlines."""

import random

from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.events import ShockEvent
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import Headline

# ── Regime-based headline pools ────────────────────────────────────────

_REGIME_HEADLINES: dict[Regime, list[tuple[str, str]]] = {
    Regime.BULL: [
        ("Markets Rally as Economic Expansion Continues Into New Quarter", "bullish"),
        ("S&P 500 Notches Another Record Close on Strong Earnings Season", "bullish"),
        ("Wall Street Sees Further Upside as Growth Indicators Improve", "bullish"),
        ("Investor Confidence Surges as GDP Beats Expectations", "bullish"),
        ("Bull Run Extends as Corporate Profits Exceed Forecasts", "bullish"),
        ("Risk Appetite Returns as Markets Hit New Highs", "bullish"),
        ("Fund Managers Increase Equity Exposure Amid Bullish Outlook", "bullish"),
        ("Merger Activity Surges as Boardrooms Turn Optimistic", "bullish"),
    ],
    Regime.BEAR: [
        ("Markets Slide as Economic Outlook Darkens", "bearish"),
        ("Investors Brace for Prolonged Downturn as Indicators Weaken", "bearish"),
        ("Bear Market Deepens: Major Indices Post Third Consecutive Weekly Loss", "bearish"),
        ("Selling Pressure Intensifies as Growth Fears Grip Wall Street", "bearish"),
        ("Flight to Safety: Investors Dump Equities for Bonds", "bearish"),
        ("Market Strategists Slash Year-End Targets Amid Deterioration", "bearish"),
        ("Corporate Earnings Warnings Pile Up as Demand Softens", "bearish"),
        ("Wall Street Braces for More Pain as Recession Fears Mount", "bearish"),
    ],
    Regime.RECESSION: [
        ("Economy Officially in Contraction: GDP Shrinks for Second Quarter", "bearish"),
        ("Unemployment Claims Surge to Multi-Year Highs", "bearish"),
        ("Markets in Freefall as Recession Deepens", "bearish"),
        ("Corporate Defaults Rise Sharply as Credit Conditions Tighten", "bearish"),
        ("Consumer Spending Collapses as Confidence Hits Record Low", "bearish"),
        ("Factory Orders Plunge: Manufacturing Sector in Crisis", "bearish"),
        ("Banking Sector Under Pressure as Loan Losses Mount", "bearish"),
        ("Economists Debate Depth and Duration of Current Recession", "bearish"),
    ],
    Regime.RECOVERY: [
        ("Green Shoots: Economy Shows Early Signs of Recovery", "bullish"),
        ("Markets Bounce as Leading Indicators Turn Positive", "bullish"),
        ("Cautious Optimism Returns as Hiring Picks Up", "mixed"),
        ("Recovery Takes Hold: Industrial Production Rises for Third Month", "bullish"),
        ("Investors Rotate Back Into Equities as Outlook Improves", "bullish"),
        ("Credit Markets Thaw as Recovery Gains Momentum", "mixed"),
        ("Small Business Confidence Ticks Up, Signaling Broader Recovery", "bullish"),
        ("Housing Starts Rebound, Adding to Recovery Evidence", "bullish"),
    ],
}

# ── Volatility-driven headlines ────────────────────────────────────────

_VOL_HEADLINES: dict[VolatilityState, list[tuple[str, str]]] = {
    VolatilityState.LOW: [
        ("VIX Drops to Multi-Year Low as Calm Pervades Markets", "bullish"),
        ("Market Volatility at Historic Lows: Is Complacency a Risk?", "mixed"),
    ],
    VolatilityState.NORMAL: [],  # No special headline for normal vol
    VolatilityState.HIGH: [
        ("Volatility Spikes as Markets Digest Mixed Signals", "bearish"),
        ("Wild Swings on Wall Street as Traders Navigate Uncertainty", "mixed"),
        ("Options Market Signals Elevated Risk Ahead", "bearish"),
    ],
    VolatilityState.CRISIS: [
        ("Panic Selling Grips Markets in Wild Session", "bearish"),
        ("VIX Surges Past 40: Fear Index Signals Extreme Stress", "bearish"),
        ("Circuit Breakers Triggered as Markets Plunge", "bearish"),
        ("Historic Volatility: Markets See Largest Intraday Swings in a Decade", "bearish"),
    ],
}

# ── Rate-driven headlines ──────────────────────────────────────────────

_RATE_HEADLINES: dict[RateDirection, list[tuple[str, str]]] = {
    RateDirection.RISING: [
        ("Treasury Yields Hit Fresh Highs on Hawkish Fed Signals", "bearish"),
        ("Bond Market Selloff Accelerates as Rate Hike Expectations Rise", "bearish"),
        ("Mortgage Rates Surge, Cooling Housing Market Momentum", "mixed"),
    ],
    RateDirection.STABLE: [
        ("Fed Holds Steady: Markets React to Policy Pause", "mixed"),
        ("Rate Stability Provides Backdrop for Measured Risk-Taking", "mixed"),
    ],
    RateDirection.FALLING: [
        ("Bond Rally Extends as Yields Fall to New Lows", "bullish"),
        ("Rate Cuts Boost Growth Stocks: Tech Leads Market Higher", "bullish"),
        ("Falling Rates Spark Refinancing Boom and Housing Optimism", "bullish"),
    ],
}

# ── Event-triggered headlines keyed by template_name ───────────────────

_EVENT_HEADLINES: dict[str, list[tuple[str, str, dict[str, str]]]] = {
    "Oil Price Spike": [
        (
            "Crude Surges on OPEC Cuts — Energy Stocks Whipsaw",
            "mixed",
            {"Energy": "volatile", "Consumer Staples": "negative", "Consumer Discretionary": "negative"},
        ),
        (
            "Oil Prices Spike: Energy Sector Rallies as Consumers Feel the Pinch",
            "mixed",
            {"Energy": "positive", "Consumer Staples": "negative", "Consumer Discretionary": "negative"},
        ),
    ],
    "Tech Earnings Miss": [
        (
            "Big Tech Stumbles: Megacap Earnings Disappoint Across the Board",
            "bearish",
            {"Tech": "negative"},
        ),
        (
            "Silicon Valley Selloff: Tech Giants Report Weakening Demand",
            "bearish",
            {"Tech": "negative"},
        ),
    ],
    "Pandemic Fears": [
        (
            "New Virus Variant Sparks Global Health Concerns and Market Jitters",
            "bearish",
            {"Consumer Staples": "negative", "Consumer Discretionary": "negative", "Energy": "negative", "Healthcare": "mixed"},
        ),
    ],
    "Surprise Rate Cut": [
        (
            "Emergency Rate Cut Catches Markets Off Guard — Indices Surge",
            "bullish",
            {"Tech": "positive", "Financials": "mixed"},
        ),
    ],
    "Trade War Escalation": [
        (
            "Tariff Threats Escalate: Global Trade Tensions Rattle Markets",
            "bearish",
            {"Industrials": "negative", "Tech": "negative"},
        ),
    ],
    "Bank Run Scare": [
        (
            "Regional Bank Shares Plunge on Deposit Flight Fears",
            "bearish",
            {"Financials": "negative"},
        ),
    ],
    "Infrastructure Bill": [
        (
            "Landmark Infrastructure Spending Bill Clears Key Hurdle",
            "bullish",
            {"Industrials": "positive", "Energy": "positive"},
        ),
    ],
    "Consumer Confidence Surge": [
        (
            "Consumer Confidence Hits Multi-Year High, Boosting Retail Sector",
            "bullish",
            {"Consumer Staples": "positive", "Consumer Discretionary": "positive"},
        ),
    ],
    "Crypto Crash": [
        (
            "Cryptocurrency Meltdown Spills Over Into Tech Stocks",
            "bearish",
            {"Tech": "negative", "Financials": "mixed"},
        ),
    ],
    "Supply Chain Shock": [
        (
            "Global Supply Chain Disruptions Worsen, Squeezing Manufacturers",
            "bearish",
            {"Industrials": "negative", "Consumer Staples": "negative", "Consumer Discretionary": "negative"},
        ),
    ],
    "Geopolitical Crisis": [
        (
            "Geopolitical Tensions Flare: Markets Seek Safe Havens",
            "bearish",
            {"Energy": "positive", "Financials": "negative"},
        ),
    ],
    "Tech IPO Boom": [
        (
            "IPO Market Heats Up as Tech Startups Rush to List",
            "bullish",
            {"Tech": "positive"},
        ),
    ],
    "Manufacturing Boom": [
        (
            "Factory Output Surges: Manufacturing Sector Leads Recovery",
            "bullish",
            {"Industrials": "positive"},
        ),
    ],
    "Debt Ceiling Crisis": [
        (
            "Debt Ceiling Standoff Rattles Bond Markets and Shakes Confidence",
            "bearish",
            {"Financials": "negative"},
        ),
    ],
    "Currency Crisis": [
        (
            "Dollar Volatility Spikes as Currency Markets Roil Emerging Economies",
            "bearish",
            {"Financials": "negative", "Energy": "mixed"},
        ),
    ],
    "AI Breakthrough": [
        (
            "Artificial Intelligence Breakthrough Sends Tech Valuations Soaring",
            "bullish",
            {"Tech": "positive"},
        ),
    ],
    "Energy Transition Deal": [
        (
            "Global Clean Energy Pact Reshapes Energy Sector Outlook",
            "mixed",
            {"Energy": "mixed", "Industrials": "positive"},
        ),
    ],
    "Housing Market Crash": [
        (
            "Housing Prices in Sharp Decline as Mortgage Defaults Rise",
            "bearish",
            {"Financials": "negative", "Consumer Staples": "negative", "Consumer Discretionary": "negative"},
        ),
    ],
    "Central Bank Surprise": [
        (
            "Central Bank Policy Surprise Jolts Global Markets",
            "mixed",
            {"Financials": "volatile"},
        ),
    ],
    "Earnings Season Blowout": [
        (
            "Earnings Season Delivers: Companies Beat Expectations Across Sectors",
            "bullish",
            {"Tech": "positive", "Financials": "positive", "Healthcare": "positive"},
        ),
    ],
}


def generate_headlines(
    macro: MacroState,
    events: list[ShockEvent],
    rng: random.Random,
) -> list[Headline]:
    """Generate 2-4 weekly headlines from market conditions and events.

    Headline sources (in priority):
    1. Event-triggered headlines (one per event, if templates exist)
    2. Regime headline (always at least one)
    3. Volatility headline (if vol is not NORMAL)
    4. Rate headline (fill to reach target count)
    """
    headlines: list[Headline] = []
    target_count = rng.randint(2, 4)

    # 1. Event-triggered headlines
    for event in events:
        event_pool = _EVENT_HEADLINES.get(event.template_name, [])
        if event_pool and len(headlines) < target_count:
            text, sentiment, impact = rng.choice(event_pool)
            headlines.append(Headline(
                text=text,
                sentiment=sentiment,
                impact_summary=impact,
            ))

    # 2. Regime headline (always include at least one)
    if len(headlines) < target_count:
        regime_pool = _REGIME_HEADLINES[macro.regime]
        text, sentiment = rng.choice(regime_pool)
        headlines.append(Headline(
            text=text,
            sentiment=sentiment,
            impact_summary={},
        ))

    # 3. Volatility headline (if notable)
    vol_pool = _VOL_HEADLINES.get(macro.volatility_state, [])
    if vol_pool and len(headlines) < target_count:
        text, sentiment = rng.choice(vol_pool)
        headlines.append(Headline(
            text=text,
            sentiment=sentiment,
            impact_summary={},
        ))

    # 4. Rate headline (fill remaining slots)
    if len(headlines) < target_count:
        rate_pool = _RATE_HEADLINES.get(macro.rate_direction, [])
        if rate_pool:
            text, sentiment = rng.choice(rate_pool)
            headlines.append(Headline(
                text=text,
                sentiment=sentiment,
                impact_summary={},
            ))

    # 5. If still short, pull another regime headline
    if len(headlines) < 2:
        regime_pool = _REGIME_HEADLINES[macro.regime]
        text, sentiment = rng.choice(regime_pool)
        headlines.append(Headline(
            text=text,
            sentiment=sentiment,
            impact_summary={},
        ))

    return headlines
