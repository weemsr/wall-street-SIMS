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

    Applies 6 rules to assess portfolio risk:
    1. Concentration risk (single sector > 40%)
    2. Regime alignment (cyclicals in recession)
    3. Volatility exposure (concentration in high-vol environments)
    4. Interest rate sensitivity (tech in rising rates)
    5. Drawdown proximity (portfolio near peak drawdown)
    6. Diversification bonus (all sectors <= 30%)

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

        # Rule 1: Concentration risk
        for sector, weight in fracs.items():
            if weight > 0.60:
                risk_score += 3
                warnings.append(
                    f"CRITICAL: {sector.value} at {weight * 100:.0f}% "
                    f"-- extreme concentration."
                )
            elif weight > 0.40:
                risk_score += 2
                warnings.append(
                    f"WARNING: {sector.value} at {weight * 100:.0f}% "
                    f"-- high concentration."
                )

        # Rule 2: Regime alignment
        cyclical_exposure = (
            fracs.get(Sector.TECH, 0)
            + fracs.get(Sector.INDUSTRIALS, 0)
            + fracs.get(Sector.ENERGY, 0)
        )
        if macro_state.regime == Regime.RECESSION and cyclical_exposure > 0.60:
            risk_score += 2
            warnings.append(
                f"Cyclical exposure ({cyclical_exposure * 100:.0f}%) is high "
                f"for a recession regime."
            )

        # Rule 3: Volatility exposure
        if macro_state.volatility_state in (
            VolatilityState.HIGH,
            VolatilityState.CRISIS,
        ):
            max_weight = max(fracs.values())
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

        # Rule 6: Diversification bonus
        if all(w <= 0.30 for w in fracs.values()):
            risk_score = max(1, risk_score - 1)

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
