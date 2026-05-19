#!/usr/bin/env python3
"""pre_run: initialize seed.json with a fresh per-run uuid8.

Use this when a test needs the naming prefix but doesn't need any seeded
tenant artifacts (folders / process / solution fixture). The agent reads
seed.json's `uuid8` to derive unique resource names.

After this runs, seed.json contains:
    { "uuid8": "<8-hex>", "task_id": "<from TASK_ID env>" }
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_common import load_or_init_seed, log, naming_prefix


def main() -> int:
    seed = load_or_init_seed()
    log(f"seed initialized: prefix={naming_prefix(seed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
