#!/usr/bin/env python3
"""Runtime check for the live BPMN debug e2e.

Grades the agent's saved debug evidence — the raw CLI output of a real
`uip maestro bpmn debug` session and the following `debug-instance variables-all`
read. Un-fakeable in combination with the task's command_executed criteria: the
debug command must actually have run and reached finalStatus Completed, and the
inspected runtime variables must carry the deterministic computed product (42)
on the runtime variable named/id'd `product`. Also confirms the process computes
the result in a script task and maps the script return through the supported
BPMN.ScriptTask output contract.

Reads:
  - debug-evidence/*.json  (agent-saved raw CLI JSON: debug + variables)
  - the authored .bpmn      (must contain a mapped scriptTask)

Exits 0 with OK lines on success; non-zero with FAIL on the first problem.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

EXPECTED_PRODUCT = 42
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.com/schema/bpmn"
NS = {"bpmn": BPMN_NS, "uipath": UIPATH_NS}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _parse_json_tolerant(text: str):
    """Parse JSON, tolerating a leading CLI banner before the first object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("{") or s.startswith("["):
                try:
                    return json.loads("\n".join(lines[i:]))
                except json.JSONDecodeError:
                    continue
    return None


def _walk(obj):
    """Yield every (key, value) pair and every scalar leaf in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield ("__key__", k, v)
            yield from _walk(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _walk(item)
    else:
        yield ("__leaf__", None, obj)


def _walk_paths(obj, path=()):
    """Yield (path, value) for every node in a nested JSON-like structure."""
    yield (path, obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _walk_paths(value, (*path, str(key)))
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            yield from _walk_paths(value, (*path, str(index)))


def _has_final_status_completed(parsed) -> bool:
    for tag, key, val in _walk(parsed):
        if tag == "__key__" and isinstance(key, str) and key.lower() == "finalstatus":
            if isinstance(val, str) and val.strip().lower() == "completed":
                return True
    return False


def _is_expected_product_value(value) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value == EXPECTED_PRODUCT
    if isinstance(value, str):
        return value.strip() in ("42", "42.0")
    return False


def _has_expected_product(parsed) -> bool:
    """Find value 42 specifically attached to a runtime variable named product."""
    product_record_keys = {
        "product",
        "globals.product",
        "variables.product",
        "root.product",
    }
    name_keys = {"id", "name", "key", "variable", "variableid", "variablename", "path"}
    value_keys = {"value", "currentvalue", "runtimevalue", "rawvalue"}

    for path, value in _walk_paths(parsed):
        normalized_path = ".".join(p.lower() for p in path)
        if normalized_path in product_record_keys and _is_expected_product_value(value):
            return True
        if path and path[-1].lower() == "product" and _is_expected_product_value(value):
            return True
        if (
            path
            and path[-1].lower() == "product"
            and isinstance(value, dict)
            and any(_is_expected_product_value(leaf) for _, leaf in _walk_paths(value))
        ):
            return True

        if not isinstance(value, dict):
            continue

        names = {
            str(record_value).strip().lower()
            for record_key, record_value in value.items()
            if record_key.replace("_", "").lower() in name_keys
            and isinstance(record_value, (str, int, float))
        }
        if not (names & product_record_keys or "product" in names):
            continue

        for record_key, record_value in value.items():
            if record_key.replace("_", "").lower() in value_keys and _is_expected_product_value(record_value):
                return True
        if any(_is_expected_product_value(leaf) for _, leaf in _walk_paths(value)):
            return True
    return False


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


def _strip_js_comments(script: str) -> str:
    script = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)
    return re.sub(r"//.*", "", script)


def _root_product_variable(root: ET.Element) -> ET.Element | None:
    process = root.find("bpmn:process", NS)
    if process is None:
        return None
    for variable in process.findall("bpmn:extensionElements/uipath:variables/*", NS):
        local_name = variable.tag.rsplit("}", 1)[-1]
        if (
            local_name == "inputOutput"
            and variable.attrib.get("id") == "product"
            and variable.attrib.get("name") == "product"
        ):
            return variable
    return None


def _script_maps_product(root: ET.Element) -> bool:
    for task in root.findall(f".//{{{BPMN_NS}}}scriptTask"):
        script_format = task.attrib.get("scriptFormat", "")
        if script_format.lower() != "javascript":
            continue
        version = task.find("bpmn:extensionElements/uipath:scriptVersion", NS)
        if version is None or version.attrib.get("value") != "v3":
            continue
        mapping_type = task.find("bpmn:extensionElements/uipath:mapping/uipath:type", NS)
        if mapping_type is None or mapping_type.attrib.get("value") != "BPMN.ScriptTask":
            continue
        outputs = task.findall("bpmn:extensionElements/uipath:mapping/uipath:output", NS)
        if not any(
            output.attrib.get("var") == "product"
            and output.attrib.get("source") == "=result.response"
            for output in outputs
        ):
            continue
        body = _strip_js_comments(_text(task.find("bpmn:script", NS)))
        if "Globals." in body or "vars." in body:
            _fail("script body tries to mutate/read process variables directly; use output mapping")
        if not ("return" in body and "response" in body and "6" in body and "7" in body and "*" in body):
            _fail("script body should compute 6 * 7 and return it as { response: ... }")
        return True
    return False


def main() -> None:
    evidence = glob.glob("debug-evidence/**/*.json", recursive=True)
    if not evidence:
        _fail("no debug-evidence/*.json files found — the agent did not save raw CLI output")

    parsed_files = {}
    for path in evidence:
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError as exc:
            _fail(f"could not read {path}: {exc}")
        parsed = _parse_json_tolerant(text)
        if parsed is None:
            _fail(f"debug evidence file is not valid JSON: {path}")
        parsed_files[path] = parsed

    if not any(_has_final_status_completed(p) for p in parsed_files.values()):
        _fail(
            "no finalStatus == 'Completed' in any debug-evidence file — the debug "
            f"run did not complete. Files: {sorted(parsed_files)}"
        )
    print("OK: debug session reached finalStatus Completed")

    if not any(_has_expected_product(p) for p in parsed_files.values()):
        _fail(
            f"expected runtime variable 'product' with value {EXPECTED_PRODUCT} not "
            f"found in debug-evidence. Files: {sorted(parsed_files)}"
        )
    print(f"OK: runtime product variable is {EXPECTED_PRODUCT}")

    bpmn_files = glob.glob("**/*.bpmn", recursive=True)
    if not bpmn_files:
        _fail("no .bpmn file authored")
    found_script_mapping = False
    found_product_variable = False
    for path in bpmn_files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            _fail(f"{path} is not well-formed XML: {exc}")
        found_product_variable = found_product_variable or _root_product_variable(root) is not None
        found_script_mapping = found_script_mapping or _script_maps_product(root)
    if not found_product_variable:
        _fail("no root inputOutput variable with id='product' and name='product'")
    if not found_script_mapping:
        _fail(
            "no BPMN.ScriptTask output mapping writes source='=result.response' "
            "to var='product'"
        )
    print("OK: product is computed by a script task output mapping")
    print("PASS: all live-debug checks passed")


if __name__ == "__main__":
    main()
