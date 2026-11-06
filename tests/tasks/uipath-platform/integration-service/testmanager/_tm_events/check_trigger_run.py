#!/usr/bin/env python3
"""Grader for Test Manager connector event-trigger e2e tasks (all workflow types).

Modes:
  --artifact <surface>   The authored workflow starts on the TM trigger under test
                         (surface: api-workflow | rpa | bpmn).
  --validate <surface>   The authored workflow passes the surface's offline
                         validator (api-workflow | bpmn).
  --live                 The deployed workflow actually ran on the event: polls
                         Orchestrator (up to LIVE_WAIT s) for a Successful job of
                         seed.json's process that the trigger started, then asserts
                         the payload that job returned carries the entity type,
                         record id, project id and key fields, and that the record
                         is the one this run created.

Reads seed.json (pre_run) and result.json (agent):
  result.json -> {"connection_id", "project_id", "record_id", "execution_id"?,
                  "created": [{"object", "id"}, ...]}
The job is found independently of anything the agent reports about it.

Object types and operations match as whole tokens, case-insensitively: TestCase
does not match TestCaseLog, Updated does not match updatedAt, and Created still
matches RECORD_CREATED once the connector uppercases its operations.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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
# A TestExecution still in one of these has not changed since it was created.
INITIAL = {"", "pending", "notstarted", "new", "created", "queued"}
# Job sources that mean a person or the agent started the job, not the event trigger.
MANUAL_SOURCES = {"manual", "assistant", "commandline", "robotapi", "studio", "studioweb", "studiox", "studiopro", "apps"}
ZERO_GUID = "00000000-0000-0000-0000-000000000000"
GUID_RE = re.compile(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
LIVE_WAIT = 120     # seconds to wait for event delivery after the agent finishes
LIVE_POLL = 15
JOB_PAGE = 100
# Every uip call shares one budget that ends before the criterion timeout (300 s for --live).
BUDGET_END = time.monotonic() + 270


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


def has_token(text, word):
    """word occurs in text as a whole token (no letter or digit on either side), case-insensitively."""
    return re.search(rf"(?<![a-z0-9]){re.escape(word.lower())}(?![a-z0-9])", str(text).lower()) is not None


def parse_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def run_uip(*args, timeout=60):
    remaining = BUDGET_END - time.monotonic()
    if remaining < 5:
        fail(f"grader time budget spent before `uip {' '.join(args[:4])}`")
    timeout = min(timeout, remaining)
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
                and has_token(blob, seed["operation"]) and has_token(blob, seed["object_type"]):
            bindings = os.path.join(os.path.dirname(path), "bindings_v2.json")
            if not os.path.exists(bindings):
                fail(f"{bindings} missing — run `uip api-workflow bindings sync`; without it a deploy never subscribes")
            triggers = [r for r in json.load(open(bindings, encoding="utf-8")).get("resources", [])
                        if r.get("resource") == "EventTrigger"]
            if len(triggers) != 1:
                fail(f"bindings_v2.json has {len(triggers)} EventTrigger entries, expected 1")
            op = str(get_ci(triggers[0].get("metadata", {}), "Operation") or "")
            if not has_token(op, seed["operation"]):
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
        # Only the trigger's own attributes: child elements carry the event's output
        # schema (updatedAt, testCaseId, ...), which would match any operation or object.
        attrs = {k.rsplit("}", 1)[-1]: v for k, v in trigger.attrib.items()}
        op_values = [v for k, v in attrs.items() if any(w in k.lower() for w in ("operation", "event"))] \
            or list(attrs.values())
        if not any(has_token(v, seed["operation"]) for v in op_values) \
                or not any(has_token(v, seed["object_type"]) for v in attrs.values()):
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
            others = [v for k, v in inputs.items() if k not in ("connectorKey", "operation")]
            if inputs.get("connectorKey") == CONNECTOR \
                    and has_token(inputs.get("operation", ""), seed["operation"]) \
                    and any(has_token(v, seed["object_type"]) for v in others):
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
        # run_uip fails on a non-zero exit, which is the validator's verdict. A Status
        # field, when the output has one, must also say Valid.
        data = run_uip(*args, target)
        status = str(get_ci(data, "Status") or "")
        if status and status.lower() != "valid":
            fail(f"{target} did not validate: {json.dumps(data)[:400]}")
        print(f"OK: {target} validates")


# ---------------------------------------------------------------- live

def payload_matches(payload, seed, result):
    if seed["object_type"] == "TestCaseLog":
        return str(get_ci(payload, "testExecutionId") or "").lower() == str(result.get("execution_id", "")).lower() \
            and str(get_ci(payload, "id") or "").lower() == str(result.get("record_id", "")).lower()
    return str(get_ci(payload, "id") or "").lower() == str(result.get("record_id", "")).lower()


def key_field_error(payload, seed):
    """Return why payload lacks the operation's key fields, or None."""
    op, obj = seed["operation"], seed["object_type"]
    if obj in NAMED:
        if get_ci(payload, "name") != seed["marker"]:
            return f"payload name {get_ci(payload, 'name')!r} != seeded marker {seed['marker']!r}"
        if op == "Updated" and seed.get("updated_description") not in str(get_ci(payload, "description") or ""):
            return f"payload description does not carry the update {seed.get('updated_description')!r}"
    elif obj == "TestExecution":
        if not get_ci(payload, "testSetId"):
            return "payload has no testSetId"
        status = str(get_ci(payload, "status") or "").lower()
        if op == "Updated" and status in INITIAL:
            return f"Record Updated payload status {status!r} has not moved past its initial value"
        if op == "Finished":
            if status not in TERMINAL:
                return f"Record Finished payload status {status!r} is not terminal"
            if not get_ci(payload, "executionFinished"):
                return "Record Finished payload has no executionFinished timestamp"
    elif obj == "TestCaseLog":
        if not get_ci(payload, "testCaseId"):
            return "TestCaseLog payload has no testCaseId"
        if op == "Finished" and not get_ci(payload, "result"):
            return "Record Finished payload for TestCaseLog has no result"
    return None


def get_record(result, obj, record_id):
    return run_uip(
        "is", "resources", "run", "get", CONNECTOR, obj, "--connection-id", result["connection_id"],
        "--query", f"{PROJECT_PARAM[obj]}={result['project_id']}&id={record_id}",
    )


def check_record_is_ours(seed, result):
    obj = seed["object_type"]
    if obj in NAMED:
        data = get_record(result, obj, result["record_id"])
        if get_ci(data, "name") != seed["marker"]:
            fail(f"{obj} {result['record_id']} is named {get_ci(data, 'name')!r}, not the seeded marker — not this run's record")
        return
    # Execution-driven: every deployed workflow sees the whole project's executions, so
    # prove this one ran the seeded fixture test set and started after this run began.
    execution_id = result["execution_id"] if obj == "TestCaseLog" else result["record_id"]
    execution = get_record(result, "TestExecution", execution_id)
    if not get_ci(execution, "id"):
        fail(f"TestExecution {execution_id} not found in project {result['project_id']}")
    test_set_id = str(get_ci(execution, "testSetId") or "")
    wanted = str(seed["execution_test_set"]).lower()
    if test_set_id.lower() != wanted:
        test_set = get_record(result, "TestSet", test_set_id) if test_set_id else {}
        names = {str(get_ci(test_set, k) or "").lower() for k in ("key", "name", "id")}
        if wanted not in names:
            fail(f"TestExecution {execution_id} ran test set {test_set_id!r}, not the fixture {seed['execution_test_set']!r}")
    started = next((parse_time(v) for v in (get_ci(execution, k) for k in
                    ("executionStarted", "created", "createdOn", "createdAt", "startTime")) if v), None)
    run_start = parse_time(seed["started_at"])
    if started is None or run_start is None:
        fail(f"TestExecution {execution_id} has no readable start or creation time — cannot prove it belongs to this run")
    if started < run_start:
        fail(f"TestExecution {execution_id} started {started.isoformat()}, before this run began ({seed['started_at']})")


def list_jobs(seed):
    common = ("--all-folders", "--created-after", seed["started_at"], "--all-fields", "--limit", str(JOB_PAGE))
    jobs = items(run_uip("or", "jobs", "list", "--process-name", seed["process_name"], *common))
    if jobs:
        return jobs
    # A solution deploy may prefix the process name, so fall back to a containment match.
    return [j for j in items(run_uip("or", "jobs", "list", *common))
            if any(seed["process_name"].lower() in str(get_ci(j, k) or "").lower()
                   for k in ("ReleaseName", "ProcessName", "ProcessKey"))]


def job_error(job, payload, seed, result):
    """Return why this job does not prove the event ran the workflow, or None."""
    state = str(get_ci(job, "State") or "")
    if state.lower() != "successful":
        return f"job {get_ci(job, 'Key')} ended {state!r}, not Successful"
    for field in ("SourceType", "Source"):
        source = str(get_ci(job, field) or "").replace(" ", "").lower()
        if source in MANUAL_SOURCES:
            return f"job {get_ci(job, 'Key')} was started by hand ({field} {get_ci(job, field)!r}), not by the event trigger"
    object_type = str(get_ci(payload, "objectType") or "")
    if object_type.lower() != seed["object_type"].lower():
        return f"payload objectType {object_type!r} != {seed['object_type']!r}"
    project_id = str(get_ci(payload, "projectId") or "")
    if project_id.lower() != str(result["project_id"]).lower():
        return f"payload projectId {project_id!r} != {result['project_id']!r}"
    return key_field_error(payload, seed)


def live(seed):
    result = load("result.json", "result.json missing — agent did not record the fired record")
    for key in ("connection_id", "project_id", "record_id"):
        if not result.get(key):
            fail(f"result.json has no {key}")
    if seed["object_type"] == "TestCaseLog" and not result.get("execution_id"):
        fail("result.json has no execution_id for a TestCaseLog event")
    check_record_is_ours(seed, result)

    # Updated events fire several jobs per record, so every matching job is tried and the
    # check passes on the first that holds. Delivery can trail the agent, so poll.
    deadline = min(time.monotonic() + LIVE_WAIT, BUDGET_END - 90)
    while True:
        jobs = list_jobs(seed)
        reasons = []
        for job in jobs:
            outputs = get_ci(job, "OutputArguments")
            if outputs is None and get_ci(job, "Key"):
                outputs = get_ci(run_uip("or", "jobs", "get", str(get_ci(job, "Key")), "--all-fields", "--no-download"),
                                 "OutputArguments")
            for payload in walk_dicts(outputs):
                if not payload_matches(payload, seed, result):
                    continue
                error = job_error(job, payload, seed, result)
                if error is None:
                    print(f"OK: job {get_ci(job, 'Key')} was started by the Record {seed['operation']} trigger for "
                          f"{seed['object_type']} {result['record_id']} and ran Successful; payload fields verified")
                    return
                reasons.append(error)
        if time.monotonic() + LIVE_POLL > deadline:
            break
        time.sleep(LIVE_POLL)
    if reasons:
        fail("no job for this record passed every check: " + "; ".join(sorted(set(reasons))))
    if jobs:
        fail(f"{len(jobs)} job(s) ran but none returned a payload for record {result['record_id']}")
    fail(f"no job of process {seed['process_name']!r} since {seed['started_at']} — the trigger never fired")


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
