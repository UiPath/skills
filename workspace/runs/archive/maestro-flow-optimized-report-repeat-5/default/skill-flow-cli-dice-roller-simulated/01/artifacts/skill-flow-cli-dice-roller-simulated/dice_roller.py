#!/usr/bin/env python3
"""
dice_roller.py — a simple CLI dice roller.

Usage:
    python dice_roller.py            # roll a single d6
    python dice_roller.py --sides 20 # roll a d20
    python dice_roller.py --rolls 3  # roll three d6s
    python dice_roller.py --sides 10 --rolls 5  # roll five d10s
"""

import argparse
import random


def roll_die(sides: int) -> int:
    """Return a random integer between 1 and `sides` (inclusive)."""
    return random.randint(1, sides)


def run(sides: int = 6, rolls: int = 1) -> None:
    """Run the dice-roller flow and print the result(s)."""
    if sides < 2:
        raise ValueError(f"A die must have at least 2 sides, got {sides}.")
    if rolls < 1:
        raise ValueError(f"Number of rolls must be at least 1, got {rolls}.")

    print(f"\n🎲  Rolling {rolls}d{sides}...\n")

    results = [roll_die(sides) for _ in range(rolls)]

    for i, result in enumerate(results, start=1):
        bar = "█" * result + "░" * (sides - result)
        print(f"  Roll {i:>2}: [{bar}]  →  {result}")

    if rolls > 1:
        total = sum(results)
        print(f"\n  Total : {total}  (min possible {rolls}, max possible {rolls * sides})")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Roll a die and show the result.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--sides", "-s",
        type=int,
        default=6,
        help="Number of sides on the die (default: 6)",
    )
    parser.add_argument(
        "--rolls", "-r",
        type=int,
        default=1,
        help="How many times to roll (default: 1)",
    )
    args = parser.parse_args()
    run(sides=args.sides, rolls=args.rolls)


if __name__ == "__main__":
    main()
