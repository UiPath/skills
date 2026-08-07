#!/usr/bin/env python3
"""Assert every seeded inline-agent sidecar was left alone.

Usage (from a task's `run_command`, cwd = sandbox root):
    python3 "$TASK_DIR/../../_shared/check_sidecar_untouched.py" "$TASK_DIR/fixture"

For brownfield inline-agent tasks whose fixture ships a derived sidecar
(`<flow-project>/<GUID>/agent.json`). The sidecar is a DERIVED artifact: the
canvas rewrites it from the `.flow` on every save, so an edit there is shadowed
and lost. The contract is "read it, work in the node, leave the file in place"
— so every seeded `agent.json` must still exist and still hold its seeded
content when the task ends.

Discovery: every `<UUID>/agent.json` under the fixture root, compared to the
same relative path under the sandbox root. Comparison is on parsed JSON, not
bytes, so an incidental reformat passes while any content change fails —
catching edits made by any means (Write, Edit, a shell heredoc, `uip agent
refresh`).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

UUID_DIR_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <fixture-root>", file=sys.stderr)
        return 2
    fixture = Path(argv[1]).resolve()
    if not fixture.is_dir():
        print(f"FAIL: fixture root not found at {fixture}", file=sys.stderr)
        return 1

    seeded = [
        p for p in sorted(fixture.rglob("agent.json"))
        if UUID_DIR_RE.match(p.parent.name)
    ]
    if not seeded:
        print(
            f"FAIL: no seeded <UUID>/agent.json under {fixture} — this check "
            "only applies to fixtures that ship a derived sidecar",
            file=sys.stderr,
        )
        return 1

    sandbox = Path.cwd()
    failures = []
    for path in seeded:
        rel = path.relative_to(fixture)
        live = sandbox / rel
        if not live.is_file():
            failures.append(
                f"{rel} is gone — the flow's agent identity points at this "
                "sidecar; leave it in place (it also holds eval sets and "
                "server-only fields)"
            )
            continue
        try:
            live_json = json.loads(live.read_text())
        except json.JSONDecodeError as exc:
            failures.append(f"{rel} is no longer valid JSON: {exc}")
            continue
        if live_json != json.loads(path.read_text()):
            failures.append(
                f"{rel} was modified — it is a derived artifact (rewritten "
                "from the .flow on every canvas save), so edits there are "
                "shadowed and lost. Author the change in the node's inputs."
            )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"OK: {len(seeded)} seeded sidecar file(s) left untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
