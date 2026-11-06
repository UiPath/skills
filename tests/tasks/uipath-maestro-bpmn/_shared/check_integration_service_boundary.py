#!/usr/bin/env python3

import glob
import json
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


def check_blockers(text: str) -> dict[str, bool]:
    # Each blocker is satisfied by any reasonable phrasing of the concept,
    # not a single exact bigram. Normalise whitespace so line-wrapped phrases
    # (e.g. "connection\n   binding" or "package\n   metadata") match reliably
    # across line breaks.
    low = re.sub(r"\s+", " ", text.lower())
    conn = r"\b(connection|connector)s?\b"
    bind = r"\b(binding|bind|bound)s?\b"
    conn_bind = bool(
        re.search(rf"{conn}\s+(\S+\s+){{0,8}}{bind}", low)
        or re.search(rf"{bind}\s+(\S+\s+){{0,8}}{conn}", low)
    )
    pkg_meta = bool(
        "package metadata" in low
        or re.search(r"\bpackage\s+(\S+\s+){0,4}metadata\b", low)
    )
    return {
        "connection binding": conn_bind,
        "dynamic schema(s)": bool(
            re.search(r"dynamic\s+(\w+\s+){0,4}schema", low)
        ),
        "bindings_v2.json": "bindings_v2.json" in low,
        "package metadata": pkg_meta,
    }


def check_artifact_bindings(
    required: dict[str, bool], root_dir: str = "."
) -> dict[str, bool]:
    # If connection binding or bindings_v2.json was not identified from
    # prose notes alone, grade the artifact directly: check if
    # bindings_v2.json exists and carries the connection.
    res = dict(required)
    if not (res.get("connection binding") and res.get("bindings_v2.json")):
        pattern = os.path.join(root_dir, "**/bindings_v2.json")
        for p in sorted(glob.glob(pattern, recursive=True)):
            if "node_modules" not in Path(p).parts:
                res["bindings_v2.json"] = True
                try:
                    data = json.loads(Path(p).read_text(encoding="utf-8"))
                    resources = data.get("resources", {})
                    for res_name, res_val in resources.items():
                        res_str = f"{res_name} {res_val}".lower()
                        if "connection" in res_str or "connector" in res_str:
                            res["connection binding"] = True
                            break
                except Exception:
                    pass
    return res


def main() -> None:
    path, root = parse_bpmn("SlackDigestBoundaryBpmn")
    wrappers = [*elements(root, "sendTask"), *elements(root, "serviceTask")]
    if not any(has_uipath_extension(task, "Intsvc.") for task in wrappers):
        fail("missing draft Integration Service uipath:activity shell")
    require_no_private_connector_values(root)
    # Draft boundary: connection binding + package metadata are CLI-owned.
    # Files the CLI wrote (`init` / `update-metadata`) are that boundary;
    # hand-written ones, or a resolved connection id, are what breach it —
    # see require_no_hand_authored_package_files.
    require_no_hand_authored_package_files()
    # The prompt asks for "a README or notes file" and names no location:
    # v1 wrote it beside the .bpmn, the builder-SDK arm at the workspace
    # root (its skill keeps the source there), and a glob pinned to the
    # project folder failed the second on placement alone (run 2026-09-25).
    # Read every notes file the agent left.
    notes = "\n".join(
        Path(p).read_text(encoding="utf-8")
        for p in sorted(glob.glob("**/*.md", recursive=True))
        if "node_modules" not in Path(p).parts
        and not Path(p).name.startswith("SKILL")
    )
    required = check_artifact_bindings(check_blockers(notes))
    missing = [name for name, ok in required.items() if not ok]
    if missing:
        fail(f"boundary notes missing CLI-owned blockers: {missing}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(
        f"OK: {path} keeps Integration Service details in the "
        "CLI-owned boundary"
    )


if __name__ == "__main__":
    main()
