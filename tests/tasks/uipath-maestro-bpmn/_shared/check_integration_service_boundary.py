#!/usr/bin/env python3

import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    require_no_hand_authored_package_files,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("SlackDigestBoundaryBpmn")
    wrappers = [*elements(root, "sendTask"), *elements(root, "serviceTask")]
    if not any(has_uipath_extension(task, "Intsvc.") for task in wrappers):
        fail("missing draft Integration Service uipath:activity shell")
    require_no_private_connector_values(root)
    # Draft boundary: connection binding + package metadata are CLI-owned. Files the
    # CLI wrote (`init` / `update-metadata`) are that boundary; hand-written ones, or a
    # resolved connection id, are what breach it — see require_no_hand_authored_package_files.
    require_no_hand_authored_package_files()
    # The prompt asks for "a README or notes file" and names no location: v1 wrote it
    # beside the .bpmn, the builder-SDK arm at the workspace root (its skill keeps the
    # source there), and a glob pinned to the project folder failed the second on
    # placement alone (run 2026-09-25). Read every notes file the agent left.
    notes = "\n".join(
        Path(p).read_text(encoding="utf-8")
        for p in sorted(glob.glob("**/*.md", recursive=True))
        if "node_modules" not in Path(p).parts and not Path(p).name.startswith("SKILL")
    )
    low = notes.lower()
    # Each blocker is satisfied by any reasonable phrasing of the concept, not a
    # single exact bigram. "Dynamic input schema" is as correct as "dynamic
    # schemas"; the check verifies the agent named the blocker, not its wording.
    required = {
        "connection binding": "connection binding" in low,
        "dynamic schema(s)": bool(re.search(r"dynamic\s+(\w+\s+){0,4}schema", low)),
        "bindings_v2.json": "bindings_v2.json" in low,
        "package metadata": "package metadata" in low,
    }
    missing = [name for name, ok in required.items() if not ok]
    if missing:
        fail(f"boundary notes missing CLI-owned blockers: {missing}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} keeps Integration Service details in the CLI-owned boundary")


if __name__ == "__main__":
    main()
