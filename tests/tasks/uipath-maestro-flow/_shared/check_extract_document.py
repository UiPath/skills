#!/usr/bin/env python3
"""Grade how an Extract document node sits in its flow, from the ``.flow`` JSON.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_extract_document.py --flow-name <NAME> <CHECK> [--only] [VALUE ...]

``--flow-name NAME`` selects the discovered ``NAME.flow``, as in
``flow_contains.py``. The node under test is the first
``uipath.ixp.extract-document-builder`` node in it. Its taxonomy is its
``inputs.schemaDocument``, the document ``nodes schema get`` prints.

Checks:
    fields JSON          each entry of the JSON array claims a field it fits:
                         '[{"name_matches": "date", "type": "ft-date"}, {"name": "Total"}]'
                         "name", "group", "type", "instructions" and "id"
                         must equal the field's name, its group's key, its
                         type, its instructions and its x-uipath-field-id.
                         "name_matches", "group_matches" and
                         "instructions_matches" are case-insensitive regexes
                         searched in the same name, group key and
                         instructions. "repeats" (true or
                         false) says whether the group is a table ("type":
                         "array"). An entry may give any of these keys.
                         Entries claim in order, each
                         taking the first field no earlier entry took. With
                         --only, every field is claimed.
    has-instructions     the overall prompt, every group and every field have
                         instructions (a non-empty prompt or description)
    defs                 the six built-in field types are still in $defs; with
                         --only, $defs holds nothing else
    unchanged ORIGINAL [OLD=NEW ...]
                         the taxonomy equals the one in the ORIGINAL .flow,
                         with each OLD field renamed to NEW (same id, type and
                         instructions): prompt, config, groups, fields, ids
                         and $defs. The order of "required" lists is ignored.
    extends ORIGINAL     every group, field, id, instruction, config value
                         and $defs entry of the taxonomy in the ORIGINAL
                         .flow is still there, unchanged. New groups, new
                         fields, their "required" entries and new $defs
                         entries (a Choice) may be added, and the overall
                         prompt may change.
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
EXACT_KEYS = ("name", "group", "type", "instructions", "id")
PATTERN_KEYS = ("name_matches", "group_matches", "instructions_matches")
FIELD_KEYS = {*EXACT_KEYS, *PATTERN_KEYS, "repeats"}
MAX_DIFFERENCES = 10
ONLY_CHECKS = ("fields", "defs")


def _read_schema_document(node: dict) -> dict:
    return (node.get("inputs") or {}).get("schemaDocument") or {}


def _read_output_schema(node: dict) -> dict:
    return _read_schema_document(node).get("outputSchema") or {}


def _list_groups(node: dict) -> dict:
    return _read_output_schema(node).get("properties") or {}


def _find_field_holder(group: dict) -> dict:
    """The part of a group that holds its fields: the group, or its ``items`` for a table."""
    return group if "properties" in group else group.get("items") or {}


def _list_fields(node: dict) -> list[tuple[str, str, dict]]:
    """``(group, field, spec)`` for every field, in plain and table groups."""
    return [
        (group, name, field)
        for group, spec in _list_groups(node).items()
        for name, field in (_find_field_holder(spec).get("properties") or {}).items()
    ]


def _get_field_type(field: dict) -> str:
    return field.get("$ref", "").rsplit("/", 1)[-1] or "no type"


def _is_repeating(group: dict) -> bool:
    kind = group.get("type")
    return "array" in (kind if isinstance(kind, list) else [kind])


def _fits(want: dict, group: str, name: str, field: dict, repeats: bool) -> bool:
    instructions = field.get("description") or ""
    exact = {
        "name": name,
        "group": group,
        "type": _get_field_type(field),
        "instructions": instructions,
        "id": field.get("x-uipath-field-id"),
    }
    searched = {"name_matches": name, "group_matches": group, "instructions_matches": instructions}
    if any(k in want and want[k] != exact[k] for k in EXACT_KEYS):
        return False
    if "repeats" in want and want["repeats"] != repeats:
        return False
    return not any(k in want and not re.search(want[k], searched[k], re.IGNORECASE) for k in PATTERN_KEYS)


def _describe(group: str, name: str, field: dict) -> str:
    field_id = field.get("x-uipath-field-id") or "none"
    return f"'{group} > {name}' {_get_field_type(field)} id {field_id} {(field.get('description') or '')!r}"


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
            or not all(isinstance(v, bool) if k == "repeats" else isinstance(v, str) for k, v in want.items())
        ):
            raise ValueError(
                f"each entry has string {', '.join(sorted(FIELD_KEYS - {'repeats'}))} keys"
                f" and a true/false repeats key, not {json.dumps(want)}"
            )
        for key in PATTERN_KEYS:
            if key in want:
                try:
                    re.compile(want[key])
                except re.error as exc:
                    raise ValueError(f"{key} {want[key]!r} is not a valid pattern ({exc})") from None
    return wanted


def check_fields(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    fields = _list_fields(node)
    groups = _list_groups(node)
    unclaimed = list(range(len(fields)))
    problems = []
    for want in args.wanted:
        claim = next((i for i in unclaimed if _fits(want, *fields[i], _is_repeating(groups[fields[i][0]]))), None)
        if claim is None:
            problems.append(f"no field left fits {json.dumps(want)}")
        else:
            unclaimed.remove(claim)
    if args.only:
        problems += [f"'{fields[i][0]} > {fields[i][1]}' is a field no entry asks for" for i in unclaimed]
    if not problems:
        return None
    found = "; ".join(_describe(*entry) for entry in fields)
    return "; ".join(problems) + f" (the taxonomy has: {found or 'no fields'})"


def check_has_instructions(_: dict, node: dict, __: argparse.Namespace) -> str | None:
    problems = []
    if not _read_schema_document(node).get("prompt"):
        problems.append("the overall prompt is empty")
    problems += [f"group {g!r} has no description" for g, s in _list_groups(node).items() if not s.get("description")]
    problems += [f"field '{g} > {n}' has no description" for g, n, f in _list_fields(node) if not f.get("description")]
    return "; ".join(problems) or None


def check_defs(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    defs = _read_output_schema(node).get("$defs") or {}
    problems = [f"$defs is missing {t} (has: {', '.join(defs) or 'none'})" for t in BUILT_IN_TYPES if t not in defs]
    if args.only:
        problems += [f"$defs also has {k}, which is not a built-in field type" for k in defs if k not in BUILT_IN_TYPES]
    return "; ".join(problems) or None


def _rename_field(node: dict, old: str, new: str) -> bool:
    """Rename field ``old`` to ``new`` in place, in its group's properties and required list."""
    for spec in _list_groups(node).values():
        holder = _find_field_holder(spec)
        props = holder.get("properties") or {}
        if old in props:
            holder["properties"] = {new if k == old else k: v for k, v in props.items()}
            if isinstance(holder.get("required"), list):
                holder["required"] = [new if k == old else k for k in holder["required"]]
            return True
    return False


def _find_differences(want: object, got: object, path: str = "", grow: bool = False) -> list[str]:
    """Each JSON path where ``got`` differs from ``want``; ``required`` lists compare as sets.

    With ``grow``, ``got`` may add keys to a ``properties`` map (new groups and
    fields) or to ``$defs`` (a new Choice), names to a ``required`` list, or a
    ``required`` list where there was none.
    """
    if isinstance(want, dict) and isinstance(got, dict):
        found = []
        for key in sorted(set(want) | set(got)):
            where = f"{path}.{key}" if path else key
            if key not in got:
                found.append(f"{where} was dropped")
            elif key not in want:
                if not (grow and (path.endswith(("properties", "$defs")) or key == "required")):
                    found.append(f"{where} was added: {json.dumps(got[key])[:80]}")
            else:
                found += _find_differences(want[key], got[key], where, grow)
        return found
    if path.endswith(".required") and isinstance(want, list) and isinstance(got, list):
        if grow:
            lost = sorted(set(map(str, want)) - set(map(str, got)))
            return [f"{path} lost {json.dumps(lost)[:80]}"] if lost else []
        want, got = sorted(map(str, want)), sorted(map(str, got))
    if want == got:
        return []
    return [f"{path} was {json.dumps(want)[:80]}, now {json.dumps(got)[:80]}"]


def _read_extract_node(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        flow = json.load(fh)
    node = next((n for n in flow.get("nodes") or [] if n.get("type") == EXTRACT_NODE_TYPE), None)
    if node is None:
        raise SystemExit(f"FAIL: no Extract document node in the original {path}")
    return node


def check_unchanged(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    original, *renames = args.values
    expected = _read_extract_node(original)
    for rename in renames:
        old, new = rename.split("=", 1)
        if not _rename_field(expected, old, new):
            raise SystemExit(f"FAIL: the original taxonomy has no field named {old!r}")
    return _report_differences(_find_differences(_read_schema_document(expected), _read_schema_document(node)))


def check_extends(_: dict, node: dict, args: argparse.Namespace) -> str | None:
    expected = _read_schema_document(_read_extract_node(args.values[0]))
    got = _read_schema_document(node)
    return _report_differences(_find_differences(
        {k: v for k, v in expected.items() if k != "prompt"},
        {k: v for k, v in got.items() if k != "prompt"},
        grow=True,
    ))


def _report_differences(found: list[str]) -> str | None:
    if not found:
        return None
    more = f"; and {len(found) - MAX_DIFFERENCES} more" if len(found) > MAX_DIFFERENCES else ""
    return "the taxonomy differs from the original: " + "; ".join(found[:MAX_DIFFERENCES]) + more


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
    "has-instructions": check_has_instructions,
    "defs": check_defs,
    "unchanged": check_unchanged,
    "extends": check_extends,
    "file-ref": check_file_ref,
    "edge": check_edge,
    "no-other-ixp": check_no_other_ixp,
}


def _find_usage_error(args: argparse.Namespace) -> str | None:
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
    elif args.check == "unchanged":
        if not args.values or not all(re.fullmatch(r"[^=]+=[^=]+", v) for v in args.values[1:]):
            return "unchanged takes: ORIGINAL [OLD=NEW ...]"
    elif args.check == "extends":
        if len(args.values) != 1:
            return "extends takes: ORIGINAL"
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

    usage = _find_usage_error(args)
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
