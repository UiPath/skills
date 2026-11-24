#!/usr/bin/env python3
"""Behaviour criterion: the deployed process runs from the seeded folder and
the deployed agent it calls answers.

Picks fresh inputs now (two numbers and a first name with an unambiguous
gender), starts the process deployed in `<parentFolderPath>/<folderName>`, and
requires a clean completion with `sum` = a + b, `gender` = the expected value
and a non-empty `reason`. One run of the agent-job node must return exactly
that label (no other of male/female/unknown) together with the process
`reason`, so a script or a constant cannot stand in for the agent. The job
that agent-job node started (its element-execution `JobKey`) must be a
successful job of the seeded folder's Agent process.
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
    fetch_element_executions,
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
    reasons = {squash(v) for v in named_values(process, variables, "reason") if isinstance(v, str)}
    records = element_output_records(variables, tuple(node_ids))
    labels_per_run = []
    for record in records:
        leaves = {squash(leaf) for leaf in string_leaves(record)}
        labels = leaves & LABELS
        if labels == {gender} and reasons & (leaves - LABELS):
            return
        labels_per_run.append(sorted(labels))
    raise CheckFailure(
        f"no run of agent-job node(s) {node_ids} returned exactly the label {gender!r} together with "
        f"the process `reason` {sorted(reasons)!r}; labels per run: {labels_per_run}; Outputs: {records!r}"
    )


def agent_release_keys(rows: list[Any]) -> set[str]:
    return {
        str(get_ci(row, "Key")).casefold()
        for row in rows
        if str(get_ci(row, "ProcessType", "") or "").casefold() == "agent" and get_ci(row, "Key")
    }


def started_job_keys(executions: list[Any], node_ids: list[str]) -> set[str]:
    keys = set()
    for execution in executions:
        if get_ci(execution, "ElementId") not in node_ids:
            continue
        runs = get_ci(execution, "ElementRuns", []) or []
        for item in [execution, *runs]:
            key = get_ci(item, "JobKey") if isinstance(item, dict) else None
            if key:
                keys.add(str(key).casefold())
    return keys


def release_key(job: Any) -> str:
    release = get_ci(job, "Release")
    return str(get_ci(release, "Key", "") or "").casefold() if isinstance(release, dict) else ""


def started_agent_jobs(jobs: list[Any], release_keys: set[str], job_keys: set[str]) -> list[Any]:
    return [
        job
        for job in jobs
        if str(get_ci(job, "Key", "") or "").casefold() in job_keys
        and release_key(job) in release_keys
        and get_ci(job, "State") == "Successful"
    ]


def assert_agent_job_ran(
    folder_path: str, since: Any, process: ET.Element, instance_id: str, folder_key: str
) -> None:
    if not isinstance(since, str) or not since:
        raise CheckFailure("the deployed job has no CreationTime to bound the agent job by")
    node_ids = agent_job_ids(process)
    executions = fetch_element_executions(instance_id, folder_key)
    job_keys = started_job_keys(executions, node_ids)
    if not job_keys:
        mine = [e for e in executions if get_ci(e, "ElementId") in node_ids]
        raise CheckFailure(
            f"agent-job node(s) {node_ids} report no started job in their element executions: "
            f"{json.dumps(mine, default=str)[:3000]}"
        )
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
            [
                "uip", "or", "jobs", "list", "--folder-path", folder_path,
                "--created-after", since, "--all-fields", "--limit", "50",
            ],
            timeout=LIST_TIMEOUT,
        ),
        f"jobs list in {folder_path}",
    )
    rows = jobs if isinstance(jobs, list) else []
    if not started_agent_jobs(rows, release_keys, job_keys):
        seen = [
            (get_ci(j, "Key"), get_ci(j, "ReleaseName"), get_ci(j, "State"), get_ci(j, "ParentJobKey"))
            for j in rows
        ]
        raise CheckFailure(
            f"agent-job node(s) {node_ids} started job(s) {sorted(job_keys)}, none a successful job of the "
            f"Agent process in {folder_path}; jobs there since {since} (key, name, state, parent): {seen}"
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
        assert_agent_job_ran(folder_path, run_data["CreationTime"], process, instance_id, folder_key)
        print(f"OK: the job the agent-job node started is a successful job of {folder_path}'s Agent process")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
    print("PASS")


if __name__ == "__main__":
    main()
