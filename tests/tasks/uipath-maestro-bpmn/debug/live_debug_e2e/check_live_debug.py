#!/usr/bin/env python3
"""Runtime check for the live BPMN debug e2e.

Grades the agent's saved debug evidence — the raw CLI output of a real
`uip maestro bpmn debug` session and the following `debug-instance variables`
read. Un-fakeable in combination with the task's command_executed criteria: the
debug command must actually have run and reached finalStatus Completed, and the
inspected runtime variables must carry the deterministic computed product (42
for inputs a=6, b=7). Also confirms the process computes the result in a script
task rather than hardcoding it.

Reads:
  - debug-evidence/*.json  (agent-saved raw CLI JSON: debug + variables)
  - the authored .bpmn      (must contain a scriptTask)

Exits 0 with OK lines on success; non-zero with FAIL on the first problem.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

EXPECTED_PRODUCT = 42
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


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


def _has_final_status_completed(parsed) -> bool:
    for tag, key, val in _walk(parsed):
        if tag == "__key__" and isinstance(key, str) and key.lower() == "finalstatus":
            if isinstance(val, str) and val.strip().lower() == "completed":
                return True
    return False


def _has_expected_product(parsed) -> bool:
    for tag, _key, val in _walk(parsed):
        if tag != "__leaf__":
            continue
        if isinstance(val, bool):
            continue
        if isinstance(val, (int, float)) and val == EXPECTED_PRODUCT:
            return True
        if isinstance(val, str) and val.strip() in ("42", "42.0"):
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
            f"expected product {EXPECTED_PRODUCT} not found among runtime variable "
            f"values in debug-evidence. Files: {sorted(parsed_files)}"
        )
    print(f"OK: runtime product variable is {EXPECTED_PRODUCT}")

    bpmn_files = glob.glob("**/*.bpmn", recursive=True)
    if not bpmn_files:
        _fail("no .bpmn file authored")
    found_script = False
    for path in bpmn_files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            _fail(f"{path} is not well-formed XML: {exc}")
        if root.findall(f".//{{{BPMN_NS}}}scriptTask"):
            found_script = True
            break
    if not found_script:
        _fail(
            "no scriptTask in any authored .bpmn — the product must be computed by "
            "a script task, not hardcoded"
        )
    print("OK: product is computed by a script task")
    print("PASS: all live-debug checks passed")


if __name__ == "__main__":
    main()
