#!/usr/bin/env python3
"""Verify a deterministic path-parameter value is wired into the BPMN (path_params.yaml).

Ported from Flow `connector_features/check_path_param_value.py`: same
scenario (the Jira issue key ``ENGCE-00000`` must be wired into a real
path-parameter, not just mentioned in the prompt echo), translated from a
JSON `inputs.detail` walk to an XML walk over the registry-driven
`Intsvc.*` connector shell (see skills/uipath-maestro-bpmn/references/
registry-workflow.md §3 "Connector enrichment").

Flow looked in exactly two places: a node's `pathParameters` dict values
(exact match) or its `url`/`endpoint` string (substring match). The BPMN
homes are a `target="path"` input (exact) and a url/path/endpoint field
(substring). A query or body value is not a path parameter.

Assertion map (Flow -> BPMN):
  F check_path_param_value.py:87-91  pathParameters dict value == needle   -> path_input_match(): a
    (exact match)                                                             target="path" input whose value
                                                                                equals needle
  F check_path_param_value.py:92-95  url/endpoint substring match          -> context_field_match(): any "url"/
                                                                                "path"/"endpoint" context field
                                                                                containing needle, checked on every
                                                                                connector/HTTP node
  I             locate/parse .bpmn                                         -> parse_bpmn(name_hint)
  T             collect uipath:input elements at any depth under the node -> context_inputs() (bpmn_check) used by
                                                                                every match function above

No Flow assertions dropped: both of Flow's two search locations (path-param
values, url/endpoint) have a BPMN counterpart above.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_path_param_value.py <NAME_HINT> <expected_value>
"""

from __future__ import annotations

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


def path_input_match(node: ET.Element, needle: str) -> str | None:
    node_id = node.attrib.get("id", "<unknown>")
    for inp in context_inputs(node):
        if inp.attrib.get("target") != "path":
            continue
        value = (inp.attrib.get("value") or inp.text or "").strip()
        if value == needle:
            name = inp.attrib.get("name") or "?"
            return f"path input {name!r} of node {node_id!r}"
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


def find_needle(root: ET.Element, needle: str) -> str | None:
    candidates = [node for tag in CANDIDATE_TAGS for node in elements(root, tag)]
    for node in candidates:
        for matcher in (path_input_match, context_field_match):
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
            f"{needle!r} not found in any node's path input or url/path/endpoint "
            f"context field in {path}"
        )
    print(f"OK: {needle!r} found in {location}")


if __name__ == "__main__":
    main()
