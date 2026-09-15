#!/usr/bin/env python3
"""Verify the flow builds Data Fabric read + create with the NATIVE nodes.

Grades the path `planning-arch.md` makes the default for record CRUD, which no
other task covers — every task under `connector_features/datafabric_connector/`
pins itself to `uipath.connector.uipath-uipath-dataservice.*` instead.

Three things have to hold, and the third is the one that catches a hand-written
definition:

1. Node instances of `core.datafabric.read` and `core.datafabric.create` exist,
   both naming FlowCodeEvalEntity via `inputs.entityConfig`.
2. No `uipath-uipath-dataservice` connector activity stands in for either.
3. Each type has a `definitions[]` entry that looks like it came from
   `registry get` — `model.type == "bpmn:Task"` and an `api-function` runtime
   exclusion. A definition typed `bpmn:ServiceTask`, or missing the exclusion,
   is the signature of a definition assembled from the doc's field list rather
   than copied from the registry, which passes `flow validate` and fails at
   runtime.
"""
import glob
import json
import sys

ENTITY = "FlowCodeEvalEntity"
READ = "core.datafabric.read"
CREATE = "core.datafabric.create"
CONNECTOR_PREFIX = "uipath.connector.uipath-uipath-dataservice."


def _entity_of(node):
    cfg = node.get("inputs", {}).get("entityConfig") or {}
    return cfg.get("entityName")


def _check_definition(defs_by_type, node_type):
    """``None`` when the definition looks registry-sourced, else why it does not."""
    d = defs_by_type.get(node_type)
    if d is None:
        return f"no definitions[] entry for {node_type}"
    model_type = (d.get("model") or {}).get("type")
    if model_type != "bpmn:Task":
        return f"{node_type} definition has model.type={model_type!r}, expected 'bpmn:Task'"
    exclude = (d.get("runtimeConstraints") or {}).get("exclude") or []
    if "api-function" not in exclude:
        return f"{node_type} definition is missing the 'api-function' runtimeConstraints.exclude"
    return None


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file found", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)

        nodes = doc.get("nodes", [])
        types = [n.get("type", "") for n in nodes]
        if READ not in types or CREATE not in types:
            continue

        defs_by_type = {
            d.get("nodeType"): d for d in doc.get("definitions", []) if isinstance(d, dict)
        }

        problems = []

        for node_type in (READ, CREATE):
            matching = [n for n in nodes if n.get("type") == node_type]
            if not any(_entity_of(n) == ENTITY for n in matching):
                got = sorted({repr(_entity_of(n)) for n in matching})
                problems.append(
                    f"no {node_type} node names entityName={ENTITY!r} "
                    f"(inputs.entityConfig.entityName saw {', '.join(got) or 'nothing'})"
                )
            why = _check_definition(defs_by_type, node_type)
            if why:
                problems.append(why)

        substitutes = sorted({t for t in types if t.startswith(CONNECTOR_PREFIX)})
        if substitutes:
            problems.append(
                "connector activities stand in alongside the native nodes: "
                + ", ".join(substitutes)
            )

        if problems:
            print(f"FAIL: {path}", file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            return 1

        print(f"OK: {path} — native {READ} + {CREATE} on {ENTITY}, definitions registry-shaped")
        return 0

    print(
        f"FAIL: no .flow carries both {READ} and {CREATE} node instances. "
        f"Types seen: {sorted({t for p in flows for t in [n.get('type','') for n in json.load(open(p)).get('nodes',[])]})}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
