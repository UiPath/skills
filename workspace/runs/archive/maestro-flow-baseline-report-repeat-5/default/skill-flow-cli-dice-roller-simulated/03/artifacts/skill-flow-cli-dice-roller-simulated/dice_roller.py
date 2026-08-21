#!/usr/bin/env python3
"""A simple CLI dice roller."""

import random
import sys


def roll_die(sides: int = 6) -> int:
    """Roll a single die with the given number of sides."""
    if sides < 2:
        raise ValueError(f"A die must have at least 2 sides, got {sides}")
    return random.randint(1, sides)


def main():
    # Default to a standard 6-sided die
    sides = 6

    # Allow optional command-line argument: python dice_roller.py [sides]
    if len(sys.argv) > 1:
        try:
            sides = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid number of sides.")
            sys.exit(1)

    try:
        result = roll_die(sides)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Rolling a d{sides}...")
    print(f"You rolled: {result}")


if __name__ == "__main__":
    main()
