"""Short Seller agent — scans player allocations for vulnerabilities."""

import random

from wallstreet.models.enums import RateDirection, Regime, Sector, VolatilityState
from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import ShortThesis
from wallstreet.models.portfolio import Allocation

# Sectors classified as cyclical (sensitive to economic downturns)
_CYCLICAL_SECTORS = {Sector.TECH, Sector.ENERGY, Sector.INDUSTRIALS}

# Rate-sensitive sectors
_RATE_SENSITIVE = {Sector.TECH, Sector.FINANCIALS}


# ── Critique templates keyed by (attack_type, sector) ──────────────────

_CONCENTRATION_CRITIQUES: dict[Sector, list[str]] = {
    Sector.TECH: [
        "Massive tech concentration is a ticking time bomb. One earnings miss and this portfolio implodes.",
        "This portfolio is a leveraged bet on tech. Classic retail trap — chasing momentum into the abyss.",
        "Overloaded on tech with zero hedging. When the music stops, this portfolio won't have a chair.",
        "Tech exposure at these levels screams capitulation-in-waiting. We're building our short position now.",
    ],
    Sector.ENERGY: [
        "Dangerously concentrated in energy. One OPEC headline and this portfolio is toast.",
        "This kind of energy exposure reeks of commodity speculation. The fundamentals don't support it.",
        "All-in on energy? Supply shocks cut both ways. This is a short seller's dream.",
        "Massive energy bet in this vol environment is reckless. We're positioning accordingly.",
    ],
    Sector.FINANCIALS: [
        "Heavy financial exposure in this rate environment is a recipe for disaster.",
        "This portfolio is a proxy for a bank balance sheet. One credit event and it's over.",
        "Concentrated financials position screams late-cycle hubris. We've seen this movie before.",
        "Overweight financials with credit spreads widening? Bold strategy. We disagree.",
    ],
    Sector.CONSUMER: [
        "Oversized consumer bet suggests this manager has run out of ideas.",
        "Heavy consumer allocation at these valuations is dead money. We see downside from here.",
        "Hiding in consumer stocks won't save this portfolio from macro reality.",
        "Consumer concentration at these levels ignores the margin compression story entirely.",
    ],
    Sector.INDUSTRIALS: [
        "Industrials overweight in this cycle is a textbook value trap. We're short.",
        "Heavy industrial exposure with PMIs rolling over. This portfolio is fighting the data.",
        "Oversized industrials bet ignores the CapEx slowdown that's already underway.",
        "This kind of industrial concentration is what happens when a PM reads last quarter's data.",
    ],
}

_REGIME_MISALIGNMENT_CRITIQUES: dict[Sector, list[str]] = {
    Sector.TECH: [
        "Overweight tech in a recessionary environment is financial malpractice. History is clear here.",
        "Loading up on growth stocks during a contraction. This portfolio manager needs a history lesson.",
    ],
    Sector.ENERGY: [
        "Energy overweight during recession? Demand is collapsing. This is a gift for short sellers.",
        "Cyclical energy exposure in a downturn reveals a fundamental misread of the macro picture.",
    ],
    Sector.INDUSTRIALS: [
        "Heavy industrials in a recession is contrarian for the wrong reasons. Earnings will crater.",
        "Industrials overweight while the economy contracts? The order books tell a different story.",
    ],
    Sector.FINANCIALS: [
        "Financials overweight as credit quality deteriorates. Loan losses will eat this alive.",
        "Leaning into financials during economic stress — classic mistake of confusing cheap with value.",
    ],
    Sector.CONSUMER: [
        "Consumer stocks won't be the safe haven this PM thinks. Spending is already rolling over.",
        "Overweight consumer heading into a spending cliff. Defensive positioning isn't always safe.",
    ],
}

_RATE_SENSITIVITY_CRITIQUES: list[str] = [
    "Tech overweight with rates rising is fighting the Fed. Duration risk is real and it's coming.",
    "Loading up on rate-sensitive growth while the Fed tightens. Discount rates matter.",
    "This tech exposure in a rising rate environment is textbook duration risk. We're short.",
    "Rising rates will compress these tech multiples. This portfolio is on the wrong side of history.",
]

_MOMENTUM_REVERSAL_CRITIQUES: dict[Sector, list[str]] = {
    Sector.TECH: [
        "Tech has run hot and this portfolio is all-in. Mean reversion is a matter of when, not if.",
        "Chasing tech momentum at these levels. The smart money is already rotating out.",
    ],
    Sector.ENERGY: [
        "Energy's winning streak has attracted a crowd. Crowded trades always end the same way.",
        "Energy momentum is peaking. This overweight position is buying the top.",
    ],
    Sector.FINANCIALS: [
        "Financials rallied and this PM piled in. Classic performance-chasing behavior.",
        "Momentum in financials is already fading. This overweight will underperform from here.",
    ],
    Sector.CONSUMER: [
        "Consumer run-up has this PM complacent. Margin pressures are building underneath.",
        "Chasing consumer momentum into stretched valuations. We see a reversal ahead.",
    ],
    Sector.INDUSTRIALS: [
        "Industrials momentum is extended. This overweight position is late to the party.",
        "Industrial rally is long in the tooth. Overweight here is buying the consensus, not the opportunity.",
    ],
}

_SHORT_SQUEEZE_CRITIQUES: dict[Sector, list[str]] = {
    Sector.TECH: [
        "Shorting tech in a bull market? Bold. When the squeeze hits, this portfolio will feel it.",
        "This PM is short tech while the sector is rallying. We love to see it — easy money on the squeeze.",
    ],
    Sector.ENERGY: [
        "Short energy into a rising commodity cycle? This PM is about to learn about short squeezes.",
        "Betting against energy here is contrarian for the wrong reasons. Supply constraints say otherwise.",
    ],
    Sector.FINANCIALS: [
        "Shorting financials while credit conditions are stable. This position is exposed to a violent unwind.",
        "A short financials bet this size is a gift. One positive earnings surprise and this blows up.",
    ],
    Sector.CONSUMER: [
        "Consumer shorts in a healthy economy? This PM is overthinking it. Spending data disagrees.",
        "Shorting consumer staples — the definition of picking up pennies in front of a steamroller.",
    ],
    Sector.INDUSTRIALS: [
        "Short industrials while CapEx is expanding? This PM is on the wrong side of the cycle.",
        "Betting against industrials here is fighting the order book. We're positioned for the squeeze.",
    ],
}


class ShortSellerAgent:
    """Scans player allocation for vulnerabilities and fires short thesis attacks.

    Deterministic and template-based for MVP. Designed so the
    analyze() method can be swapped to an LLM call later.
    """

    def analyze(
        self,
        allocation: Allocation,
        macro: MacroState,
        game_state: GameState,
        rng: random.Random,
    ) -> ShortThesis | None:
        """Analyze player allocation for vulnerabilities.

        Returns a ShortThesis if a vulnerability is found, otherwise None.
        Checks are evaluated in priority order; first match wins.
        """
        # 1. Concentration attack: any sector |weight| > 40%
        result = self._check_concentration(allocation, rng)
        if result:
            return result

        # 2. Player short squeeze: shorts in bull/recovery market
        result = self._check_player_short(allocation, macro, rng)
        if result:
            return result

        # 3. Regime misalignment: cyclicals overweight in recession
        result = self._check_regime_misalignment(allocation, macro, rng)
        if result:
            return result

        # 4. Rate sensitivity: tech overweight in rising rates
        result = self._check_rate_sensitivity(allocation, macro, rng)
        if result:
            return result

        # 5. Momentum reversal: sector with streak + heavy allocation
        result = self._check_momentum_reversal(allocation, game_state, rng)
        if result:
            return result

        # No vulnerability found
        return None

    def _check_concentration(
        self, allocation: Allocation, rng: random.Random
    ) -> ShortThesis | None:
        """Attack any sector with |weight| > 40%."""
        for sector, weight in allocation.weights.items():
            abs_w = abs(weight)
            if abs_w > 40.0:
                severity = (abs_w - 40.0) / 60.0  # 0 at 40%, 1 at 100%
                conviction = round(0.60 + severity * 0.35, 2)  # 0.60 – 0.95
                critique = rng.choice(_CONCENTRATION_CRITIQUES[sector])
                return ShortThesis(
                    target_sector=sector,
                    critique=critique,
                    conviction=min(conviction, 0.95),
                )
        return None

    def _check_player_short(
        self, allocation: Allocation, macro: MacroState, rng: random.Random
    ) -> ShortThesis | None:
        """Attack player short positions in bull/recovery markets (squeeze risk)."""
        if macro.regime not in (Regime.BULL, Regime.RECOVERY):
            return None

        # Find the largest short position
        short_weights = {
            s: w for s, w in allocation.weights.items() if w < -10.0
        }
        if not short_weights:
            return None

        target = min(short_weights, key=short_weights.get)  # type: ignore[arg-type]
        weight = abs(short_weights[target])
        severity = (weight - 10.0) / 40.0  # 0 at -10%, 1 at -50%
        conviction = round(0.55 + severity * 0.35, 2)
        critique = rng.choice(_SHORT_SQUEEZE_CRITIQUES[target])
        return ShortThesis(
            target_sector=target,
            critique=critique,
            conviction=min(conviction, 0.90),
        )

    def _check_regime_misalignment(
        self, allocation: Allocation, macro: MacroState, rng: random.Random
    ) -> ShortThesis | None:
        """Attack cyclicals that are overweight during recession/bear."""
        if macro.regime not in (Regime.RECESSION, Regime.BEAR):
            return None

        # Find the heaviest cyclical sector
        cyclical_weights = {
            s: allocation.weights[s]
            for s in _CYCLICAL_SECTORS
            if allocation.weights[s] > 25.0
        }
        if not cyclical_weights:
            return None

        target = max(cyclical_weights, key=cyclical_weights.get)  # type: ignore[arg-type]
        weight = cyclical_weights[target]
        severity = (weight - 25.0) / 75.0
        conviction = round(0.55 + severity * 0.35, 2)
        critique = rng.choice(_REGIME_MISALIGNMENT_CRITIQUES[target])
        return ShortThesis(
            target_sector=target,
            critique=critique,
            conviction=min(conviction, 0.90),
        )

    def _check_rate_sensitivity(
        self, allocation: Allocation, macro: MacroState, rng: random.Random
    ) -> ShortThesis | None:
        """Attack tech overweight when rates are rising."""
        if macro.rate_direction != RateDirection.RISING:
            return None

        tech_weight = allocation.weights[Sector.TECH]
        if tech_weight <= 30.0:
            return None

        severity = (tech_weight - 30.0) / 70.0
        conviction = round(0.50 + severity * 0.40, 2)
        critique = rng.choice(_RATE_SENSITIVITY_CRITIQUES)
        return ShortThesis(
            target_sector=Sector.TECH,
            critique=critique,
            conviction=min(conviction, 0.90),
        )

    def _check_momentum_reversal(
        self, allocation: Allocation, game_state: GameState, rng: random.Random
    ) -> ShortThesis | None:
        """Attack sectors with 2+ weeks of positive returns where player is heavy."""
        if len(game_state.history) < 2:
            return None

        recent = game_state.history[-2:]
        for sector in Sector:
            # Check if sector had 2 consecutive positive weeks
            streak = all(
                week.adjusted_returns.returns[sector] > 0.0 for week in recent
            )
            if not streak:
                continue

            weight = allocation.weights[sector]
            if weight < 25.0:
                continue

            severity = (weight - 25.0) / 75.0
            conviction = round(0.50 + severity * 0.30, 2)
            critiques = _MOMENTUM_REVERSAL_CRITIQUES[sector]
            critique = rng.choice(critiques)
            return ShortThesis(
                target_sector=sector,
                critique=critique,
                conviction=min(conviction, 0.80),
            )
        return None
