#!/usr/bin/env python3
"""Behaviour criterion: the deployed process runs from the seeded folder and
the deployed agent it calls answers.

Picks fresh inputs now (two numbers and a first name with an unambiguous
gender), starts the process deployed in `<parentFolderPath>/<folderName>`, and
requires a clean completion with `sum` = a + b, `gender` = the expected value
and a non-empty `reason`. In the deployed BPMN, the end event must publish
`gender` and `reason` straight from variables that only one agent-job node's
response mapping writes, so a script, a literal or a second agent call cannot
stand in. That node must run once, its Outputs must hold the expected label and
an explanation in those two mapped fields, and the one job it started (its
element-execution `JobKey`) must be a successful job of the seeded folder's
Agent process.
"""

from __future__ import annotations

import json
import os
import random
import re
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

from _shared.bpmn_assertions import activity_type, mapping_outputs  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    CheckFailure,
    debug_evidence,
    declarations,
    element_output_records,
    fetch_asset,
    fetch_element_executions,
    get_ci,
    named_values,
    payload_data,
    q,
    require_clean_run,
    run_cli,
    run_deployed,
)

AGENT_JOB_TYPE = "Orchestrator.StartAgentJob"
NAMES = {
    "female": ("Maria", "Olivia", "Sophia", "Emma", "Isabella"),
    "male": ("James", "Michael", "David", "Robert", "William"),
}
LABELS = {"male", "female", "unknown"}
TRACED_OUTPUTS = ("gender", "reason")
FIELDS = r"((?:\??\.[A-Za-z_][A-Za-z0-9_]*)*)"
VARS_SOURCE = re.compile(rf"=(?:js:)?\s*vars\.([A-Za-z_][A-Za-z0-9_]*){FIELDS}\s*;?")
RESULT_SOURCE = re.compile(rf"=(?:js:)?\s*result{FIELDS}\s*;?")
MISSING = object()
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


def field_path(text: str) -> tuple[str, ...]:
    return tuple(part for part in re.split(r"\??\.", text) if part)


def output_writes(process: ET.Element) -> list[tuple[str, ET.Element]]:
    """(owner id, `uipath:output`) for every output mapping in the process."""
    return [
        (element.attrib["id"], output)
        for element in process.iter()
        if element.attrib.get("id")
        for output in mapping_outputs(element)
    ]


def traced_field(process: ET.Element, name: str, agent_ids: list[str]) -> tuple[str, tuple[str, ...]]:
    """(node id, response path) of the agent-job response field the process
    output `name` is published from."""
    output_ids = {
        d.attrib.get("id")
        for d in declarations(process)
        if d.tag == q(UIPATH_NS, "output") and d.attrib.get("name") == name and d.attrib.get("id")
    }
    writes = output_writes(process)
    sources = [out.attrib.get("source", "") for _owner, out in writes if out.attrib.get("var") in output_ids]
    if not sources:
        raise CheckFailure(f"no mapping publishes the process output `{name}`")
    traced = set()
    for source in sources:
        match = VARS_SOURCE.fullmatch(source.strip())
        if match is None:
            raise CheckFailure(f"`{name}` is published from {source!r}, not straight from one variable")
        var, below = match.group(1), field_path(match.group(2))
        var_writes = [(owner, out) for owner, out in writes if out.attrib.get("var") == var]
        owners = sorted({owner for owner, _out in var_writes})
        if len(var_writes) != 1 or owners[0] not in agent_ids:
            raise CheckFailure(
                f"`{name}` is published from vars.{var}, which is written by {owners or 'no element'}; "
                f"it must be written only by the response mapping of an agent-job node {agent_ids}"
            )
        owner, write = var_writes[0]
        node_source = (write.attrib.get("source") or "=result").strip()
        node_match = RESULT_SOURCE.fullmatch(node_source)
        if node_match is None:
            raise CheckFailure(f"vars.{var} takes {node_source!r} on {owner!r}, not a field of the agent's response")
        traced.add((owner, field_path(node_match.group(1)) + below))
    if len(traced) != 1:
        raise CheckFailure(f"`{name}` is published from more than one agent response field: {sorted(traced)}")
    return traced.pop()


def mapped_agent_fields(process: ET.Element) -> tuple[str, dict[str, tuple[str, ...]]]:
    """The one agent-job node `gender` and `reason` are published from, and
    the response path each is read from."""
    agent_ids = agent_job_ids(process)
    if not agent_ids:
        raise CheckFailure(f"no serviceTask uses {AGENT_JOB_TYPE}; the agent is never called")
    traced = {name: traced_field(process, name, agent_ids) for name in TRACED_OUTPUTS}
    nodes = {node for node, _path in traced.values()}
    if len(nodes) != 1:
        sources = {name: node for name, (node, _path) in traced.items()}
        raise CheckFailure(f"`gender` and `reason` come from different agent-job nodes: {sources}")
    paths = {name: path for name, (_node, path) in traced.items()}
    if paths["gender"] == paths["reason"]:
        raise CheckFailure(f"`gender` and `reason` are both published from result.{'.'.join(paths['gender'])}")
    return nodes.pop(), paths


def parsed(value: Any) -> Any:
    if isinstance(value, str) and value.strip()[:1] in ("{", "["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def at_path(value: Any, path: tuple[str, ...]) -> Any:
    """The field at `path` in an agent-job node's Outputs, which hold the
    agent's response itself (`result`)."""
    for key in path:
        value = parsed(value)
        if not isinstance(value, dict):
            return MISSING
        value = get_ci(value, key, MISSING)
        if value is MISSING:
            return MISSING
    return value


def squash(text: str) -> str:
    return " ".join(text.split()).casefold()


def assert_agent_provenance(process: ET.Element, variables: Any, gender: str) -> str:
    node_id, fields = mapped_agent_fields(process)
    records = element_output_records(variables, node_id)
    if len(records) != 1:
        raise CheckFailure(
            f"agent-job node {node_id!r} ran {len(records)} times; the process should call the agent once. "
            f"Outputs: {records!r}"
        )
    record = records[0]
    wanted = {
        "gender": (lambda text: text == gender, f"the label {gender!r}"),
        "reason": (lambda text: bool(text) and text not in LABELS, "an explanation, not empty or only a label"),
    }
    for name, path in fields.items():
        value = at_path(record, path)
        accepts, description = wanted[name]
        if not isinstance(value, str) or not accepts(squash(value)):
            found = "nothing" if value is MISSING else repr(value)
            raise CheckFailure(
                f"process `{name}` is mapped from result.{'.'.join(path)} of agent-job node {node_id!r}, which "
                f"should hold {description}; found {found}; Outputs: {record!r}"
            )
    return f"{node_id!r}: " + ", ".join(f"{name} from result.{'.'.join(path)}" for name, path in fields.items())


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
    node_id, _fields = mapped_agent_fields(process)
    node_ids = [node_id]
    executions = fetch_element_executions(instance_id, folder_key)
    job_keys = started_job_keys(executions, node_ids)
    if not job_keys:
        mine = [e for e in executions if get_ci(e, "ElementId") in node_ids]
        raise CheckFailure(
            f"agent-job node(s) {node_ids} report no started job in their element executions: "
            f"{json.dumps(mine, default=str)[:3000]}"
        )
    if len(job_keys) != 1:
        raise CheckFailure(
            f"agent-job node {node_id!r} started {len(job_keys)} jobs {sorted(job_keys)}; "
            "the process should call the agent once"
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
        traced = assert_agent_provenance(process, evidence.variables, gender)
        print(f"OK: gender and reason are published from one run of agent-job node {traced}")
        assert_agent_job_ran(folder_path, run_data["CreationTime"], process, instance_id, folder_key)
        print(f"OK: the job the agent-job node started is a successful job of {folder_path}'s Agent process")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
    print("PASS")


if __name__ == "__main__":
    main()
