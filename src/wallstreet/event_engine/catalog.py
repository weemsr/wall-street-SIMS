"""Shock event catalog: 20 events with narrative text and sector effects."""

from wallstreet.models.enums import Regime, Sector
from wallstreet.models.events import ShockEventTemplate

EVENT_CATALOG: list[ShockEventTemplate] = [
    # --- NEGATIVE SHOCKS ---
    ShockEventTemplate(
        name="Oil Price Spike",
        description=(
            "OPEC announces surprise production cuts. "
            "Crude oil surges 12% overnight."
        ),
        sector_effects={
            Sector.ENERGY: 0.06, Sector.TECH: -0.02,
            Sector.CONSUMER: -0.03, Sector.INDUSTRIALS: -0.04,
            Sector.FINANCIALS: -0.01,
        },
        vol_impact=0.3,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.8,
            Regime.RECESSION: 0.5, Regime.RECOVERY: 0.4,
        },
    ),
    ShockEventTemplate(
        name="Tech Earnings Miss",
        description=(
            "Major tech giants report disappointing quarterly earnings. "
            "Analysts slash forecasts."
        ),
        sector_effects={
            Sector.TECH: -0.08, Sector.FINANCIALS: -0.02,
            Sector.ENERGY: 0.0, Sector.CONSUMER: -0.01,
            Sector.INDUSTRIALS: -0.01,
        },
        vol_impact=0.2,
        regime_weights={
            Regime.BULL: 0.4, Regime.BEAR: 0.7,
            Regime.RECESSION: 0.9, Regime.RECOVERY: 0.3,
        },
    ),
    ShockEventTemplate(
        name="Banking Crisis Fears",
        description=(
            "A regional bank announces massive loan losses. "
            "Contagion fears spread across the sector."
        ),
        sector_effects={
            Sector.FINANCIALS: -0.10, Sector.TECH: -0.03,
            Sector.ENERGY: -0.02, Sector.CONSUMER: -0.03,
            Sector.INDUSTRIALS: -0.02,
        },
        vol_impact=0.5,
        regime_weights={
            Regime.BULL: 0.2, Regime.BEAR: 0.6,
            Regime.RECESSION: 1.0, Regime.RECOVERY: 0.2,
        },
    ),
    ShockEventTemplate(
        name="Consumer Confidence Plunge",
        description=(
            "Consumer confidence index drops to decade lows. "
            "Retail stocks tumble."
        ),
        sector_effects={
            Sector.CONSUMER: -0.07, Sector.TECH: -0.02,
            Sector.FINANCIALS: -0.02, Sector.ENERGY: -0.01,
            Sector.INDUSTRIALS: -0.02,
        },
        vol_impact=0.2,
        regime_weights={
            Regime.BULL: 0.2, Regime.BEAR: 0.7,
            Regime.RECESSION: 0.8, Regime.RECOVERY: 0.3,
        },
    ),
    ShockEventTemplate(
        name="Supply Chain Disruption",
        description=(
            "Major port congestion and shipping delays "
            "cripple global supply chains."
        ),
        sector_effects={
            Sector.INDUSTRIALS: -0.06, Sector.CONSUMER: -0.04,
            Sector.TECH: -0.03, Sector.ENERGY: 0.02,
            Sector.FINANCIALS: -0.01,
        },
        vol_impact=0.2,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.5,
            Regime.RECESSION: 0.7, Regime.RECOVERY: 0.4,
        },
    ),
    ShockEventTemplate(
        name="Regulatory Crackdown",
        description=(
            "Government announces sweeping new regulations "
            "targeting Big Tech antitrust violations."
        ),
        sector_effects={
            Sector.TECH: -0.06, Sector.FINANCIALS: -0.02,
            Sector.ENERGY: 0.0, Sector.CONSUMER: 0.01,
            Sector.INDUSTRIALS: 0.0,
        },
        vol_impact=0.15,
        regime_weights={
            Regime.BULL: 0.5, Regime.BEAR: 0.4,
            Regime.RECESSION: 0.3, Regime.RECOVERY: 0.6,
        },
    ),
    ShockEventTemplate(
        name="Geopolitical Tensions",
        description=(
            "Military conflict escalates in a key shipping corridor. "
            "Markets reel on uncertainty."
        ),
        sector_effects={
            Sector.ENERGY: 0.04, Sector.INDUSTRIALS: -0.05,
            Sector.TECH: -0.03, Sector.CONSUMER: -0.03,
            Sector.FINANCIALS: -0.03,
        },
        vol_impact=0.4,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.6,
            Regime.RECESSION: 0.7, Regime.RECOVERY: 0.3,
        },
    ),
    ShockEventTemplate(
        name="Inflation Surprise",
        description=(
            "CPI comes in far above expectations. "
            "The Fed signals emergency rate action."
        ),
        sector_effects={
            Sector.FINANCIALS: -0.04, Sector.TECH: -0.05,
            Sector.CONSUMER: -0.03, Sector.ENERGY: 0.03,
            Sector.INDUSTRIALS: -0.02,
        },
        vol_impact=0.3,
        regime_weights={
            Regime.BULL: 0.4, Regime.BEAR: 0.7,
            Regime.RECESSION: 0.3, Regime.RECOVERY: 0.5,
        },
    ),
    ShockEventTemplate(
        name="Currency Crisis",
        description=(
            "The dollar plunges against major currencies. "
            "Imported goods costs soar."
        ),
        sector_effects={
            Sector.CONSUMER: -0.05, Sector.TECH: -0.02,
            Sector.FINANCIALS: -0.04, Sector.ENERGY: 0.03,
            Sector.INDUSTRIALS: -0.03,
        },
        vol_impact=0.35,
        regime_weights={
            Regime.BULL: 0.2, Regime.BEAR: 0.5,
            Regime.RECESSION: 0.8, Regime.RECOVERY: 0.2,
        },
    ),
    ShockEventTemplate(
        name="Cyber Attack",
        description=(
            "A massive cyberattack takes down critical financial "
            "infrastructure for 48 hours."
        ),
        sector_effects={
            Sector.TECH: -0.05, Sector.FINANCIALS: -0.06,
            Sector.ENERGY: -0.01, Sector.CONSUMER: -0.02,
            Sector.INDUSTRIALS: -0.01,
        },
        vol_impact=0.4,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.4,
            Regime.RECESSION: 0.5, Regime.RECOVERY: 0.3,
        },
    ),
    # --- POSITIVE SHOCKS ---
    ShockEventTemplate(
        name="Tech Breakthrough",
        description=(
            "A revolutionary AI advancement sends tech stocks soaring. "
            "Investors pile in."
        ),
        sector_effects={
            Sector.TECH: 0.08, Sector.FINANCIALS: 0.02,
            Sector.ENERGY: 0.0, Sector.CONSUMER: 0.01,
            Sector.INDUSTRIALS: 0.02,
        },
        vol_impact=0.1,
        regime_weights={
            Regime.BULL: 0.7, Regime.BEAR: 0.2,
            Regime.RECESSION: 0.1, Regime.RECOVERY: 0.6,
        },
    ),
    ShockEventTemplate(
        name="Stimulus Package",
        description=(
            "Congress passes a massive infrastructure and stimulus bill. "
            "Markets rally broadly."
        ),
        sector_effects={
            Sector.INDUSTRIALS: 0.06, Sector.CONSUMER: 0.04,
            Sector.FINANCIALS: 0.03, Sector.TECH: 0.02,
            Sector.ENERGY: 0.03,
        },
        vol_impact=-0.1,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.4,
            Regime.RECESSION: 0.8, Regime.RECOVERY: 0.7,
        },
    ),
    ShockEventTemplate(
        name="Energy Discovery",
        description=(
            "A massive new natural gas field is discovered. "
            "Energy stocks surge on growth prospects."
        ),
        sector_effects={
            Sector.ENERGY: 0.09, Sector.INDUSTRIALS: 0.03,
            Sector.TECH: 0.0, Sector.CONSUMER: 0.01,
            Sector.FINANCIALS: 0.01,
        },
        vol_impact=0.1,
        regime_weights={
            Regime.BULL: 0.5, Regime.BEAR: 0.3,
            Regime.RECESSION: 0.2, Regime.RECOVERY: 0.5,
        },
    ),
    ShockEventTemplate(
        name="Rate Cut Rally",
        description=(
            "The Fed surprises markets with an aggressive rate cut. "
            "Borrowers rejoice."
        ),
        sector_effects={
            Sector.TECH: 0.05, Sector.CONSUMER: 0.04,
            Sector.FINANCIALS: -0.02, Sector.INDUSTRIALS: 0.03,
            Sector.ENERGY: 0.01,
        },
        vol_impact=-0.2,
        regime_weights={
            Regime.BULL: 0.2, Regime.BEAR: 0.5,
            Regime.RECESSION: 0.7, Regime.RECOVERY: 0.6,
        },
    ),
    ShockEventTemplate(
        name="Merger Wave",
        description=(
            "A wave of mega-mergers sweeps the financial sector. "
            "M&A activity hits record highs."
        ),
        sector_effects={
            Sector.FINANCIALS: 0.06, Sector.TECH: 0.02,
            Sector.INDUSTRIALS: 0.02, Sector.CONSUMER: 0.01,
            Sector.ENERGY: 0.01,
        },
        vol_impact=0.1,
        regime_weights={
            Regime.BULL: 0.7, Regime.BEAR: 0.2,
            Regime.RECESSION: 0.1, Regime.RECOVERY: 0.5,
        },
    ),
    ShockEventTemplate(
        name="Consumer Spending Boom",
        description=(
            "Holiday sales shatter records. "
            "Consumer discretionary stocks lead the market higher."
        ),
        sector_effects={
            Sector.CONSUMER: 0.07, Sector.TECH: 0.02,
            Sector.FINANCIALS: 0.02, Sector.INDUSTRIALS: 0.01,
            Sector.ENERGY: 0.01,
        },
        vol_impact=-0.1,
        regime_weights={
            Regime.BULL: 0.6, Regime.BEAR: 0.1,
            Regime.RECESSION: 0.1, Regime.RECOVERY: 0.5,
        },
    ),
    # --- MIXED / SECTOR-ROTATION SHOCKS ---
    ShockEventTemplate(
        name="Sector Rotation",
        description=(
            "Institutional investors rotate out of growth into value. "
            "A classic risk-off move."
        ),
        sector_effects={
            Sector.TECH: -0.04, Sector.ENERGY: 0.03,
            Sector.FINANCIALS: 0.02, Sector.CONSUMER: 0.01,
            Sector.INDUSTRIALS: 0.03,
        },
        vol_impact=0.1,
        regime_weights={
            Regime.BULL: 0.4, Regime.BEAR: 0.5,
            Regime.RECESSION: 0.3, Regime.RECOVERY: 0.4,
        },
    ),
    ShockEventTemplate(
        name="Green Energy Push",
        description=(
            "New climate legislation accelerates renewable investment. "
            "Traditional energy faces headwinds."
        ),
        sector_effects={
            Sector.ENERGY: -0.05, Sector.TECH: 0.03,
            Sector.INDUSTRIALS: 0.04, Sector.CONSUMER: 0.01,
            Sector.FINANCIALS: 0.0,
        },
        vol_impact=0.1,
        regime_weights={
            Regime.BULL: 0.5, Regime.BEAR: 0.3,
            Regime.RECESSION: 0.3, Regime.RECOVERY: 0.6,
        },
    ),
    ShockEventTemplate(
        name="Flash Crash",
        description=(
            "An algorithmic trading malfunction triggers "
            "a brief but violent market sell-off."
        ),
        sector_effects={
            Sector.TECH: -0.04, Sector.ENERGY: -0.03,
            Sector.FINANCIALS: -0.05, Sector.CONSUMER: -0.02,
            Sector.INDUSTRIALS: -0.03,
        },
        vol_impact=0.6,
        regime_weights={
            Regime.BULL: 0.3, Regime.BEAR: 0.5,
            Regime.RECESSION: 0.4, Regime.RECOVERY: 0.3,
        },
    ),
    ShockEventTemplate(
        name="Trade Deal Breakthrough",
        description=(
            "A landmark international trade agreement removes tariffs. "
            "Exporters celebrate."
        ),
        sector_effects={
            Sector.INDUSTRIALS: 0.05, Sector.TECH: 0.03,
            Sector.ENERGY: 0.02, Sector.CONSUMER: 0.03,
            Sector.FINANCIALS: 0.02,
        },
        vol_impact=-0.15,
        regime_weights={
            Regime.BULL: 0.5, Regime.BEAR: 0.3,
            Regime.RECESSION: 0.3, Regime.RECOVERY: 0.7,
        },
    ),
]
