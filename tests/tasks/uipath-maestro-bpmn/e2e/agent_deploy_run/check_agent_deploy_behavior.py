#!/usr/bin/env python3
"""Behaviour criterion: the process runs live and the agent it calls answers.

Picks fresh inputs now (two numbers and a first name with an unambiguous
gender), runs the submitted process with `uip maestro bpmn debug`, and
requires a clean completion with `sum` = a + b, `gender` = the expected value
and a non-empty `reason`. The expected gender must also appear as a value in
the agent-job node's own runtime Outputs, so a script or a constant cannot
stand in for the agent.
"""

from __future__ import annotations

import json
import os
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
_suite_dir = HERE
while _suite_dir != os.path.dirname(_suite_dir) and not os.path.isdir(
    os.path.join(_suite_dir, "_shared")
):
    _suite_dir = os.path.dirname(_suite_dir)
sys.path.insert(0, _suite_dir)

from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    debug_evidence,
    element_output_records,
    named_values,
    require_clean_run,
    run_debug,
    value_leaves,
)

AGENT_JOB_TYPE = "Orchestrator.StartAgentJob"
EXCLUDED_DIRS = {"node_modules", ".git"}
NAMES = {
    "female": ("Maria", "Olivia", "Sophia", "Emma", "Isabella"),
    "male": ("James", "Michael", "David", "Robert", "William"),
}


def find_bpmn(root: Path) -> Path | None:
    found = sorted(
        (p for p in root.rglob("*.bpmn") if not EXCLUDED_DIRS.intersection(p.parts)),
        key=lambda p: (len(p.parts), str(p)),
    )
    return found[0] if found else None


def process_element(bpmn_path: Path) -> ET.Element:
    process = ET.parse(bpmn_path).getroot().find(f"{{{BPMN_NS}}}process")
    if process is None:
        raise CheckFailure(f"{bpmn_path} has no bpmn:process")
    return process


def agent_job_ids(process: ET.Element) -> list[str]:
    return [
        task.attrib["id"]
        for task in process.iter(f"{{{BPMN_NS}}}serviceTask")
        if task.attrib.get("id") and AGENT_JOB_TYPE in ET.tostring(task, encoding="unicode")
    ]


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def assert_outputs(process: ET.Element, variables: Any, a: int, b: int, gender: str) -> None:
    sums = named_values(process, variables, "sum")
    if not any(as_number(v) == a + b for v in sums):
        raise CheckFailure(f"output `sum` should be {a + b}; runtime values: {sums!r}")

    genders = named_values(process, variables, "gender")
    if not any(isinstance(v, str) and v.strip().casefold() == gender for v in genders):
        raise CheckFailure(f"output `gender` should be {gender!r}; runtime values: {genders!r}")

    reasons = named_values(process, variables, "reason")
    if not any(isinstance(v, str) and v.strip() for v in reasons):
        raise CheckFailure(f"output `reason` is empty; runtime values: {reasons!r}")


def string_leaves(value: Any) -> list[str]:
    """String leaves, descending into strings that hold a JSON object or array."""
    out: list[str] = []
    for leaf in value_leaves(value):
        if not isinstance(leaf, str):
            continue
        text = leaf.strip()
        if text[:1] in ("{", "["):
            try:
                out.extend(string_leaves(json.loads(text)))
                continue
            except json.JSONDecodeError:
                pass
        out.append(leaf)
    return out


def assert_agent_provenance(process: ET.Element, variables: Any, gender: str) -> None:
    node_ids = agent_job_ids(process)
    if not node_ids:
        raise CheckFailure(f"no serviceTask uses {AGENT_JOB_TYPE}; the agent is never called")
    records = element_output_records(variables, tuple(node_ids))
    leaves = [leaf for record in records for leaf in string_leaves(record)]
    if not any(leaf.strip().casefold() == gender for leaf in leaves):
        raise CheckFailure(
            f"agent-job node(s) {node_ids} produced no {gender!r} in their own Outputs: {records!r}"
        )


def main() -> None:
    if not Path("seed.json").is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    bpmn_path = find_bpmn(Path("."))
    if bpmn_path is None:
        raise SystemExit("FAIL: no .bpmn file found")

    rng = random.SystemRandom()
    a, b = rng.randint(10, 99), rng.randint(10, 99)
    gender = rng.choice(sorted(NAMES))
    name = rng.choice(NAMES[gender])
    print(f"inputs: a={a} b={b} name={name!r} (expected gender {gender!r})")

    try:
        process = process_element(bpmn_path)
        debug_data, instance_id = run_debug(
            bpmn_path.parent, {"a": a, "b": b, "name": name}, Path("debug.log"), timeout=600
        )
        print(f"OK: debug finished (instance {instance_id})")
        evidence = debug_evidence(instance_id)
        require_clean_run(debug_data, evidence)
        assert_outputs(process, evidence.variables, a, b, gender)
        print("OK: sum, gender and reason are correct")
        assert_agent_provenance(process, evidence.variables, gender)
        print("OK: the agent-job node produced the gender")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
    print("PASS")


if __name__ == "__main__":
    main()
