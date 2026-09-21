#!/usr/bin/env python3
"""Assert the routed Flow was built with the Summarize node, not an extraction node.

The workload is a cited full-document review, which routes to Summarize. The
failure this guards is a correct mode label attached to the wrong node: an
agent that says "Summarize" and then wires an IxP extraction node has not
routed the workload, it has only named it.

Asserts, against a single discovered `.flow` file:
  1. a `.flow` file exists (the project was actually built);
  2. it contains the Summarize wire type `uipath.pattern.deep-rag` — the canvas
     label is "Summarize" but the serialized type is not;
  3. it contains no `uipath.ixp.*` extraction node.

Discovery is a recursive glob because `uip maestro flow init` scaffolds a
wrapper solution directory whose name the prompt does not pin, so the .flow
path cannot be hardcoded.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SUMMARIZE_TYPE = "uipath.pattern.deep-rag"
IXP_NODE = re.compile(r"uipath\.ixp\.[A-Za-z0-9_.-]+")
SKIP_DIRS = {"node_modules", ".git", ".venv", "__pycache__"}


def discover() -> list[Path]:
    return [
        p
        for p in Path.cwd().rglob("*.flow")
        if not SKIP_DIRS.intersection(p.parts) and p.is_file()
    ]


def main() -> int:
    flows = discover()
    if not flows:
        print("FAIL: no .flow file found anywhere in the sandbox", file=sys.stderr)
        return 1

    print(f"discovered {len(flows)} .flow file(s): {[str(f) for f in flows]}")

    for flow in flows:
        text = flow.read_text(encoding="utf-8", errors="replace")
        if SUMMARIZE_TYPE not in text:
            continue

        ixp = IXP_NODE.search(text)
        if ixp:
            print(
                f"FAIL: {flow} carries Summarize but also an extraction node "
                f"({ixp.group(0)}) — the workload is a cited review, not field extraction",
                file=sys.stderr,
            )
            return 1

        print(f"OK: {flow} uses {SUMMARIZE_TYPE} and no uipath.ixp.* node")
        return 0

    print(
        f"FAIL: no discovered .flow contains {SUMMARIZE_TYPE!r}. "
        "A cited full-document review routes to Summarize; the canvas label is "
        "'Summarize' but the serialized node type is 'uipath.pattern.deep-rag'.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
