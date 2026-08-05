#!/usr/bin/env python3
"""Assert the derived sidecar was left alone (skill-flow-inline-agent-legacy-shell).

`DisputeAnalyst/<GUID>/agent.json` is a DERIVED artifact: the canvas rewrites
it from the `.flow` on every save, so an edit there is shadowed and lost. The
brownfield contract is "read it, migrate its content into the node, leave the
file in place" — so the file must still exist and still hold its seeded
content when the task ends.

Compares parsed JSON (not bytes), so an incidental reformat is tolerated while
any content change fails. Catches sidecar edits made by any means — Write,
Edit, a shell heredoc, or `uip agent refresh`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SIDECAR_REL = Path("BillingSol") / "DisputeAnalyst" / \
    "e5715a3f-0d31-4ad8-9c70-91df180760e6" / "agent.json"
SEEDED = Path(__file__).resolve().parent / "fixture" / SIDECAR_REL


def main() -> int:
    live = Path(os.getcwd()) / SIDECAR_REL
    if not live.is_file():
        print(
            f"FAIL: {SIDECAR_REL} is gone — the stored definition is the "
            "sidecar the flow's agent identity points at; a migration leaves "
            "it in place (it also holds eval sets and server-only fields)",
            file=sys.stderr,
        )
        return 1
    if not SEEDED.is_file():
        print(f"FAIL: seeded fixture missing at {SEEDED}", file=sys.stderr)
        return 1
    try:
        live_json = json.loads(live.read_text())
    except json.JSONDecodeError as exc:
        print(f"FAIL: {SIDECAR_REL} is no longer valid JSON: {exc}", file=sys.stderr)
        return 1
    seeded_json = json.loads(SEEDED.read_text())
    if live_json != seeded_json:
        print(
            f"FAIL: {SIDECAR_REL} was modified — it is a derived artifact "
            "(rewritten from the .flow on every canvas save), so edits there "
            "are shadowed and lost. Author the change in the node's inputs.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {SIDECAR_REL} left untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
