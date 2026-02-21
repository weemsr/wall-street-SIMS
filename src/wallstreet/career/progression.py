"""Career progression logic — title computation and season updates."""

from datetime import datetime

from wallstreet.models.career import CareerProfile, CareerTitle
from wallstreet.models.scoring import ScoreCard


def create_new_career(player_name: str) -> CareerProfile:
    """Create a fresh career profile for a new player."""
    return CareerProfile(
        player_name=player_name,
        title=CareerTitle.RETAIL_SPECULATOR,
        seasons_played=0,
        lifetime_cagr=0.0,
        best_sharpe=0.0,
        worst_drawdown=0.0,
        total_pnl=0.0,
    )


def compute_title(profile: CareerProfile) -> CareerTitle:
    """Compute the career title based on cumulative stats.

    Title thresholds (must meet ALL conditions for a tier):
    - LEGENDARY_ALLOCATOR: 10+ seasons, best_sharpe > 1.5, worst_drawdown > -25%
    - INSTITUTIONAL_STRATEGIST: 5+ seasons, best_sharpe > 1.0
    - MACRO_OPERATOR: 3+ seasons, lifetime_cagr > 0
    - JUNIOR_PM: 1+ completed seasons
    - RETAIL_SPECULATOR: default
    """
    if (
        profile.seasons_played >= 10
        and profile.best_sharpe > 1.5
        and profile.worst_drawdown > -0.25
    ):
        return CareerTitle.LEGENDARY_ALLOCATOR

    if profile.seasons_played >= 5 and profile.best_sharpe > 1.0:
        return CareerTitle.INSTITUTIONAL_STRATEGIST

    if profile.seasons_played >= 3 and profile.lifetime_cagr > 0:
        return CareerTitle.MACRO_OPERATOR

    if profile.seasons_played >= 1:
        return CareerTitle.JUNIOR_PM

    return CareerTitle.RETAIL_SPECULATOR


def update_career_after_season(
    profile: CareerProfile, scorecard: ScoreCard
) -> CareerProfile:
    """Update career profile with results from a completed season.

    Returns a new CareerProfile with updated stats and title.
    """
    new_seasons = profile.seasons_played + 1
    pnl = scorecard.final_value - scorecard.initial_value

    # Running average CAGR
    if new_seasons == 1:
        new_cagr = scorecard.cagr
    else:
        new_cagr = (
            profile.lifetime_cagr * profile.seasons_played + scorecard.cagr
        ) / new_seasons

    new_best_sharpe = max(profile.best_sharpe, scorecard.sharpe_ratio)

    # Worst drawdown: more negative is worse
    if profile.worst_drawdown == 0.0:
        new_worst_dd = scorecard.max_drawdown
    else:
        new_worst_dd = min(profile.worst_drawdown, scorecard.max_drawdown)

    new_total_pnl = profile.total_pnl + pnl

    updated = CareerProfile(
        player_name=profile.player_name,
        seasons_played=new_seasons,
        lifetime_cagr=round(new_cagr, 4),
        best_sharpe=round(new_best_sharpe, 4),
        worst_drawdown=round(new_worst_dd, 4),
        total_pnl=round(new_total_pnl, 2),
        updated_at=datetime.now(),
    )
    updated.title = compute_title(updated)
    return updated
