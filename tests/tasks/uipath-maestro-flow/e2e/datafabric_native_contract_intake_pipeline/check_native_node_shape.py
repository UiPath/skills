#!/usr/bin/env python3
"""Cross-check each native `core.datafabric.*` node instance against the
structural rules in references/author/plugins/data-fabric/impl.md that
`flow validate` does NOT enforce:

- a `definitions[]` entry exists for the node's exact `type`:`typeVersion`
  (catches a hand-authored definition standing in for the registry's)
- no instance `outputs` block (the manifest + `variables.nodes[]` own the
  output contract for these nodes — see "JSON structure")
- no instance `model` block
- no outgoing edge with `sourcePort: "error"` (these four nodes have no
  error port — see "No error port")

Exit code:
  0  no defects found
  1  at least one defect
  2  usage error

Usage:
  python3 check_native_node_shape.py [<flow-file>...]

  With no args, globs every **/*.flow under CWD.
"""
import glob
import json
import sys

CORE_TYPES = {
    "core.datafabric.read",
    "core.datafabric.create",
    "core.datafabric.update",
    "core.datafabric.delete",
}


def check_flow(path: str) -> list[str]:
    with open(path) as f:
        doc = json.load(f)

    # A definitions[] entry copied from `registry get` carries the node type
    # under `nodeType` (some manifest shapes also mirror it as `type`).
    defs_by_key = {
        (d.get("nodeType") or d.get("type"), str(d.get("version"))): d
        for d in doc.get("definitions", [])
    }
    nodes = [n for n in doc.get("nodes", []) if n.get("type") in CORE_TYPES]
    if not nodes:
        return []

    errors = []
    error_edge_sources = {
        e.get("source") for e in doc.get("edges", []) if e.get("sourcePort") == "error"
    }

    for n in nodes:
        node_id = n.get("id", "<unknown>")
        node_type = n.get("type")
        type_version = str(n.get("typeVersion"))

        if (node_type, type_version) not in defs_by_key:
            errors.append(
                f"{path}: node {node_id!r} ({node_type}:{type_version}) has no matching "
                f"definitions[] entry"
            )
        if "outputs" in n:
            errors.append(f"{path}: node {node_id!r} ({node_type}) carries an instance "
                           f"`outputs` block — these nodes must not have one")
        if "model" in n:
            errors.append(f"{path}: node {node_id!r} ({node_type}) carries an instance "
                           f"`model` block — BPMN type/serviceType live in the definition")
        if node_id in error_edge_sources:
            errors.append(f"{path}: node {node_id!r} ({node_type}) has an outgoing "
                           f"sourcePort: \"error\" edge — these nodes have no error port")

    return errors


def main() -> int:
    paths = sys.argv[1:] or glob.glob("**/*.flow", recursive=True)
    if not paths:
        print("FAIL: no .flow file", file=sys.stderr)
        return 2

    all_errors = []
    for path in paths:
        all_errors.extend(check_flow(path))

    if all_errors:
        for e in all_errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print(f"OK: native entity node shape clean across {len(paths)} flow file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
