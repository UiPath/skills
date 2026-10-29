#!/usr/bin/env python3
"""Grade the Extract document node from what the CLI reports about the flow.

Node types come from `uip maestro flow nodes list`, not from matching the file
text. `fileRef` is left to `flow validate`, which rejects anything but a `$vars`
reference on this node.

Usage (cwd = sandbox root):
    check_extract_document_node.py present --flow-name InvoiceReader
    check_extract_document_node.py absent
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _shared.flow_check import assert_no_flow_files, find_flow_files  # noqa: E402

NODE_TYPE = "uipath.ixp.extract-document-builder"


def list_node_types(flow: str):
    """Node types `nodes list` reports, or (None, reason). Never raises: a
    broken call must read as a criterion failure with a reason."""
    try:
        proc = subprocess.run(
            ["uip", "maestro", "flow", "nodes", "list", flow, "--output", "json"],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as exc:
        return None, f"could not invoke uip: {exc}"
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "")[:300]
    try:
        nodes = (json.loads(proc.stdout).get("Data") or {}).get("Nodes") or []
    except ValueError:
        return None, proc.stdout[:300]
    return [node.get("Type") or "" for node in nodes], None


def check_present(flow_name: str) -> int:
    targets = [f for f in find_flow_files() if os.path.basename(f) == f"{flow_name}.flow"]
    if len(targets) != 1:
        print(f"FAIL - {len(targets)} discovered .flow files are named {flow_name}.flow")
        return 1
    types, err = list_node_types(targets[0])
    if types is None:
        print(f"FAIL - nodes list failed on {targets[0]}: {err}")
        return 1
    ixp_types = sorted({t for t in types if t.startswith("uipath.ixp.")})
    if NODE_TYPE not in ixp_types:
        print(f"FAIL - no {NODE_TYPE} node in {targets[0]}; uipath.ixp.* nodes: {ixp_types}")
        return 1
    others = [t for t in ixp_types if t != NODE_TYPE]
    if others:
        print(f"FAIL - other uipath.ixp.* nodes beside Extract document: {others}")
        return 1
    print(f"PASS - {targets[0]} has an Extract document node and no other uipath.ixp.* node")
    return 0


def check_absent() -> int:
    try:
        assert_no_flow_files()
        print("PASS - no .flow file, so no Extract document node")
        return 0
    except SystemExit:
        pass
    for flow in find_flow_files():
        types, err = list_node_types(flow)
        if types is None:
            print(f"FAIL - nodes list failed on {flow}: {err}")
            return 1
        if NODE_TYPE in types:
            print(f"FAIL - {flow} has an Extract document node the request never asked for")
            return 1
    print("PASS - no discovered .flow has an Extract document node")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("present").add_argument("--flow-name", required=True)
    sub.add_parser("absent")
    args = parser.parse_args()
    return check_present(args.flow_name) if args.mode == "present" else check_absent()


if __name__ == "__main__":
    sys.exit(main())
