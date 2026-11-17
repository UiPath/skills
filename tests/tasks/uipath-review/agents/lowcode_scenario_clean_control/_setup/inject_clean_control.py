#!/usr/bin/env python3
"""Scaffold the clean triage agent with no planted defects."""

from pathlib import Path

from lowcode_clean_agent import write_clean_triage_agent


def main() -> None:
    write_clean_triage_agent(Path("ReviewSol"))
    print("Wrote clean triage agent")


if __name__ == "__main__":
    main()
