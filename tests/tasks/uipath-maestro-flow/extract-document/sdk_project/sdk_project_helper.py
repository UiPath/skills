#!/usr/bin/env python3
"""Helper for the sdk_* tasks: print the flow the agent built outside the user's project.

Picks the first .flow (sorted) that holds an Extract document node, sits next to
a project.uiproj, has no .flow-sdk/ beside it, and is not in the user's project:
``PermitDesk/PermitDesk`` unless another project directory is the argument.
Prints nothing when none matches, so validate_flow.py fails with "flow file not
found" (sdk_project) and ``test -z`` passes (sdk_cache_only, sdk_existing_node).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_EXTRACT_NODE = re.compile(r'"type": *"uipath[.]ixp[.]extract-document-builder"')


def main() -> None:
    user_project = Path(sys.argv[1] if len(sys.argv) > 1 else "PermitDesk/PermitDesk")
    for flow in sorted(Path(".").rglob("*.flow")):
        if "node_modules" in flow.parts or flow.parent == user_project:
            continue
        project = flow.parent
        if not (project / "project.uiproj").is_file() or (project / ".flow-sdk").exists():
            continue
        if _EXTRACT_NODE.search(flow.read_text(encoding="utf-8", errors="replace")):
            print(flow)
            return


if __name__ == "__main__":
    main()
