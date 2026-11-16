#!/usr/bin/env python3
"""Assert the agentic-search design is bounded, not just labelled.

The failure this guards is a design that names "agentic search" and then
describes an uncapped retrieval loop — the exact shape that dies at
AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS. A bounded design needs both:

  1. a numeric ceiling on searches per question, and
  2. a stop rule saying what the agent does once that ceiling is reached.

Adjectives ("a few", "as needed") do not count as a ceiling.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DESIGN = Path.cwd() / "design.md"

# "at most 3", "maximum of 5 searches", "budget: 4", "up to three searches"
WORD_NUMBERS = "two|three|four|five|six|seven|eight|nine|ten"
CEILING = re.compile(
    rf"(?:maximum|max|up to|at most|no more than|limit(?:ed)? to|budget)"
    rf"[^.\n]{{0,40}}?(?:\b([2-9]|10)\b|\b({WORD_NUMBERS})\b)",
    re.IGNORECASE,
)
# The stop rule must tie an ending to the exhausted budget, not merely say "stop".
STOP_RULE = re.compile(
    r"(?:stop|halt|cease|end)[^.\n]{0,80}?"
    r"(?:search|quer|retriev|budget|limit|maximum)"
    r"|(?:after|once|when)[^.\n]{0,60}?(?:budget|maximum|limit|last search)"
    r"[^.\n]{0,80}?(?:answer|respond|report|stop)",
    re.IGNORECASE,
)


def main() -> int:
    if not DESIGN.is_file():
        print(f"FAIL: {DESIGN} not found", file=sys.stderr)
        return 1

    text = DESIGN.read_text(encoding="utf-8", errors="replace")
    failures = []

    ceiling = CEILING.search(text)
    if ceiling:
        print(f"OK: numeric search ceiling — {ceiling.group(0).strip()!r}")
    else:
        failures.append(
            "no numeric search ceiling (expected e.g. 'at most 3 searches'); "
            "an adjective like 'a few' does not bound the loop"
        )

    stop = STOP_RULE.search(text)
    if stop:
        print(f"OK: stop rule — {stop.group(0).strip()!r}")
    else:
        failures.append(
            "no stop rule tying the exhausted budget to answering; "
            "a cap without one ends the run at maxIterations with no answer"
        )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
