#!/usr/bin/env python3
"""Helper for sdk_project.yaml: print the flow the agent built outside PermitDesk.

Picks the first .flow (sorted) that holds an Extract document node, sits next to
a project.uiproj, and has no .flow-sdk/ beside it. Prints nothing when none
matches, so validate_flow.py fails with "flow file not found".
"""

from __future__ import annotations

import re
from pathlib import Path

_EXTRACT_NODE = re.compile(r'"type": *"uipath[.]ixp[.]extract-document-builder"')
_SDK_PROJECT = Path("PermitDesk", "PermitDesk")


def main() -> None:
    for flow in sorted(Path(".").rglob("*.flow")):
        if "node_modules" in flow.parts or flow.parent == _SDK_PROJECT:
            continue
        project = flow.parent
        if not (project / "project.uiproj").is_file() or (project / ".flow-sdk").exists():
            continue
        if _EXTRACT_NODE.search(flow.read_text(encoding="utf-8", errors="replace")):
            print(flow)
            return


if __name__ == "__main__":
    main()
