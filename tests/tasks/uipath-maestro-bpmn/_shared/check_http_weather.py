#!/usr/bin/env python3
"""Structural check for the connectionless HTTP weather eval.

Grades that the weather fetch is a bpmn:sendTask carrying the registry
Intsvc.UnifiedHttpRequest wrapper in manual (connectionless) mode — what the
skill's `.http()` writes: a body object with authentication "manual", method GET
and a literal Open-Meteo url — capturing the response into a declared variable.
The older Intsvc.HttpExecution type is not what `.http()` writes, so it does not
pass; the task grades the skill's prescribed form. Mirrors the Flow Open-Meteo test's
discipline (a real activity, not a mock) within the authoring-only BPMN scope.
Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    BodyShapeError,
    body_object,
    elements,
    fail,
    has_type,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

UIPATH_NS = "http://uipath.org/schema/bpmn"
TYPE_TOKEN = "Intsvc.UnifiedHttpRequest"
LEGACY_TOKEN = "Intsvc.HttpExecution"


def variable_ids(root: ET.Element) -> set[str]:
    return {
        v.attrib["id"]
        for v in root.findall(f".//{{{UIPATH_NS}}}variables/*")
        if v.attrib.get("id")
    }


def main() -> None:
    path, root = parse_bpmn("OpenMeteoWeatherHttp")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    if any(has_type(t, LEGACY_TOKEN) for t in elements(root, "sendTask")):
        fail(f"{LEGACY_TOKEN} is not the type the skill's .http() writes; write {TYPE_TOKEN} in manual mode")
    http_tasks = [t for t in elements(root, "sendTask") if has_type(t, TYPE_TOKEN)]
    if not http_tasks:
        fail(f"missing bpmn:sendTask with {TYPE_TOKEN} wrapper")
    task = http_tasks[0]

    for kind in ("serviceTask", "userTask", "scriptTask", "businessRuleTask", "task"):
        if any(has_type(e, TYPE_TOKEN) for e in elements(root, kind)):
            fail(f"{TYPE_TOKEN} used on wrong BPMN wrapper: bpmn:{kind}")

    try:
        body = body_object(task)
    except BodyShapeError as exc:
        fail(f"HTTP request body is not one JSON object: {exc}")

    mode = str(body.get("authentication", "")).lower()
    if mode != "manual":
        fail(f'HTTP node must be connectionless (body authentication "manual"); found {mode!r}')

    method = str(body.get("method", "")).upper()
    if method != "GET":
        fail(f"weather fetch should be a GET; found method={method!r}")

    url = str(body.get("url", ""))
    if "open-meteo" not in url.lower():
        fail(f"url input must target the public Open-Meteo host; found url={url!r}")
    if "=bindings." in url:
        fail("connectionless HTTP url must be a literal, not a connection binding")

    outputs = task.findall(f".//{{{UIPATH_NS}}}output")
    if not outputs:
        fail("HTTP task should capture the response as an output")
    declared = variable_ids(root)
    output_targets = {o.attrib.get("var") or o.attrib.get("target") for o in outputs}
    if not any(t and t in declared for t in output_targets):
        fail(
            f"HTTP response output must bind to a declared variable; "
            f"outputs={sorted(t for t in output_targets if t)} declared={sorted(declared)}"
        )

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} is a connectionless manual GET to Open-Meteo with a bound output")


if __name__ == "__main__":
    main()
