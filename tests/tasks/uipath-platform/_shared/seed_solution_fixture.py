#!/usr/bin/env python3
"""pre_run: copy tests/fixtures/solutions/minimal into the sandbox CWD.

Pure-local — no tenant calls. After this runs, the sandbox contains a fully-formed
solution that the agent can `uip solution pack` / `publish` / `deploy run` from.

Writes into seed.json:
    solution_dir: name of the copied solution dir
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_common import FIXTURES_DIR, load_or_init_seed, log, save_seed


def main() -> int:
    src = FIXTURES_DIR / "solutions" / "minimal"
    if not src.is_dir():
        log(f"FAIL: solution fixture missing at {src} — run `make install` to build fixtures")
        return 1

    seed = load_or_init_seed()
    dest_name = src.name
    dest = Path(dest_name)
    if dest.exists():
        log(f"skip: {dest} already exists in sandbox")
    else:
        shutil.copytree(src, dest)
        log(f"OK copied {src} -> {dest}")
    seed["solution_dir"] = dest_name
    save_seed(seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
