#!/usr/bin/env python3
"""Cross-check each native `core.datafabric.*` node instance against the shape
Studio Web writes, which `flow validate` does NOT enforce:

- a `definitions[]` entry exists for the node's exact `type`:`typeVersion`,
  and it is the registry's copy rather than a hand-written or trimmed one:
  `model.type == "bpmn:Task"`, `"api-function"` in
  `runtimeConstraints.exclude`, a non-empty `form.sections`, and an
  `outputDefinition` for every verb except delete (every registry version of
  these nodes has all of them; flow-workbench core-datafabric-*/v1.*.ts)
- instance `outputs`, when present, match the definition's
  `outputDefinition`: no key the definition lacks, and the same `type`, `var`
  and `source` for each key. The canvas persists these (instance-converters.ts
  `nodeToInstance` keeps every output whose `source` is set, and the manifests
  declare `source: '=response'`), so they are allowed, not invented. Delete
  declares no output, so it carries none.
- no instance `model` block. Studio Web never writes one (flow-core node.ts:
  "`node.model` is never written"; `nodeToInstance` omits it), and export
  spreads an instance copy over the definition's (services bpmn-to-xml.ts), so
  a copy that differs changes the BPMN.
- no outgoing edge with `sourcePort: "error"` (these four nodes have no
  error port)

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
NO_OUTPUT_TYPES = {"core.datafabric.delete"}


def _source(value):
    """`=response` whether written as the canvas does or as the SDK does.

    The canvas keeps the manifest's plain string (`'=response'`); the builder
    SDK wraps it as `{type: 'literal', expression: '=response', ...}`.
    """
    if isinstance(value, dict):
        return value.get("expression", value.get("source"))
    return value


def _definition_problems(d: dict, node_type: str) -> list[str]:
    problems = []
    model_type = (d.get("model") or {}).get("type") if isinstance(d.get("model"), dict) else None
    if model_type != "bpmn:Task":
        problems.append(f"model.type is {model_type!r}, expected 'bpmn:Task'")
    constraints = d.get("runtimeConstraints")
    exclude = (constraints or {}).get("exclude") if isinstance(constraints, dict) else None
    if not isinstance(exclude, list) or "api-function" not in exclude:
        problems.append("runtimeConstraints.exclude lacks 'api-function'")
    form = d.get("form")
    sections = form.get("sections") if isinstance(form, dict) else None
    if not isinstance(sections, list) or not sections:
        problems.append("form.sections is empty or missing")
    if node_type not in NO_OUTPUT_TYPES and not isinstance(d.get("outputDefinition"), dict):
        problems.append("outputDefinition is missing")
    return problems


def _outputs_problems(outputs, definition: dict | None, node_type: str) -> list[str]:
    if outputs is None or outputs == {}:
        return []
    if not isinstance(outputs, dict):
        return [f"instance `outputs` is a {type(outputs).__name__}, not an object"]
    if node_type in NO_OUTPUT_TYPES:
        return [f"instance `outputs` {sorted(outputs)} on a node type that declares no output"]
    declared = (definition or {}).get("outputDefinition")
    if not isinstance(declared, dict):
        return []  # already reported against the definition
    problems = []
    extra = sorted(set(outputs) - set(declared))
    if extra:
        problems.append(f"instance `outputs` has {extra}, which the definition's "
                        f"outputDefinition {sorted(declared)} does not declare")
    for key in sorted(set(outputs) & set(declared)):
        mine, theirs = outputs[key], declared[key]
        if not isinstance(mine, dict) or not isinstance(theirs, dict):
            problems.append(f"instance `outputs.{key}` is not an object")
            continue
        for field in ("type", "var"):
            if mine.get(field) != theirs.get(field):
                problems.append(f"instance `outputs.{key}.{field}` is {mine.get(field)!r}, "
                                f"the definition says {theirs.get(field)!r}")
        if _source(mine.get("source")) != _source(theirs.get("source")):
            problems.append(f"instance `outputs.{key}.source` is {_source(mine.get('source'))!r}, "
                            f"the definition says {_source(theirs.get('source'))!r}")
    return problems


def check_flow(path: str) -> list[str]:
    with open(path) as f:
        doc = json.load(f)

    # A definitions[] entry copied from `registry get` carries the node type
    # under `nodeType` (some manifest shapes also mirror it as `type`).
    defs_by_key = {
        (d.get("nodeType") or d.get("type"), str(d.get("version"))): d
        for d in doc.get("definitions", [])
        if isinstance(d, dict)
    }
    nodes = [n for n in doc.get("nodes", []) if isinstance(n, dict) and n.get("type") in CORE_TYPES]
    if not nodes:
        return []

    errors = []
    # `.flow` edges name their ends `sourceNodeId`/`targetNodeId`; `source` is
    # accepted for any older shape.
    error_edge_sources = {
        e.get("sourceNodeId", e.get("source"))
        for e in doc.get("edges", [])
        if isinstance(e, dict) and e.get("sourcePort") == "error"
    }

    for n in nodes:
        node_id = n.get("id", "<unknown>")
        node_type = n.get("type")
        type_version = str(n.get("typeVersion"))

        definition = defs_by_key.get((node_type, type_version))
        if definition is None:
            errors.append(
                f"{path}: node {node_id!r} ({node_type}:{type_version}) has no matching "
                f"definitions[] entry"
            )
        else:
            for problem in _definition_problems(definition, node_type):
                errors.append(f"{path}: definitions[] entry for {node_type}:{type_version} "
                              f"is not the registry's copy — {problem}")
        for problem in _outputs_problems(n.get("outputs"), definition, node_type):
            errors.append(f"{path}: node {node_id!r} ({node_type}) — {problem}")
        if "model" in n:
            errors.append(f"{path}: node {node_id!r} ({node_type}) carries an instance "
                          f"`model` block — Studio Web never writes one (the definition "
                          f"owns BPMN type/serviceType; export merges an instance copy over it)")
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
