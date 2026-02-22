"""Rules-based risk committee agent."""

from wallstreet.agents.base import RiskAgent, RiskAssessment
from wallstreet.models.enums import (
    RateDirection,
    Regime,
    Sector,
    VolatilityState,
)
from wallstreet.models.game import GameState
from wallstreet.models.market import MacroState
from wallstreet.models.portfolio import Allocation, PortfolioState


class RulesBasedRiskCommittee(RiskAgent):
    """Deterministic rules-based risk committee.

    Applies 10 rules to assess portfolio risk:
    1. Concentration risk (single sector |weight| > 40%)
    2. Regime alignment (long cyclicals in recession)
    3. Volatility exposure (concentration in high-vol environments)
    4. Interest rate sensitivity (tech in rising rates)
    5. Drawdown proximity (portfolio near peak drawdown)
    6. Diversification bonus (all |weights| <= 30%)
    7. Gross exposure / leverage risk
    8. Short squeeze risk (shorts during high volatility)
    9. Counter-trend short warning (shorting in bull market)
    10. High cash drag (>50% uninvested)

    Designed to be swapped with an LLM-based agent later.
    """

    def evaluate(
        self,
        allocation: Allocation,
        macro_state: MacroState,
        portfolio: PortfolioState,
        game_state: GameState,
    ) -> RiskAssessment:
        risk_score = 1
        warnings: list[str] = []
        fracs = allocation.as_fractions

        # Rule 1: Concentration risk (uses absolute weight)
        for sector, weight in fracs.items():
            abs_w = abs(weight)
            if abs_w > 0.60:
                risk_score += 3
                label = "short" if weight < 0 else "long"
                warnings.append(
                    f"CRITICAL: {sector.value} {label} at {abs_w * 100:.0f}% "
                    f"-- extreme concentration."
                )
            elif abs_w > 0.40:
                risk_score += 2
                label = "short" if weight < 0 else "long"
                warnings.append(
                    f"WARNING: {sector.value} {label} at {abs_w * 100:.0f}% "
                    f"-- high concentration."
                )

        # Rule 2: Regime alignment (only long cyclical exposure counts)
        long_cyclical = sum(
            max(0.0, fracs.get(s, 0)) for s in (Sector.TECH, Sector.INDUSTRIALS, Sector.ENERGY)
        )
        if macro_state.regime == Regime.RECESSION and long_cyclical > 0.60:
            risk_score += 2
            warnings.append(
                f"Cyclical exposure ({long_cyclical * 100:.0f}%) is high "
                f"for a recession regime."
            )

        # Rule 3: Volatility exposure
        if macro_state.volatility_state in (
            VolatilityState.HIGH,
            VolatilityState.CRISIS,
        ):
            max_weight = max(abs(w) for w in fracs.values())
            if max_weight > 0.35:
                risk_score += 1
                warnings.append(
                    "High volatility environment -- consider diversifying."
                )

        # Rule 4: Interest rate sensitivity
        if macro_state.rate_direction == RateDirection.RISING:
            tech_weight = fracs.get(Sector.TECH, 0)
            if tech_weight > 0.35:
                risk_score += 1
                warnings.append(
                    f"Heavy tech ({tech_weight * 100:.0f}%) during rising rates "
                    f"increases sensitivity."
                )

        # Rule 5: Drawdown proximity
        if game_state.weekly_values:
            peak = max(game_state.weekly_values)
            current = portfolio.total_value
            if peak > 0:
                current_dd = (current - peak) / peak
                if current_dd < -0.15:
                    risk_score += 1
                    warnings.append(
                        f"Portfolio is {current_dd * 100:.1f}% from peak -- "
                        f"consider defensive positioning."
                    )

        # Rule 6: Diversification bonus (uses absolute weight)
        if all(abs(w) <= 0.30 for w in fracs.values()):
            risk_score = max(1, risk_score - 1)

        # Rule 7: Gross exposure / leverage risk
        gross = allocation.gross_exposure
        if gross > 1.80:
            risk_score += 2
            warnings.append(
                f"CRITICAL: Gross exposure at {gross * 100:.0f}% -- "
                f"extreme leverage amplifies losses."
            )
        elif gross > 1.40:
            risk_score += 1
            warnings.append(
                f"WARNING: Gross exposure at {gross * 100:.0f}% -- "
                f"elevated leverage risk."
            )

        # Rule 8: Short squeeze risk (shorts during high volatility)
        if allocation.has_shorts and macro_state.volatility_state in (
            VolatilityState.HIGH,
            VolatilityState.CRISIS,
        ):
            short_sectors = [
                s.value for s, w in allocation.weights.items() if w < 0
            ]
            risk_score += 1
            warnings.append(
                f"Short positions ({', '.join(short_sectors)}) during high "
                f"volatility increase squeeze risk."
            )

        # Rule 9: Counter-trend short warning (shorting in bull market)
        if allocation.has_shorts and macro_state.regime == Regime.BULL:
            short_sectors = [
                s.value for s, w in allocation.weights.items() if w < 0
            ]
            risk_score += 1
            warnings.append(
                f"Shorting ({', '.join(short_sectors)}) in a bull market "
                f"is a counter-trend bet -- proceed with caution."
            )

        # Rule 10: High cash drag
        cash_pct = allocation.cash_weight
        if cash_pct > 0.50:
            risk_score += 1
            warnings.append(
                f"Holding {cash_pct * 100:.0f}% cash -- significant drag "
                f"on returns. Consider deploying capital."
            )

        risk_score = min(10, max(1, risk_score))
        critique = self._build_critique(risk_score, warnings, macro_state)

        return RiskAssessment(
            risk_score=risk_score,
            critique=critique,
            warnings=warnings,
        )

    def _build_critique(
        self,
        score: int,
        warnings: list[str],
        macro: MacroState,
    ) -> str:
        """Build a narrative critique from the score and warnings."""
        if score <= 3:
            tone = "The committee finds your allocation prudent."
        elif score <= 6:
            tone = "The committee has some concerns about your positioning."
        elif score <= 8:
            tone = (
                "The committee strongly advises reconsidering this allocation."
            )
        else:
            tone = (
                "The committee is alarmed by this allocation's risk profile."
            )

        parts = [tone]
        parts.extend(warnings)
        parts.append(f"Overall risk assessment: {score}/10.")
        return " ".join(parts)
