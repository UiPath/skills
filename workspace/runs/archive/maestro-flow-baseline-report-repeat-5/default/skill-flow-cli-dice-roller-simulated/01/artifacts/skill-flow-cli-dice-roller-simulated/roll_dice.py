#!/usr/bin/env python3
"""A simple dice roller that rolls a 6-sided die and shows the result."""

import random


def roll_die(sides: int = 6) -> int:
    """Roll a die with the given number of sides."""
    return random.randint(1, sides)


def main():
    result = roll_die()
    print(f"🎲 You rolled a {result}!")


if __name__ == "__main__":
    main()
