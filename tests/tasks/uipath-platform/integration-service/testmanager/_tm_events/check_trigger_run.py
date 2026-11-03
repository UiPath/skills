#!/usr/bin/env python3
"""Grader for Test Manager connector event-trigger e2e tasks (all workflow types).

Modes:
  --artifact <surface>   The authored workflow starts on the TM trigger under test
                         (surface: api-workflow | rpa | bpmn).
  --validate <surface>   The authored workflow passes the surface's offline
                         validator (api-workflow | bpmn).
  --live                 The deployed workflow actually ran on the event: re-queries
                         Orchestrator for a Successful job of seed.json's process,
                         then asserts the payload that job returned carries the
                         entity type, record id, project id and key fields, and that
                         the record id is the record this run created.

Reads seed.json (pre_run) and result.json (agent):
  result.json -> {"connection_id", "project_id", "record_id", "execution_id"?,
                  "created": [{"object", "id"}, ...]}
The job is found independently of anything the agent reports about it.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import NoReturn

CONNECTOR = "uipath-uipath-testmanager"
EVENT_OBJECT = "TestManagerEvents"
NAMED = ("Requirement", "TestCase", "TestSet")
TERMINAL = {
    "passed", "failed", "completed", "cancelled", "canceled",
    "error", "done", "stopped", "faulted", "successful", "partiallypassed", "finished",
}
PROJECT_PARAM = {"Requirement": "ProjectId", "TestCase": "ProjectId", "TestSet": "ProjectId",
                 "TestExecution": "projectId", "TestCaseLog": "projectId"}
ZERO_GUID = "00000000-0000-0000-0000-000000000000"
GUID_RE = re.compile(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")


def fail(msg) -> NoReturn:
    print(f"FAIL: {msg}")
    sys.exit(1)


def load(path, missing):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        fail(missing)
    except ValueError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def get_ci(obj, key):
    if not isinstance(obj, dict):
        return None
    for k, v in obj.items():
        if k.lower() == key.lower():
            return v
    return None


def run_uip(*args, timeout=180):
    cmd = ["uip", *args, "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"`uip {' '.join(args[:4])}` did not complete: {exc}")
    try:
        envelope = json.loads(proc.stdout or "{}")
    except ValueError:
        fail(f"`uip {' '.join(args[:4])}` returned non-JSON (exit {proc.returncode}): {(proc.stdout or proc.stderr)[:300]}")
    if proc.returncode != 0:
        fail(f"`uip {' '.join(args[:4])}` exited {proc.returncode}: {json.dumps(envelope)[:400]}")
    return envelope.get("Data", envelope) if isinstance(envelope, dict) else envelope


def items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "Items", "value", "data", "records"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def walk_dicts(value):
    """Yield every dict nested in value, decoding JSON-encoded strings on the way."""
    if isinstance(value, str):
        text = value.strip()
        if text[:1] in "{[":
            try:
                yield from walk_dicts(json.loads(text))
            except ValueError:
                pass
        return
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk_dicts(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk_dicts(v)


def project_files(pattern):
    return [p for p in glob.glob(pattern, recursive=True)
            if "node_modules" not in p and f"{os.sep}.local{os.sep}" not in p]


# ---------------------------------------------------------------- artifact

def check_api_workflow(seed):
    workflows = [p for p in project_files("**/Workflow.json") if os.path.dirname(p)]
    if not workflows:
        fail("no Workflow.json inside a project folder")
    for path in workflows:
        doc = json.load(open(path, encoding="utf-8"))
        try:
            root = doc["do"][0]
            seq = root[next(iter(root))]["do"]
            first, step = next(iter(seq[0])), seq[1][next(iter(seq[1]))]
        except (KeyError, IndexError, TypeError, StopIteration):
            continue
        if first != "WorkflowStart" or step.get("call") != "UiPath.IntSvcEvent":
            continue
        blob = json.dumps(step).lower()
        if CONNECTOR in blob and EVENT_OBJECT.lower() in blob \
                and seed["operation"].lower() in blob and seed["object_type"].lower() in blob:
            bindings = os.path.join(os.path.dirname(path), "bindings_v2.json")
            if not os.path.exists(bindings):
                fail(f"{bindings} missing — run `uip api-workflow bindings sync`; without it a deploy never subscribes")
            triggers = [r for r in json.load(open(bindings, encoding="utf-8")).get("resources", [])
                        if r.get("resource") == "EventTrigger"]
            if len(triggers) != 1:
                fail(f"bindings_v2.json has {len(triggers)} EventTrigger entries, expected 1")
            op = str(get_ci(triggers[0].get("metadata", {}), "Operation") or "")
            if seed["operation"].lower() not in op.lower():
                fail(f"EventTrigger Operation {op!r} is not Record {seed['operation']}")
            if "REPLACE_WITH" in open(path, encoding="utf-8").read():
                fail("unresolved <REPLACE_WITH_*> placeholder in Workflow.json")
            print(f"OK: {path} starts on Test Manager Record {seed['operation']} / {seed['object_type']}, EventTrigger bound")
            return
    fail(f"no Workflow.json whose first activity after WorkflowStart is the Test Manager "
         f"Record {seed['operation']} trigger for {seed['object_type']}")


def check_rpa(seed):
    mains = project_files("**/Main.xaml")
    if not mains:
        fail("no Main.xaml found")
    for path in mains:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            fail(f"{path} is not well-formed XAML: {exc}")
        sequence = next((el for el in root if el.tag.rsplit("}", 1)[-1] == "Sequence"), None)
        if sequence is None:
            continue
        activities = [el for el in sequence if "." not in el.tag.rsplit("}", 1)[-1]]
        if not activities:
            continue
        trigger = activities[0]
        blob = ET.tostring(trigger, encoding="unicode").lower()
        if seed["operation"].lower() not in blob or seed["object_type"].lower() not in blob:
            continue
        connection = next((v for k, v in trigger.attrib.items() if k.rsplit("}", 1)[-1] == "ConnectionId"), "")
        if not GUID_RE.fullmatch(connection.strip()) or connection.strip() == ZERO_GUID:
            fail(f"trigger ConnectionId {connection!r} is not a real connection GUID — it would fail to subscribe")
        print(f"OK: {path} root Sequence starts on the Test Manager Record {seed['operation']} trigger for {seed['object_type']}")
        return
    fail(f"no Main.xaml whose first root-Sequence activity is the Test Manager "
         f"Record {seed['operation']} trigger for {seed['object_type']}")


def check_bpmn(seed):
    files = project_files("**/*.bpmn")
    if not files:
        fail("no .bpmn file found")
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            fail(f"{path} is not well-formed XML: {exc}")
        for start in root.iter():
            if start.tag.rsplit("}", 1)[-1] != "startEvent":
                continue
            types = [el.get("value") for el in start.iter() if el.tag.rsplit("}", 1)[-1] == "type"]
            if "Intsvc.EventTrigger" not in types:
                continue
            inputs = {el.get("name"): (el.get("value") or el.text or "") for el in start.iter()
                      if el.tag.rsplit("}", 1)[-1] == "input"}
            blob = " ".join(inputs.values()).lower()
            if inputs.get("connectorKey") == CONNECTOR \
                    and seed["operation"].lower() in str(inputs.get("operation", "")).lower() \
                    and seed["object_type"].lower() in blob:
                print(f"OK: {path} starts on an Intsvc.EventTrigger for Test Manager Record {seed['operation']} / {seed['object_type']}")
                return
    fail(f"no bpmn:startEvent carrying Intsvc.EventTrigger for {CONNECTOR} "
         f"operation {seed['operation']!r} and object type {seed['object_type']!r}")


# ---------------------------------------------------------------- validate

def validate(surface):
    if surface == "api-workflow":
        targets = [p for p in project_files("**/Workflow.json") if os.path.dirname(p)]
        args = ("api-workflow", "validate")
    else:
        targets = project_files("**/*.bpmn")
        args = ("maestro", "bpmn", "validate")
    if not targets:
        fail(f"nothing to validate for {surface}")
    for target in targets:
        data = run_uip(*args, target)
        status = str(get_ci(data, "Status") or get_ci(data, "status") or "")
        if status and status.lower() != "valid":
            fail(f"{target} did not validate: {json.dumps(data)[:400]}")
        print(f"OK: {target} validates")


# ---------------------------------------------------------------- live

def payload_matches(payload, seed, result):
    if seed["object_type"] == "TestCaseLog":
        return str(get_ci(payload, "testExecutionId") or "").lower() == str(result.get("execution_id", "")).lower()
    return str(get_ci(payload, "id") or "").lower() == str(result.get("record_id", "")).lower()


def check_key_fields(payload, seed):
    op, obj = seed["operation"], seed["object_type"]
    if obj in NAMED:
        if get_ci(payload, "name") != seed["marker"]:
            fail(f"payload name {get_ci(payload, 'name')!r} != seeded marker {seed['marker']!r}")
        if op == "Updated" and seed.get("updated_description") not in str(get_ci(payload, "description") or ""):
            fail(f"payload description does not carry the update {seed.get('updated_description')!r}")
    elif obj == "TestExecution":
        if not get_ci(payload, "testSetId"):
            fail("payload has no testSetId")
        if op == "Finished":
            status = str(get_ci(payload, "status") or "").lower()
            if status not in TERMINAL:
                fail(f"Record Finished payload status {status!r} is not terminal")
            if not get_ci(payload, "executionFinished"):
                fail("Record Finished payload has no executionFinished timestamp")
    elif obj == "TestCaseLog" and op == "Finished":
        if not get_ci(payload, "result"):
            fail("Record Finished payload for TestCaseLog has no result")


def check_record_is_ours(seed, result):
    obj = seed["object_type"]
    record_id = result.get("execution_id") if obj == "TestCaseLog" else result.get("record_id")
    get_obj = "TestExecution" if obj == "TestCaseLog" else obj
    data = run_uip(
        "is", "resources", "run", "get", CONNECTOR, get_obj, "--connection-id", result["connection_id"],
        "--query", f"{PROJECT_PARAM[get_obj]}={result['project_id']}&id={record_id}",
    )
    if obj in NAMED and get_ci(data, "name") != seed["marker"]:
        fail(f"{obj} {record_id} is named {get_ci(data, 'name')!r}, not the seeded marker — not this run's record")
    if get_obj == "TestExecution" and not get_ci(data, "id"):
        fail(f"TestExecution {record_id} not found in project {result['project_id']}")


def live(seed):
    result = load("result.json", "result.json missing — agent did not record the fired record")
    for key in ("connection_id", "project_id", "record_id"):
        if not result.get(key):
            fail(f"result.json has no {key}")
    if seed["object_type"] == "TestCaseLog" and not result.get("execution_id"):
        fail("result.json has no execution_id for a TestCaseLog event")
    check_record_is_ours(seed, result)

    jobs = items(run_uip("or", "jobs", "list", "--all-folders", "--process-name", seed["process_name"],
                         "--created-after", seed["started_at"], "--all-fields", "--limit", "50"))
    if not jobs:
        fail(f"no job of process {seed['process_name']!r} since {seed['started_at']} — the trigger never fired")
    states = []
    for job in jobs:
        outputs = get_ci(job, "OutputArguments")
        if outputs is None and get_ci(job, "Key"):
            outputs = get_ci(run_uip("or", "jobs", "get", str(get_ci(job, "Key")), "--all-fields", "--no-download"),
                             "OutputArguments")
        for payload in walk_dicts(outputs):
            if not payload_matches(payload, seed, result):
                continue
            state = str(get_ci(job, "State") or "")
            states.append(state)
            if state.lower() != "successful":
                continue
            object_type = str(get_ci(payload, "objectType") or "")
            if object_type.lower() != seed["object_type"].lower():
                fail(f"payload objectType {object_type!r} != {seed['object_type']!r}")
            project_id = str(get_ci(payload, "projectId") or "")
            if project_id.lower() != str(result["project_id"]).lower():
                fail(f"payload projectId {project_id!r} != {result['project_id']!r}")
            check_key_fields(payload, seed)
            print(f"OK: job {get_ci(job, 'Key')} ran Successful on Record {seed['operation']} "
                  f"for {seed['object_type']} {result['record_id']}; payload fields verified")
            return
    if states:
        fail(f"the job(s) for this record ended {sorted(set(states))}, none Successful")
    fail(f"{len(jobs)} job(s) ran but none returned a payload for record {result['record_id']}")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--artifact", choices=("api-workflow", "rpa", "bpmn"))
    mode.add_argument("--validate", choices=("api-workflow", "bpmn"))
    mode.add_argument("--live", action="store_true")
    args = parser.parse_args()

    seed = load("seed.json", "seed.json missing (pre_run did not run)")
    if args.artifact:
        {"api-workflow": check_api_workflow, "rpa": check_rpa, "bpmn": check_bpmn}[args.artifact](seed)
    elif args.validate:
        validate(args.validate)
    else:
        live(seed)


if __name__ == "__main__":
    main()
