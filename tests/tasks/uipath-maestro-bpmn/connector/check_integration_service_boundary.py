#!/usr/bin/env python3

import glob
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
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
    generated = [
        name
        for name in (
            "bindings_v2.json",
            "entry-points.json",
            "operate.json",
            "package-descriptor.json",
        )
        if glob.glob(f"**/{name}", recursive=True)
    ]
    if generated:
        fail(
            f"draft boundary should not hand-author generated package files: {generated}"
        )
    notes = "\n".join(
        Path(p).read_text(encoding="utf-8")
        for p in glob.glob("SlackDigestBoundaryBpmn/**/*.md", recursive=True)
    )
    required = [
        "connection binding",
        "dynamic schemas",
        "bindings_v2.json",
        "package metadata",
    ]
    missing = [token for token in required if token.lower() not in notes.lower()]
    if missing:
        fail(f"boundary notes missing CLI-owned blockers: {missing}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} keeps Integration Service details in the CLI-owned boundary")


if __name__ == "__main__":
    main()
