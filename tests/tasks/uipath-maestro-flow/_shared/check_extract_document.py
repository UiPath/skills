#!/usr/bin/env python3
"""Grade how an Extract document node sits in its flow, from the ``.flow`` JSON.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_extract_document.py --flow-name <NAME> <CHECK> [VALUE ...]

``--flow-name NAME`` selects the discovered ``NAME.flow``, as in
``flow_contains.py``. The node under test is the first
``uipath.ixp.extract-document-builder`` node in it.

Checks:
    file-ref             the node's inputs.fileRef reads a declared
                         ``direction: in``, ``type: file`` global
                         (``flow validate`` passes a fileRef to an input that
                         was never declared)
    edge in|out PORT     an edge enters or leaves the node on PORT
    no-other-ixp         no other uipath.ixp.* node: no published model, no
                         processor, no second Extract document node

Exit 0 and ``OK: ...`` on stdout when the check holds. Otherwise exit 1 and a
``FAIL: ...`` line on stderr naming what was found instead.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import find_flow_files  # noqa: E402

EXTRACT_NODE_TYPE = "uipath.ixp.extract-document-builder"
IXP_NODE_PREFIX = "uipath.ixp."


def _extract_expression(value: object) -> str:
    """The ``$vars`` expression of a ``=js:`` string or a ``jsExpression`` object."""
    if isinstance(value, dict) and value.get("type") == "jsExpression":
        value = value.get("expression")
    return value.strip().removeprefix("=js:").strip() if isinstance(value, str) else ""


def check_file_ref(flow: dict, node: dict, _: list[str]) -> str | None:
    declared = [
        f"$vars.{v.get('triggerNodeId')}.output.{v.get('id')}"
        for v in (flow.get("variables") or {}).get("globals") or []
        if v.get("direction") == "in" and v.get("type") == "file"
    ]
    file_ref = (node.get("inputs") or {}).get("fileRef")
    if _extract_expression(file_ref) in declared:
        return None
    return (
        f"fileRef is {json.dumps(file_ref)}, which reads no declared file input "
        f"(file inputs: {', '.join(declared) or 'none'})"
    )


def check_edge(flow: dict, node: dict, values: list[str]) -> str | None:
    if len(values) != 2 or values[0] not in ("in", "out"):
        raise SystemExit("FAIL: edge takes: in|out PORT")
    direction, port = values
    end = "target" if direction == "in" else "source"
    edges = flow.get("edges") or []
    if any(e.get(f"{end}NodeId") == node["id"] and e.get(f"{end}Port") == port for e in edges):
        return None
    found = ", ".join(
        f"{e.get('sourceNodeId')}:{e.get('sourcePort')} -> {e.get('targetNodeId')}:{e.get('targetPort')}"
        for e in edges
    )
    side = "into" if direction == "in" else "out of"
    return f"no edge {side} {node['id']}:{port} (edges: {found or 'none'})"


def check_no_other_ixp(flow: dict, node: dict, _: list[str]) -> str | None:
    others = [
        f"{n.get('id')} ({n.get('type')})"
        for n in flow.get("nodes") or []
        if (n.get("type") or "").startswith(IXP_NODE_PREFIX) and n is not node
    ]
    return f"other uipath.ixp.* nodes: {', '.join(others)}" if others else None


CHECKS = {"file-ref": check_file_ref, "edge": check_edge, "no-other-ixp": check_no_other_ixp}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--flow-name", required=True, help="flow name, without .flow")
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("values", nargs="*")
    args = parser.parse_args(argv)

    try:
        paths = [p for p in find_flow_files() if os.path.basename(p) == f"{args.flow_name}.flow"]
        if not paths:
            raise SystemExit(f"FAIL: no discovered .flow file is named {args.flow_name}.flow")
        with open(paths[0], encoding="utf-8") as fh:
            flow = json.load(fh)
        nodes = flow.get("nodes") or []
        node = next((n for n in nodes if n.get("type") == EXTRACT_NODE_TYPE), None)
        if node is None:
            types = ", ".join(n.get("type", "?") for n in nodes) or "none"
            raise SystemExit(f"FAIL: no Extract document node in {paths[0]} (node types: {types})")
        problem = CHECKS[args.check](flow, node, args.values)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if problem:
        print(f"FAIL: {args.check}: {problem}", file=sys.stderr)
        return 1
    print(f"OK: {args.check} {' '.join(args.values)}".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
