#!/usr/bin/env python3
"""Grade how an Extract document node sits in its flow, from the ``.flow`` JSON.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_extract_document.py --flow-name <NAME> <CHECK> [--only] [VALUE ...]

``--flow-name NAME`` selects the discovered ``NAME.flow``, as in
``flow_contains.py``. The node under test is the first
``uipath.ixp.extract-document-builder`` node in it. Its taxonomy is its
``inputs.schemaDocument``, the document ``nodes schema get`` prints.

Checks:
    fields JSON          each entry of the JSON array fits a different field:
                         '[{"name": "date", "type": "ft-date"}, {"says": "prefix"}]'
                         "name" is searched in the field name, "says" in its
                         instructions and "group" in the name of the group
                         holding it (case-insensitive regex, so a plain word
                         means "contains"). "type" must equal the field type
                         and "id" its x-uipath-field-id. "repeats" (true or
                         false) says whether that group is a repeating one.
                         An entry may give any of these keys. With --only,
                         the taxonomy has no field beyond the entries.
    described            the overall prompt, every group and every field have
                         a description
    defs                 the six built-in field types are still in $defs; with
                         --only, $defs holds nothing else
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
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import find_flow_files  # noqa: E402

EXTRACT_NODE_TYPE = "uipath.ixp.extract-document-builder"
IXP_NODE_PREFIX = "uipath.ixp."
BUILT_IN_TYPES = (
    "ft-exact-text",
    "ft-inferred-text",
    "ft-date",
    "ft-number",
    "ft-monetary-quantity",
    "ft-boolean",
)
FIELD_KEYS = {"name", "type", "says", "group", "id", "repeats"}
PATTERN_KEYS = ("name", "says", "group")
ONLY_CHECKS = ("fields", "defs")


def _output_schema(node: dict) -> dict:
    return ((node.get("inputs") or {}).get("schemaDocument") or {}).get("outputSchema") or {}


def _groups(node: dict) -> dict:
    return _output_schema(node).get("properties") or {}


def _fields(node: dict) -> list[tuple[str, str, dict, bool]]:
    """``(group, field, spec, repeats)`` for every field, in plain and table groups."""
    result = []
    for group, spec in _groups(node).items():
        props = spec.get("properties") or (spec.get("items") or {}).get("properties") or {}
        kind = spec.get("type")
        repeats = "array" in (kind if isinstance(kind, list) else [kind])
        result.extend((group, name, field, repeats) for name, field in props.items())
    return result


def _type(field: dict) -> str:
    return field.get("$ref", "").rsplit("/", 1)[-1] or "no type"


def _fits(want: dict, group: str, name: str, field: dict, repeats: bool) -> bool:
    text = {"name": name, "says": field.get("description") or "", "group": group}
    if any(k in want and not re.search(want[k], text[k], re.IGNORECASE) for k in PATTERN_KEYS):
        return False
    if "type" in want and want["type"] != _type(field):
        return False
    if "id" in want and want["id"] != field.get("x-uipath-field-id"):
        return False
    return "repeats" not in want or want["repeats"] == repeats


def _describe(group: str, name: str, field: dict, repeats: bool) -> str:
    table = " (repeats)" if repeats else ""
    field_id = field.get("x-uipath-field-id") or "none"
    return f"'{group} > {name}'{table} {_type(field)} id {field_id} {(field.get('description') or '')!r}"


def _match(wanted: list[dict], fields: list[tuple]) -> tuple[list[dict], set[int]]:
    """Give each wanted entry a different field (bipartite matching, so not greedy).

    Returns the entries left without one, and the indexes of the fields given out.
    """
    owner: dict[int, int] = {}

    def place(w: int, seen: set[int]) -> bool:
        for f, entry in enumerate(fields):
            if f in seen or not _fits(wanted[w], *entry):
                continue
            seen.add(f)
            if f not in owner or place(owner[f], seen):
                owner[f] = w
                return True
        return False

    missing = [wanted[w] for w in range(len(wanted)) if not place(w, set())]
    return missing, set(owner)


def parse_fields(values: list[str]) -> list[dict]:
    """Read the ``fields`` value; raise ValueError when it is malformed."""
    if len(values) != 1:
        raise ValueError("fields takes one JSON array; quote it")
    try:
        wanted = json.loads(values[0])
    except ValueError as exc:
        raise ValueError(f"fields takes a JSON array ({exc})") from None
    if not isinstance(wanted, list) or not wanted:
        raise ValueError("fields takes a non-empty JSON array")
    for want in wanted:
        if (
            not isinstance(want, dict)
            or not want
            or set(want) - FIELD_KEYS
            or not all(isinstance(v, bool if k == "repeats" else str) for k, v in want.items())
        ):
            raise ValueError(
                "each entry has string name, type, says, group or id keys and a true or "
                f"false repeats, not {json.dumps(want)}"
            )
        for key in PATTERN_KEYS:
            if key in want:
                try:
                    re.compile(want[key])
                except re.error as exc:
                    raise ValueError(f"{key} {want[key]!r} is not a valid pattern ({exc})") from None
    return wanted


def check_fields(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    fields = _fields(node)
    missing, used = _match(args.wanted, fields)
    problems = []
    for want in missing:
        fitting = [f"{g} > {n}" for g, n, f, r in fields if _fits(want, g, n, f, r)]
        if fitting:
            problems.append(f"{json.dumps(want)} fits only {fitting}, already used by another entry")
        else:
            problems.append(f"no field fits {json.dumps(want)}")
    if args.only:
        problems += [
            f"'{g} > {n}' is a field no entry asks for"
            for i, (g, n, _, _) in enumerate(fields)
            if i not in used
        ]
    if not problems:
        return None
    found = "; ".join(_describe(*entry) for entry in fields)
    return "; ".join(problems) + f" (the taxonomy has: {found or 'no fields'})"


def check_described(_: dict, node: dict, __: argparse.Namespace) -> str | None:
    problems = []
    if not ((node.get("inputs") or {}).get("schemaDocument") or {}).get("prompt"):
        problems.append("the overall prompt is empty")
    problems += [f"group {g!r} has no description" for g, s in _groups(node).items() if not s.get("description")]
    problems += [f"field '{g} > {n}' has no description" for g, n, f, _ in _fields(node) if not f.get("description")]
    return "; ".join(problems) or None


def check_defs(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    defs = _output_schema(node).get("$defs") or {}
    problems = [f"$defs is missing {t} (has: {', '.join(defs) or 'none'})" for t in BUILT_IN_TYPES if t not in defs]
    if args.only:
        problems += [f"$defs also has {k}, which is not a built-in field type" for k in defs if k not in BUILT_IN_TYPES]
    return "; ".join(problems) or None


def _extract_expression(value: object) -> str:
    """The ``$vars`` expression of a ``=js:`` string or a ``jsExpression`` object."""
    if isinstance(value, dict) and value.get("type") == "jsExpression":
        value = value.get("expression")
    return value.strip().removeprefix("=js:").strip() if isinstance(value, str) else ""


def check_file_ref(flow: dict, node: dict, _: argparse.Namespace) -> str | None:
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


def check_edge(flow: dict, node: dict, args: argparse.Namespace) -> str | None:
    direction, port = args.values
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


def check_no_other_ixp(flow: dict, node: dict, _: argparse.Namespace) -> str | None:
    others = [
        f"{n.get('id')} ({n.get('type')})"
        for n in flow.get("nodes") or []
        if (n.get("type") or "").startswith(IXP_NODE_PREFIX) and n is not node
    ]
    return f"other uipath.ixp.* nodes: {', '.join(others)}" if others else None


CHECKS = {
    "fields": check_fields,
    "described": check_described,
    "defs": check_defs,
    "file-ref": check_file_ref,
    "edge": check_edge,
    "no-other-ixp": check_no_other_ixp,
}


def _usage_error(args: argparse.Namespace) -> str | None:
    if args.only and args.check not in ONLY_CHECKS:
        return f"--only applies to {' and '.join(ONLY_CHECKS)}, not {args.check}"
    if args.check == "fields":
        try:
            args.wanted = parse_fields(args.values)
        except ValueError as exc:
            return str(exc)
    elif args.check == "edge":
        if len(args.values) != 2 or args.values[0] not in ("in", "out"):
            return "edge takes: in|out PORT"
    elif args.values:
        return f"{args.check} takes no values"
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--flow-name", required=True, help="flow name, without .flow")
    parser.add_argument("--only", action="store_true", help="fields, defs: and nothing else")
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("values", nargs="*")
    args = parser.parse_args(argv)

    usage = _usage_error(args)
    if usage:
        print(f"FAIL: {usage}", file=sys.stderr)
        return 2
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
        problem = CHECKS[args.check](flow, node, args)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if problem:
        print(f"FAIL: {args.check}: {problem}", file=sys.stderr)
        return 1
    print(f"OK: {args.check}{' --only' if args.only else ''} {' '.join(args.values)}".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
