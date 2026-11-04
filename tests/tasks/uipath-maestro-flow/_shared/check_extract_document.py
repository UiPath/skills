#!/usr/bin/env python3
"""Grade an Extract document node through the ``uip maestro flow`` CLI.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_extract_document.py --flow <NAME> <CHECK> [--only] [VALUE ...]

``--flow NAME`` selects the discovered ``NAME.flow`` (discovery is
:func:`flow_check.find_flow_files`, as in ``flow_contains.py --flow-name``).
The node under test is the first ``uipath.ixp.extract-document-builder`` node
that ``nodes list`` reports. Its taxonomy is read with ``nodes schema get``.

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
    node                 the flow holds an Extract document node
    no-other-ixp         no other uipath.ixp.* node: no published model, no
                         processor, no second Extract document node
    file-ref             the node's fileRef reads a file input that
                         ``variables list`` reports (fileRef is read from the
                         .flow, since no CLI verb prints node inputs)
    edge in|out PORT     an edge enters or leaves the node on PORT
    label                the node's label is not the default "Extract document"
    no-model             no modelName, folderKey or processorKey value in the flow
    no-sdk               no .flow-sdk/ directory beside the flow
    validate             ``flow validate`` passes with no warnings

Exit 0 and ``OK: ...`` on stdout when the check holds. Otherwise exit 1 and
one ``FAIL: ...`` line per problem on stderr, naming what was found instead.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from functools import cached_property

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
DEFAULT_LABEL = re.compile(r"extract( document)?", re.IGNORECASE)
MODEL_IDENTITY = re.compile(r'"(modelName|folderKey|processorKey)"\s*:\s*"[^"]')
VALIDATE_TIMEOUT_SECONDS = 150
FIELD_KEYS = {"name", "type", "says", "group", "id", "repeats"}
PATTERN_KEYS = ("name", "says", "group")
ONLY_CHECKS = ("fields", "defs")


class CheckError(Exception):
    """A precondition failed, so the check cannot run."""


def uip(*args: str, timeout: int = 60) -> dict:
    """Run ``uip <args> --output json`` and return its ``Data``."""
    exe = shutil.which("uip")
    if exe is None:
        raise CheckError("uip is not on PATH")
    command = "uip " + " ".join(args)
    try:
        proc = subprocess.run(
            [exe, *args, "--output", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CheckError(f"{command} did not finish within {timeout}s") from None
    try:
        envelope = json.loads(proc.stdout)
    except ValueError:
        raise CheckError(
            f"{command} printed no JSON (exit {proc.returncode}): "
            f"{(proc.stdout or proc.stderr).strip()[:500]}"
        ) from None
    if envelope.get("Result") != "Success":
        detail = " ".join(
            str(envelope[k]) for k in ("Message", "Instructions") if envelope.get(k)
        )
        raise CheckError(f"{command} failed: {detail or envelope}")
    return envelope.get("Data") or {}


class Flow:
    """The flow under test, its Extract document node and that node's taxonomy."""

    def __init__(self, name: str):
        try:
            flows = find_flow_files()
        except SystemExit as exc:
            raise CheckError(str(exc)) from None
        matches = [p for p in flows if os.path.basename(p) == f"{name}.flow"]
        if not matches:
            found = ", ".join(flows) or "none"
            raise CheckError(f"no discovered .flow file is named {name}.flow (found: {found})")
        self.path = matches[0]

    @cached_property
    def nodes(self) -> list[dict]:
        return uip("maestro", "flow", "nodes", "list", self.path).get("Nodes") or []

    @cached_property
    def node(self) -> dict:
        for node in self.nodes:
            if node.get("Type") == EXTRACT_NODE_TYPE:
                return node
        types = ", ".join(n.get("Type", "?") for n in self.nodes) or "none"
        raise CheckError(f"no Extract document node in {self.path} (node types: {types})")

    @cached_property
    def schema(self) -> dict:
        data = uip(
            "maestro", "flow", "nodes", "schema", "get", self.path,
            "--node-id", self.node["Id"],
        )
        return data.get("Schema") or {}

    @cached_property
    def groups(self) -> dict:
        return (self.schema.get("outputSchema") or {}).get("properties") or {}

    @cached_property
    def fields(self) -> list[tuple[str, str, dict, bool]]:
        """``(group, field, spec, repeats)`` for every field, in plain and table groups."""
        result = []
        for group, spec in self.groups.items():
            props = spec.get("properties") or (spec.get("items") or {}).get("properties") or {}
            result.extend((group, name, field, _repeats(spec)) for name, field in props.items())
        return result


def _repeats(group: dict) -> bool:
    kind = group.get("type")
    return "array" in (kind if isinstance(kind, list) else [kind])


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
    if "repeats" in want and want["repeats"] != repeats:
        return False
    return True


def _describe(group: str, name: str, field: dict, repeats: bool) -> str:
    table = " (repeats)" if repeats else ""
    field_id = field.get("x-uipath-field-id") or "none"
    return f"'{group} > {name}'{table} {_type(field)} id {field_id} {(field.get('description') or '')!r}"


def _match(wanted: list[dict], fields: list[tuple[str, str, dict, bool]]) -> tuple[list[dict], set[int]]:
    """Give each wanted entry a different field.

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


def parse_fields(text: str) -> list[dict]:
    """Read the ``fields`` value; raise ValueError when it is malformed."""
    try:
        wanted = json.loads(text)
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


def check_fields(flow: Flow, args: argparse.Namespace) -> list[str]:
    problems = []
    missing, used = _match(args.wanted, flow.fields)
    for want in missing:
        fitting = [f"{g} > {n}" for g, n, f, r in flow.fields if _fits(want, g, n, f, r)]
        if fitting:
            problems.append(f"{json.dumps(want)} fits only {fitting}, already used by another entry")
        else:
            problems.append(f"no field fits {json.dumps(want)}")
    if args.only:
        problems += [
            f"'{g} > {n}' is a field no entry asks for"
            for i, (g, n, _, _) in enumerate(flow.fields)
            if i not in used
        ]
    if problems:
        found = "; ".join(_describe(*entry) for entry in flow.fields)
        problems.append(f"the taxonomy has: {found or 'no fields'}")
    return problems


def check_described(flow: Flow, _: argparse.Namespace) -> list[str]:
    problems = []
    if not flow.schema.get("prompt"):
        problems.append("the overall prompt is empty")
    problems += [f"group {g!r} has no description" for g, s in flow.groups.items() if not s.get("description")]
    problems += [f"field '{g} > {n}' has no description" for g, n, f, _ in flow.fields if not f.get("description")]
    return problems


def check_defs(flow: Flow, args: argparse.Namespace) -> list[str]:
    defs = (flow.schema.get("outputSchema") or {}).get("$defs") or {}
    problems = [f"$defs is missing {t} (has: {', '.join(defs) or 'none'})" for t in BUILT_IN_TYPES if t not in defs]
    if args.only:
        problems += [f"$defs also has {k}, which is not a built-in field type" for k in defs if k not in BUILT_IN_TYPES]
    return problems


def check_node(flow: Flow, _: argparse.Namespace) -> list[str]:
    flow.node  # raises CheckError when there is none
    return []


def check_no_other_ixp(flow: Flow, _: argparse.Namespace) -> list[str]:
    under_test = flow.node["Id"]
    return [
        f"{n.get('Id')} is a {n.get('Type')} node"
        for n in flow.nodes
        if (n.get("Type") or "").startswith(IXP_NODE_PREFIX) and n.get("Id") != under_test
    ]


def _expression(value: object) -> str:
    """The ``$vars`` expression of a ``=js:`` string or a ``jsExpression`` object."""
    if isinstance(value, dict):
        value = value.get("expression") if value.get("type") == "jsExpression" else None
    if not isinstance(value, str):
        return ""
    return value.strip().removeprefix("=js:").strip()


def check_file_ref(flow: Flow, _: argparse.Namespace) -> list[str]:
    node_id = flow.node["Id"]
    with open(flow.path, encoding="utf-8") as fh:
        instances = json.load(fh).get("nodes") or []
    inputs = next((n.get("inputs") or {} for n in instances if n.get("id") == node_id), {})
    if "fileRef" not in inputs:
        return [f"{node_id} has no inputs.fileRef"]
    variables = uip("maestro", "flow", "variables", "list", flow.path).get("Variables") or []
    declared = [
        f"$vars.{v.get('TriggerNodeId')}.output.{v.get('Id')}"
        for v in variables
        if v.get("Direction") == "in" and v.get("Type") == "file"
    ]
    if _expression(inputs["fileRef"]) in declared:
        return []
    return [
        f"fileRef is {json.dumps(inputs['fileRef'])}, which reads no declared file input "
        f"(file inputs: {', '.join(declared) or 'none'})"
    ]


def check_edge(flow: Flow, args: argparse.Namespace) -> list[str]:
    values = args.values
    if len(values) != 2 or values[0] not in ("in", "out"):
        raise CheckError("edge takes: in|out PORT")
    direction, port = values
    end, key = ("Target", "Source") if direction == "in" else ("Source", "Target")
    handle = f"{flow.node['Id']}:{port}"
    edges = uip("maestro", "flow", "edges", "list", flow.path).get("Edges") or []
    if any(e.get(end) == handle for e in edges):
        return []
    found = ", ".join(f"{e.get('Source')} -> {e.get('Target')}" for e in edges) or "none"
    return [f"no edge {'into' if direction == 'in' else 'out of'} {handle} (edges: {found})"]


def check_label(flow: Flow, _: argparse.Namespace) -> list[str]:
    label = (flow.node.get("Label") or "").strip()
    if not label or DEFAULT_LABEL.fullmatch(label):
        return [f"the node's label is {label!r}, not one that says what it extracts"]
    return []


def check_no_model(flow: Flow, _: argparse.Namespace) -> list[str]:
    with open(flow.path, encoding="utf-8") as fh:
        hits = sorted({m.group(1) for m in MODEL_IDENTITY.finditer(fh.read())})
    return [f"{flow.path} sets {key}" for key in hits]


def check_no_sdk(flow: Flow, _: argparse.Namespace) -> list[str]:
    sdk = os.path.join(os.path.dirname(flow.path), ".flow-sdk")
    return [f"{sdk} exists"] if os.path.isdir(sdk) else []


def check_validate(flow: Flow, _: argparse.Namespace) -> list[str]:
    data = uip("maestro", "flow", "validate", flow.path, timeout=VALIDATE_TIMEOUT_SECONDS)
    warnings = data.get("Warnings")
    return [f"flow validate reported warnings: {json.dumps(warnings)}"] if warnings is not None else []


CHECKS = {
    "fields": (check_fields, True),
    "described": (check_described, False),
    "defs": (check_defs, False),
    "node": (check_node, False),
    "no-other-ixp": (check_no_other_ixp, False),
    "file-ref": (check_file_ref, False),
    "edge": (check_edge, True),
    "label": (check_label, False),
    "no-model": (check_no_model, False),
    "no-sdk": (check_no_sdk, False),
    "validate": (check_validate, False),
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--flow", required=True, help="flow name, without .flow")
    parser.add_argument("--only", action="store_true", help="fields, defs: and nothing else")
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("values", nargs="*")
    args = parser.parse_args(argv)

    run, takes_values = CHECKS[args.check]
    if takes_values != bool(args.values):
        need = "needs values" if takes_values else "takes no values"
        print(f"FAIL: {args.check} {need}", file=sys.stderr)
        return 2
    if args.only and args.check not in ONLY_CHECKS:
        print(f"FAIL: --only applies to {' and '.join(ONLY_CHECKS)}, not {args.check}", file=sys.stderr)
        return 2
    if args.check == "fields":
        try:
            if len(args.values) != 1:
                raise ValueError("fields takes one JSON array; quote it")
            args.wanted = parse_fields(args.values[0])
        except ValueError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 2
    try:
        problems = run(Flow(args.flow), args)
    except CheckError as exc:
        problems = [str(exc)]
    for problem in problems:
        print(f"FAIL: {args.check}: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"OK: {args.check}{' --only' if args.only else ''} {' '.join(args.values)}".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
