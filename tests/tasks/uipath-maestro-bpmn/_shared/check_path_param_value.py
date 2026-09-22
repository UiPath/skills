#!/usr/bin/env python3
"""Verify a deterministic path-parameter value is wired into the BPMN (path_params.yaml).

Ported from Flow `connector_features/check_path_param_value.py`: same
scenario (the Jira issue key ``ENGCE-00000`` must be wired into a real
path-parameter, not just mentioned in the prompt echo), translated from a
JSON `inputs.detail` walk to an XML walk over the registry-driven
`Intsvc.*` connector shell (see skills/uipath-maestro-bpmn/references/
registry-workflow.md §3 "Connector enrichment").

Flow looked in exactly two places: a node's `pathParameters` dict values
(exact match) or its `url`/`endpoint` string (substring match). BPMN has no
fixed home for a path parameter -- the registry does not pin whether it lands
as a `target="path"` input, a `target="query"` input, inside the single
`target="body"` JSON payload, or embedded in a managed-HTTP node's own
url/path field -- so this checker widens the search to all of those homes
(BATCH1-ADDENDUM "Where connector node values live in BPMN" +
_porting/PORTING-BRIEF.md's `T` translation-tolerance for "entity anywhere in
inputs/objectName/path"). Widening only ever makes an assertion easier to
satisfy, never harder, so this stays within the Normalization pass's
"dropping/widening only" rule.

Assertion map (Flow -> BPMN):
  F check_path_param_value.py:87-91  pathParameters dict value == needle   -> path_or_query_input_match(): any
    (exact match)                                                             target="path"/"query" input whose
                                                                                value/text contains needle
  F check_path_param_value.py:92-95  url/endpoint substring match          -> context_field_match(): any "url"/
                                                                                "path"/"endpoint" context field
                                                                                containing needle, checked on every
                                                                                connector/HTTP node
  I             locate/parse .bpmn                                         -> parse_bpmn(name_hint)
  T             needle searched across path/query/body, not only          -> body_json_match(): the needle also
                pathParameters (widened breadth, kept in scope by the        matched inside the single target="body"
                calling task's instructions)                                 JSON payload, at any nesting depth
  T             collect uipath:input elements at any depth under the node -> context_inputs() (bpmn_check) used by
                                                                                every match function above

No Flow assertions dropped: both of Flow's two search locations (path-param
values, url/endpoint) have a widened BPMN counterpart above; nothing is
required that Flow did not also accept.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_path_param_value.py <NAME_HINT> <expected_value>
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import context_inputs, elements, fail, parse_bpmn  # noqa: E402

CONTEXT_FIELDS = ("url", "path", "endpoint")

# Task-like leaf elements only -- NOT root.iter(), which also yields ancestor
# containers (bpmn:process, bpmn:definitions). An ancestor's serialized
# subtree recursively contains every descendant's inputs, so context_inputs()
# would "find" a match on the ancestor first and report an unhelpful
# "<unknown>" node id instead of the real host element.
CANDIDATE_TAGS = (
    "sendTask",
    "serviceTask",
    "task",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
)


def _flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for v in value.values():
            out.extend(_flatten_strings(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(_flatten_strings(v))
        return out
    return []


def path_or_query_input_match(node: ET.Element, needle: str) -> str | None:
    node_id = node.attrib.get("id", "<unknown>")
    for inp in context_inputs(node):
        if inp.attrib.get("target") not in ("path", "query"):
            continue
        value = (inp.attrib.get("value") or inp.text or "")
        if needle.lower() in value.lower():
            target = inp.attrib.get("target")
            name = inp.attrib.get("name") or "?"
            return f"{target} input {name!r} of node {node_id!r}"
    return None


def context_field_match(node: ET.Element, needle: str) -> str | None:
    node_id = node.attrib.get("id", "<unknown>")
    for inp in context_inputs(node):
        name = inp.attrib.get("name") or ""
        if name.lower() not in CONTEXT_FIELDS:
            continue
        value = (inp.attrib.get("value") or inp.text or "")
        if needle.lower() in value.lower():
            return f"{name} field of node {node_id!r}"
    return None


def body_json_match(node: ET.Element, needle: str) -> str | None:
    node_id = node.attrib.get("id", "<unknown>")
    for inp in context_inputs(node):
        if inp.attrib.get("target") != "body":
            continue
        raw = (inp.text or inp.attrib.get("value") or "").strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for leaf in _flatten_strings(parsed):
            if needle.lower() in leaf.lower():
                return f"body JSON payload of node {node_id!r}"
    return None


def find_needle(root: ET.Element, needle: str) -> str | None:
    candidates = [node for tag in CANDIDATE_TAGS for node in elements(root, tag)]
    for node in candidates:
        for matcher in (path_or_query_input_match, context_field_match, body_json_match):
            location = matcher(node, needle)
            if location is not None:
                return location
    return None


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: check_path_param_value.py <name_hint> <expected_value>")

    name_hint, needle = sys.argv[1], sys.argv[2]
    path, root = parse_bpmn(name_hint)

    location = find_needle(root, needle)
    if location is None:
        fail(
            f"{needle!r} not found in any node's path/query input, url/path/endpoint "
            f"context field, or body JSON payload in {path}"
        )
    print(f"OK: {needle!r} found in {location}")


if __name__ == "__main__":
    main()
