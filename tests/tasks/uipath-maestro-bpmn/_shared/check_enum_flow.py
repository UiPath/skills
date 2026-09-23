#!/usr/bin/env python3
"""Validate the EnumTest BPMN process: structure and enum body-value wiring.

Ported from Flow `connector_features/check_enum_flow.py`: only the
`structure` and `body_params` modes are ported (enum.yaml's own criteria
never call Flow's `control` mode -- that mode grades enhanced_enum's
Decision/Terminate control-flow shape, not enum.yaml's), translated from a
JSON `inputs.detail.bodyParameters` walk to an XML walk over the
registry-driven `Intsvc.*` connector shell (see skills/uipath-maestro-bpmn/
references/registry-workflow.md §3 "Body shape").

registry-workflow.md documents the canonical hand-authored body shape as
exactly ONE `target="body"` input holding the whole request as a JSON CDATA
blob. The CLI manifest's stale `InputNotes`, however, still tell an author to
add one `uipath:input` per request field, and BATCH1-ADDENDUM's own lessons
record agents emitting both shapes for other Intsvc.ActivityExecution
parameters (curated separate path/query inputs vs. one JSON blob). Per this
task's instructions, both body forms are accepted here too: one JSON blob
input, or one typed `target="body"` input per field.

Assertion map (Flow -> BPMN):
  F check_enum_flow.py:39-44  structure: flow exists, valid JSON,          -> check_structure(): locate/parse .bpmn
    has nodes/edges                                                          (translation of "artifact exists and is
                                                                                parseable" to the BPMN artifact shape)
  F check_enum_flow.py:49-52  _EXPECTED_BODY = {"to": ..., "importance":   -> EXPECTED_BODY (kept identical --
    "high"}  (only `to` and `importance` are asserted, despite the           only `to` and `importance`, matching
    docstring's "to/subject/body/importance" -- the code is the source       Flow's actual code, not its stale
    of truth)                                                                 docstring)
  F check_enum_flow.py:63-72  _body_matches(): case-insensitive field      -> body_fields_match(): same
    lookup, `.strip().lower()` value comparison                              case-insensitive compare
  F check_enum_flow.py:76-94  _check_body_params(): scan every node's      -> check_body_params(): scan every node
    inputs.detail.bodyParameters, keep the best (fewest-missing) partial      carrying a target="body" input, keep
    match for the failure message                                            the best (fewest-missing) partial match
  I             locate/parse .bpmn                                        -> parse_bpmn(name_hint)
  T             body read in both forms: one JSON blob, or one typed      -> body_fields(): single JSON-parseable
    input per field (task instruction; mirrors the CLI manifest's stale      target="body" input -> its parsed
    separateInputs InputNotes as a real, if non-canonical, shape)             object; multiple target="body" inputs,
                                                                               each name=field -> {name: value} map
  T             `=`-prefixed expression values pass any type/value check  -> body_fields_match() treats a value
    (grading-contract-wide translation tolerance for expression strings)     starting with "=" as satisfying its
                                                                               expected field unconditionally

No Flow assertions dropped: `structure`'s existence/parse check and
`body_params`'s to/importance field match both have a BPMN counterpart above.
Flow's `control` mode is out of scope (enum.yaml's criteria never call it).

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_enum_flow.py <NAME_HINT> <structure|body_params>
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import body_object, context_inputs, elements, fail, parse_bpmn  # noqa: E402

# Kept identical to Flow's own _EXPECTED_BODY (check_enum_flow.py:49-52): only
# `to` and `importance` are asserted, matching the code, not its docstring.
EXPECTED_BODY = {
    "to": "is-test@uipath.com",
    "importance": "high",  # this is the enum field under test
}

# Task-like leaf elements only -- NOT root.iter(), which also yields ancestor
# containers (bpmn:process, bpmn:definitions). An ancestor's serialized
# subtree recursively contains every descendant's inputs, so scanning it too
# would let unrelated target="body" inputs on different nodes merge into one
# fields map.
CANDIDATE_TAGS = (
    "sendTask",
    "serviceTask",
    "task",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
)


def check_structure(name_hint: str) -> None:
    path, root = parse_bpmn(name_hint)
    tasks = [
        *elements(root, "sendTask"),
        *elements(root, "serviceTask"),
        *elements(root, "task"),
    ]
    print(f"OK: {path} is well-formed BPMN XML with {len(tasks)} task-like node(s)")


def body_fields(node: ET.Element) -> dict[str, str] | None:
    """The node's request body as a field->value map, in either registry form
    (one JSON blob, or one typed input per field), via bpmn_check.body_object;
    None when the node has no target="body" input at all."""
    if not any(inp.attrib.get("target") == "body" for inp in context_inputs(node)):
        return None
    fields = {
        str(k): (v if isinstance(v, str) else json.dumps(v))
        for k, v in body_object(node).items()
    }
    return fields or None


def body_fields_match(fields: dict[str, object]) -> list[str]:
    """Missing/mismatched field descriptions; empty list means OK.

    A value beginning with "=" is an expression (`=vars.X`, `=js:...`) and
    passes unconditionally -- the grading-contract-wide translation tolerance
    for expression strings.
    """
    lowered = {str(k).lower(): v for k, v in fields.items()}
    missing: list[str] = []
    for key, expected in EXPECTED_BODY.items():
        actual = lowered.get(key.lower())
        if actual is None:
            missing.append(f"{key}={expected!r} (missing)")
            continue
        actual_str = str(actual).strip()
        if actual_str.startswith("="):
            continue
        if actual_str.lower() != expected.lower():
            missing.append(f"{key}={expected!r} (got {actual!r})")
    return missing


def check_body_params(name_hint: str) -> None:
    path, root = parse_bpmn(name_hint)
    best_missing: list[str] | None = None
    checked_any = False
    candidates = [node for tag in CANDIDATE_TAGS for node in elements(root, tag)]
    for node in candidates:
        fields = body_fields(node)
        if fields is None:
            continue
        checked_any = True
        missing = body_fields_match(fields)
        if not missing:
            node_id = node.attrib.get("id", "<unknown>")
            print(f"OK: body payload on node {node_id!r} carries expected to/importance")
            return
        if best_missing is None or len(missing) < len(best_missing):
            best_missing = missing

    if not checked_any:
        fail(
            f"No node in {path} has a target=\"body\" input. Hand-authored connector "
            f"nodes must carry either one JSON target=\"body\" input holding the "
            f"whole request object, or one target=\"body\" input per field."
        )
    fail(f"target=\"body\" input found but missing or wrong fields: {best_missing}. BPMN: {path}")


CHECKS = {
    "structure": check_structure,
    "body_params": check_body_params,
}


def main() -> None:
    if len(sys.argv) != 3:
        fail(f"usage: check_enum_flow.py <name_hint> <{'|'.join(CHECKS)}>")
    name_hint, check_name = sys.argv[1], sys.argv[2]
    check = CHECKS.get(check_name)
    if check is None:
        fail(f"unknown check {check_name!r}; expected one of {sorted(CHECKS)}")
    check(name_hint)


if __name__ == "__main__":
    main()
