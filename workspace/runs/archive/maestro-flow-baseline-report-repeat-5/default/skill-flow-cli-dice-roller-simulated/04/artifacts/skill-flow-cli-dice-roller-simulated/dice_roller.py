#!/usr/bin/env python3
"""
A simple dice roller CLI tool.
Usage:
  python dice_roller.py          # Roll a standard 6-sided die
  python dice_roller.py 20       # Roll a 20-sided die
  python dice_roller.py 6 3      # Roll three 6-sided dice
"""

import random
import sys


def roll_die(sides: int) -> int:
    """Roll a single die with the given number of sides."""
    return random.randint(1, sides)


def roll_dice(sides: int, count: int) -> list[int]:
    """Roll multiple dice with the given number of sides."""
    return [roll_die(sides) for _ in range(count)]


def display_result(results: list[int], sides: int) -> None:
    """Display the dice roll results in a friendly format."""
    count = len(results)
    total = sum(results)

    die_label = f"d{sides}"

    if count == 1:
        print(f"\n🎲 Rolling 1 {die_label}...")
        print(f"   Result: {results[0]}")
    else:
        print(f"\n🎲 Rolling {count} {die_label}s...")
        print(f"   Individual rolls: {', '.join(str(r) for r in results)}")
        print(f"   Total: {total}")

    print()


def main():
    # Parse arguments
    sides = 6    # default: 6-sided die
    count = 1    # default: roll once

    args = sys.argv[1:]

    try:
        if len(args) >= 1:
            sides = int(args[0])
            if sides < 2:
                print("Error: A die must have at least 2 sides.")
                sys.exit(1)
        if len(args) >= 2:
            count = int(args[1])
            if count < 1:
                print("Error: Must roll at least 1 die.")
                sys.exit(1)
    except ValueError:
        print("Usage: python dice_roller.py [sides] [count]")
        print("  sides  - number of sides on the die (default: 6)")
        print("  count  - number of dice to roll (default: 1)")
        sys.exit(1)

    results = roll_dice(sides, count)
    display_result(results, sides)


if __name__ == "__main__":
    main()
