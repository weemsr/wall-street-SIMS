"""Fed Chair agent — generates weekly policy statements."""

import random

from wallstreet.models.enums import RateDirection, Regime, VolatilityState
from wallstreet.models.market import MacroState
from wallstreet.models.narrative import FedStatement

# Statement templates keyed by (regime, rate_direction)
# Each pool contains 5+ templates for variety
_STATEMENT_TEMPLATES: dict[tuple[Regime, RateDirection], list[str]] = {
    (Regime.BULL, RateDirection.RISING): [
        "The committee notes sustained economic expansion and robust labor markets. Inflation pressures remain elevated, warranting continued policy vigilance. We are prepared to act further if conditions require.",
        "Economic indicators suggest above-trend growth. The committee judges that the current pace of tightening remains appropriate. We will continue monitoring inflation data closely.",
        "Growth has exceeded expectations this quarter. The committee sees upside risks to inflation and stands ready to adjust policy accordingly. Financial conditions remain supportive.",
        "The economy continues to demonstrate resilience. With price stability our mandate, the committee maintains its hawkish posture. Rate normalization remains on track.",
        "Labor markets are tight and consumer spending is strong. The committee reaffirms its commitment to bringing inflation back to target through measured rate increases.",
    ],
    (Regime.BULL, RateDirection.STABLE): [
        "The economy is growing at a healthy pace. The committee has decided to hold rates steady while assessing the cumulative impact of prior tightening. We remain data-dependent.",
        "Economic conditions warrant a pause in rate adjustments. The committee sees balanced risks and will monitor incoming data before determining the next policy move.",
        "Growth remains solid and inflation is moderating. The committee judges the current policy stance as appropriate and sees no urgency to adjust rates at this time.",
        "The expansion continues on firm footing. The committee holds rates unchanged, balancing the need for price stability against the goal of maximum employment.",
        "Market conditions are orderly and the economy is performing well. The committee maintains its current stance and will proceed cautiously in future decisions.",
    ],
    (Regime.BULL, RateDirection.FALLING): [
        "Despite positive growth signals, the committee sees an opportunity to provide additional accommodation. This rate adjustment is a mid-cycle recalibration, not a directional shift.",
        "The economy is expanding but inflation remains below target. The committee has opted for a modest rate reduction to sustain the expansion and support price stability.",
        "Growth is healthy but global headwinds warrant a precautionary easing. The committee views this adjustment as insurance against downside risks to the outlook.",
        "The committee has reduced rates to extend the current expansion. We see this as a prudent step given the balance of risks, not a signal of broader concerns.",
        "Economic fundamentals are sound. The committee's rate cut reflects an effort to align policy with the neutral rate and support continued growth.",
    ],
    (Regime.BEAR, RateDirection.RISING): [
        "The committee acknowledges the challenging economic environment but judges that inflation remains the primary threat. Further tightening may be necessary despite slowing growth.",
        "Economic conditions have softened, but the committee cannot ignore persistent price pressures. We will continue our tightening cycle until inflation is decisively contained.",
        "Markets have experienced turbulence, yet the committee's resolve on inflation is firm. The path to price stability may involve short-term economic discomfort.",
        "Growth has moderated and financial conditions have tightened. The committee nevertheless maintains its hawkish stance given the stickiness of core inflation measures.",
        "The committee recognizes the difficult trade-offs in the current environment. However, history shows that failing to address inflation now leads to worse outcomes later.",
    ],
    (Regime.BEAR, RateDirection.STABLE): [
        "The committee is closely monitoring the deteriorating economic outlook. We have chosen to hold rates steady to assess whether the slowdown is temporary or structural.",
        "Economic conditions have weakened. The committee pauses to evaluate the lagged effects of prior rate actions before determining the appropriate next step.",
        "Markets are under stress and growth is slowing. The committee holds rates unchanged while weighing the competing risks of recession and persistent inflation.",
        "The committee notes rising uncertainty in economic forecasts. We maintain current rates and stand ready to act in either direction as conditions evolve.",
        "Financial markets are signaling caution. The committee's decision to hold reflects a desire for more clarity before committing to the next policy move.",
    ],
    (Regime.BEAR, RateDirection.FALLING): [
        "The committee has moved decisively to cut rates in response to clear signs of economic weakness. We will continue to use all tools at our disposal to support the economy.",
        "Deteriorating conditions require urgent action. The committee has reduced rates and signals willingness to ease further if the downturn deepens.",
        "The committee acknowledges the severity of the current slowdown. Today's rate cut reflects our commitment to cushioning the economy against further deterioration.",
        "Growth risks have shifted firmly to the downside. The committee has acted to provide relief and restore confidence in the economic outlook.",
        "Financial stress has intensified. The committee's rate reduction aims to ease credit conditions and prevent the slowdown from becoming self-reinforcing.",
    ],
    (Regime.RECESSION, RateDirection.RISING): [
        "Despite the contraction, the committee judges that inflation expectations must be anchored. This difficult decision reflects our long-term commitment to price stability.",
        "The committee acknowledges the recession but warns that abandoning the inflation fight now would cause greater harm. We maintain our tightening bias with heavy hearts.",
        "These are painful times for the economy. The committee's decision to hold firm on rates reflects the painful reality that stagflation requires resolute policy action.",
        "Economic output is contracting, yet inflation persists above target. The committee's mandate requires us to prioritize price stability even during periods of economic distress.",
        "The recession is real and painful. But the committee cannot ignore the inflation threat. We proceed with caution but remain committed to our dual mandate.",
    ],
    (Regime.RECESSION, RateDirection.STABLE): [
        "The economy is in contraction. The committee holds rates steady as it assesses the depth of the downturn and the trajectory of inflation expectations.",
        "The committee acknowledges the severe economic conditions. We pause to evaluate whether prior rate actions are sufficient or whether additional measures are needed.",
        "Output is falling and unemployment is rising. The committee holds rates while preparing contingency measures should conditions deteriorate further.",
        "The recession has proven deeper than anticipated. The committee maintains current rates but is actively considering the full range of policy options.",
        "The committee recognizes the pain households and businesses are experiencing. We hold rates steady and will act promptly if the situation warrants.",
    ],
    (Regime.RECESSION, RateDirection.FALLING): [
        "The committee has cut rates aggressively to combat the recession. We stand ready to deploy all available tools to stabilize the economy and restore growth.",
        "The depth of the economic contraction demands bold action. The committee has reduced rates substantially and signals further easing is likely if conditions warrant.",
        "The committee has acted with urgency. Today's rate cut is among the largest in recent memory, reflecting the severity of the economic downturn we face.",
        "We are in extraordinary times requiring extraordinary measures. The committee has slashed rates and is exploring additional policy interventions to support the economy.",
        "The economy needs support, and the committee is delivering it. This aggressive rate cut is part of a comprehensive strategy to prevent a deeper contraction.",
    ],
    (Regime.RECOVERY, RateDirection.RISING): [
        "The recovery is gaining traction, and the committee judges it appropriate to begin normalizing policy. Gradual rate increases will help ensure the expansion is sustainable.",
        "Encouraging signs of recovery allow the committee to start withdrawing emergency accommodation. We will proceed carefully to avoid disrupting the healing process.",
        "The economy has turned a corner. The committee begins a measured tightening cycle, confident that the recovery can withstand a return to more normal rates.",
        "Recovery is underway and the committee sees an opportunity to rebuild policy space. Rate increases will be gradual and data-dependent.",
        "The healing economy gives the committee room to normalize. We raise rates modestly, balancing the need to control emerging inflation against the fragility of the recovery.",
    ],
    (Regime.RECOVERY, RateDirection.STABLE): [
        "The recovery continues at a moderate pace. The committee holds rates steady to allow the expansion to gather strength before considering further adjustments.",
        "Economic conditions are improving. The committee sees no rush to adjust rates and will allow the recovery to build momentum before acting.",
        "The committee is encouraged by the recovery but remains cautious. We hold rates unchanged and will evaluate the durability of the improvement before making changes.",
        "The economy is healing. The committee maintains accommodative policy to support the recovery while monitoring for any signs of overheating.",
        "Conditions are improving gradually. The committee holds steady, balancing the desire to support growth against the need to prevent excessive risk-taking.",
    ],
    (Regime.RECOVERY, RateDirection.FALLING): [
        "The recovery remains fragile. The committee has opted for additional accommodation to ensure the economic rebound takes hold and becomes self-sustaining.",
        "While conditions are improving, the committee judges that further support is warranted. This rate cut aims to accelerate the recovery and reduce slack in the economy.",
        "The committee provides additional stimulus to cement the recovery. We will maintain accommodative conditions until we are confident the expansion is durable.",
        "The healing process needs more time and more support. The committee cuts rates to bolster confidence and encourage investment during this critical phase.",
        "The recovery is progressing but unevenly. The committee's rate reduction aims to broaden the expansion and support sectors still under stress.",
    ],
}

# Policy bias mapping
_POLICY_BIAS: dict[RateDirection, str] = {
    RateDirection.RISING: "tightening",
    RateDirection.STABLE: "neutral",
    RateDirection.FALLING: "easing",
}

# Confidence level ranges by volatility state (higher vol = lower confidence)
_CONFIDENCE_RANGES: dict[VolatilityState, tuple[float, float]] = {
    VolatilityState.LOW: (0.75, 0.95),
    VolatilityState.NORMAL: (0.60, 0.80),
    VolatilityState.HIGH: (0.40, 0.65),
    VolatilityState.CRISIS: (0.20, 0.45),
}


class FedChairAgent:
    """Generates weekly Federal Reserve policy statements.

    Deterministic and template-based for MVP. Designed so the
    generate() method can be swapped to an LLM call later.
    """

    def generate(self, macro: MacroState, rng: random.Random) -> FedStatement:
        """Generate a Fed policy statement for the current week."""
        key = (macro.regime, macro.rate_direction)
        templates = _STATEMENT_TEMPLATES[key]
        statement = rng.choice(templates)

        policy_bias = _POLICY_BIAS[macro.rate_direction]

        conf_lo, conf_hi = _CONFIDENCE_RANGES[macro.volatility_state]
        confidence = round(rng.uniform(conf_lo, conf_hi), 2)

        return FedStatement(
            statement=statement,
            policy_bias=policy_bias,
            confidence_level=confidence,
        )
