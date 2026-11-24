#!/usr/bin/env python3
"""Behaviour criterion: the deployed process runs from the seeded folder and
the deployed agent it calls answers.

Picks fresh inputs now (two numbers and a first name with an unambiguous
gender), starts the process deployed in `<parentFolderPath>/<folderName>`, and
requires a clean completion with `sum` = a + b, `gender` = the expected value
and a non-empty `reason`. The agent-job node's own runtime Outputs must hold
that gender and not the other one, and the process `reason` must be one of
their strings, so a script or a constant cannot stand in for the agent. A job
of the folder's Agent process must also have succeeded during the run.
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

from _shared.bpmn_assertions import activity_type  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    debug_evidence,
    element_output_records,
    fetch_asset,
    get_ci,
    named_values,
    payload_data,
    require_clean_run,
    run_cli,
    run_deployed,
    value_leaves,
)

AGENT_JOB_TYPE = "Orchestrator.StartAgentJob"
NAMES = {
    "female": ("Maria", "Olivia", "Sophia", "Emma", "Isabella"),
    "male": ("James", "Michael", "David", "Robert", "William"),
}
OTHER_GENDER = {"female": "male", "male": "female"}
LABELS = {"male", "female", "unknown"}
LIST_TIMEOUT = 60


def process_element(bpmn_xml: str) -> ET.Element:
    process = ET.fromstring(bpmn_xml.encode("utf-8")).find(f"{{{BPMN_NS}}}process")
    if process is None:
        raise CheckFailure("the deployed BPMN has no bpmn:process")
    return process


def agent_job_ids(process: ET.Element) -> list[str]:
    return [
        task.attrib["id"]
        for task in process.iter(f"{{{BPMN_NS}}}serviceTask")
        if task.attrib.get("id") and activity_type(task) == AGENT_JOB_TYPE
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


def squash(text: str) -> str:
    return " ".join(text.split()).casefold()


def assert_agent_provenance(process: ET.Element, variables: Any, gender: str) -> None:
    node_ids = agent_job_ids(process)
    if not node_ids:
        raise CheckFailure(f"no serviceTask uses {AGENT_JOB_TYPE}; the agent is never called")
    records = element_output_records(variables, tuple(node_ids))
    leaves = {squash(leaf) for record in records for leaf in string_leaves(record)}
    if gender not in leaves:
        raise CheckFailure(
            f"agent-job node(s) {node_ids} produced no {gender!r} in their own Outputs: {records!r}"
        )
    if OTHER_GENDER[gender] in leaves:
        raise CheckFailure(
            f"agent-job node(s) {node_ids} hold both {gender!r} and {OTHER_GENDER[gender]!r}, "
            f"so their Outputs do not decide the gender: {records!r}"
        )
    agent_text = leaves - LABELS
    reasons = [squash(v) for v in named_values(process, variables, "reason") if isinstance(v, str)]
    if not any(reason in agent_text for reason in reasons):
        raise CheckFailure(
            f"output `reason` {reasons!r} is not a string the agent-job node returned: {records!r}"
        )


def agent_release_keys(rows: list[Any]) -> set[str]:
    return {
        str(get_ci(row, "Key")).casefold()
        for row in rows
        if str(get_ci(row, "ProcessType", "") or "").casefold() == "agent" and get_ci(row, "Key")
    }


def successful_agent_jobs(jobs: list[Any], release_keys: set[str]) -> list[Any]:
    return [
        job
        for job in jobs
        if str(get_ci(job, "ReleaseKey", "") or "").casefold() in release_keys
        and get_ci(job, "State") == "Successful"
    ]


def assert_agent_job_ran(folder_path: str, since: Any) -> None:
    if not isinstance(since, str) or not since:
        raise CheckFailure("the deployed job has no CreationTime to bound the agent job by")
    _payload, processes = payload_data(
        run_cli(
            ["uip", "or", "processes", "list", "--folder-path", folder_path, "--all-fields", "--limit", "200"],
            timeout=LIST_TIMEOUT,
        ),
        f"processes list in {folder_path}",
    )
    release_keys = agent_release_keys(processes if isinstance(processes, list) else [])
    if not release_keys:
        raise CheckFailure(f"{folder_path} holds no Agent process")
    _payload, jobs = payload_data(
        run_cli(
            ["uip", "or", "jobs", "list", "--folder-path", folder_path, "--created-after", since, "--limit", "50"],
            timeout=LIST_TIMEOUT,
        ),
        f"jobs list in {folder_path}",
    )
    rows = jobs if isinstance(jobs, list) else []
    if not successful_agent_jobs(rows, release_keys):
        seen = [(get_ci(j, "ProcessName"), get_ci(j, "State")) for j in rows]
        raise CheckFailure(
            f"no job of the Agent process in {folder_path} succeeded during the run; jobs since {since}: {seen}"
        )


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    folder_path = f"{seed['parentFolderPath']}/{seed['folderName']}"

    rng = random.SystemRandom()
    a, b = rng.randint(10, 99), rng.randint(10, 99)
    gender = rng.choice(sorted(NAMES))
    name = rng.choice(NAMES[gender])
    print(f"inputs: a={a} b={b} name={name!r} (expected gender {gender!r})")

    try:
        run_data, instance_id, folder_key = run_deployed(
            folder_path, {"a": a, "b": b, "name": name}, Path("deployed_run.log"), timeout=600
        )
        print(f"OK: deployed {run_data['ProcessName']!r} finished in {folder_path} (instance {instance_id})")
        evidence = debug_evidence(instance_id, folder_key)
        require_clean_run(run_data, evidence)
        process = process_element(fetch_asset(instance_id, folder_key))
        assert_outputs(process, evidence.variables, a, b, gender)
        print("OK: sum, gender and reason are correct")
        assert_agent_provenance(process, evidence.variables, gender)
        print("OK: the agent-job node produced the gender and the reason")
        assert_agent_job_ran(folder_path, run_data["CreationTime"])
        print(f"OK: the Agent process in {folder_path} ran during the run")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
    print("PASS")


if __name__ == "__main__":
    main()
