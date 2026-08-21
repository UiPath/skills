#!/usr/bin/env python3
"""
Dice Roller
-----------
Rolls one or more dice and prints the result.

Usage:
    python dice_roller.py              # roll one standard d6
    python dice_roller.py 3            # roll three d6s
    python dice_roller.py 2 20         # roll two d20s
"""

import random
import sys


def roll(num_dice: int = 1, sides: int = 6) -> list[int]:
    """Return a list of *num_dice* rolls, each in [1, sides]."""
    return [random.randint(1, sides) for _ in range(num_dice)]


def main() -> None:
    args = sys.argv[1:]

    # Parse optional positional arguments: [num_dice] [sides]
    try:
        num_dice = int(args[0]) if len(args) >= 1 else 1
        sides    = int(args[1]) if len(args) >= 2 else 6
    except ValueError:
        print("Usage: python dice_roller.py [num_dice] [sides]")
        print("  Both arguments must be positive integers.")
        sys.exit(1)

    if num_dice < 1 or sides < 2:
        print("Error: num_dice must be >= 1 and sides must be >= 2.")
        sys.exit(1)

    results = roll(num_dice, sides)
    total   = sum(results)

    # ---- pretty output ----
    label = f"{num_dice}d{sides}"
    print(f"\nRolling {label}...")
    print()

    for i, value in enumerate(results, start=1):
        bar = "#" * value
        print(f"  Die {i:>2}: {value:>3}  {bar}")

    if num_dice > 1:
        print()
        print(f"  Total : {total}")

    print()


if __name__ == "__main__":
    main()
