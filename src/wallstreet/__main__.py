"""Entry point: python -m wallstreet"""

import argparse
import random
import sys

from wallstreet.cli.app import run_game
from wallstreet.cli.display import display_game_list
from wallstreet.models.game import GameConfig
from wallstreet.persistence.repository import GameRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wall Street War Room -- Portfolio Management Roguelike"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--name", type=str, default="Player",
        help="Player name",
    )
    parser.add_argument(
        "--weeks", type=int, default=26,
        choices=[3, 5, 10, 13, 26],
        help="Season length in months (3 = quick play)",
    )
    parser.add_argument(
        "--list-games", action="store_true",
        help="List all saved games",
    )

    args = parser.parse_args()

    if args.list_games:
        repo = GameRepository()
        repo.initialize()
        games = repo.list_games()
        display_game_list(games)
        repo.close()
        sys.exit(0)

    if args.seed is None:
        args.seed = random.randint(0, 2**32 - 1)

    config = GameConfig(
        seed=args.seed,
        player_name=args.name,
        total_weeks=args.weeks,
    )

    run_game(config)


if __name__ == "__main__":
    main()
