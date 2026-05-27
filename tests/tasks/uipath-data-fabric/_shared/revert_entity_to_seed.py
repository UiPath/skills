#!/usr/bin/env python3
"""
Post-run cleanup wrapper: revert a brownfield Data Fabric entity to its
canonical seed state.

Thin shim over ``seed_entity.py --reset``: forwards the same flags (with
``--reset`` appended) so the source of truth for the seed (schema + records
JSON files) stays in one place. The separate filename keeps post_run lines
obviously about *cleanup* — pre_run uses ``seed_entity.py`` for setup,
post_run uses ``revert_entity_to_seed.py`` for revert.

Usage (typically called from a brownfield task's post_run):
    revert_entity_to_seed.py --entity-name IntegrationOrders \
        --schema-file seeds/integration_orders.schema.json \
        --records-file seeds/integration_orders.records.json

Exits with the same status as seed_entity.py (which is always 0 unless
arg validation fails) — cleanup never blocks the test.
"""

import os
import sys
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    seed_script = here / "seed_entity.py"
    if not seed_script.exists():
        print(f"FAIL: seed_entity.py not found next to revert script at {seed_script}", file=sys.stderr)
        sys.exit(1)

    # Pass every argv flag through to seed_entity.py, append --reset to flip
    # it into restore mode (wipe records, re-insert canonical seed).
    args = [sys.executable, str(seed_script), *sys.argv[1:], "--reset"]
    print(f"[revert] forwarding to: {' '.join(args[1:])}")
    os.execv(sys.executable, args)


if __name__ == "__main__":
    main()
