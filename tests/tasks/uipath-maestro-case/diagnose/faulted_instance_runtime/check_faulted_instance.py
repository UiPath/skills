"""Grade diagnosis.json against the tenant, read at grading time.

The answer is not hardcoded: the expected instance, task and error code are
re-derived from the same read-only CLI calls the skill teaches (instance list
-> incidents -> instance asset). A diagnosis copied from a stale run, or guessed,
fails whenever it disagrees with what the tenant says now.

Exit codes: 0 pass, 1 wrong or missing answer, 2 precondition (the tenant no
longer holds a faulted OutcomeExpenseApproval instance in the folder).
"""

import json
import os
import shutil
import subprocess
import sys

FOLDER = os.environ.get("CASE_FAULT_FOLDER", "Shared/OutcomeExpenseApproval")
PACKAGE_PREFIX = "OutcomeExpenseApproval."
ANSWER = os.environ.get("CASE_FAULT_ANSWER", "diagnosis.json")


def uip(*args):
    exe = shutil.which("uip")
    if not exe:
        sys.exit("FAIL: uip not on PATH")
    out = subprocess.run([exe, *args, "--output", "json"], capture_output=True, text=True, timeout=120)
    text = out.stdout
    start = text.find("{")
    if start < 0:
        sys.exit(f"FAIL: no JSON from uip {' '.join(args)}: {out.stderr[:300]}")
    body = json.loads(text[start:])
    if body.get("Result") != "Success":
        sys.exit(f"FAIL: uip {' '.join(args)} -> {body.get('Message')}")
    return body.get("Data")


def tasks_by_id(asset):
    found = {}
    for node in asset.get("Nodes") or []:
        data = node.get("Data") or {}
        for group in data.get("Tasks") or []:
            for task in group if isinstance(group, list) else [group]:
                found[task.get("Id")] = task.get("DisplayName")
    return found


def truth():
    processes = uip("maestro", "case", "processes", "list")["Processes"]
    rows = [p for p in processes if p.get("FolderName") == FOLDER and p.get("PackageId", "").startswith(PACKAGE_PREFIX)]
    if not rows:
        print(f"PRECONDITION: no OutcomeExpenseApproval process in {FOLDER}")
        sys.exit(2)
    proc = rows[0]
    instances = uip("maestro", "case", "instance", "list", "--process-key", proc["ProcessKey"], "--folder-key", proc["FolderKey"])
    faulted = {}
    for inst in instances or []:
        if inst.get("LatestRunStatus") != "Faulted":
            continue
        open_incidents = [i for i in inst.get("Incidents") or [] if i.get("IncidentStatus") == "Open"]
        if not open_incidents:
            continue
        asset = uip("maestro", "case", "instance", "asset", inst["InstanceId"], "--folder-key", proc["FolderKey"])
        names = tasks_by_id(asset)
        faulted[inst["InstanceId"]] = [
            {"errorCode": str(i.get("ErrorCode")), "taskName": names.get(i.get("ElementId")), "elementId": i.get("ElementId")}
            for i in open_incidents
        ]
    if not faulted:
        print(f"PRECONDITION: no faulted OutcomeExpenseApproval instance with an open incident in {FOLDER}")
        sys.exit(2)
    return faulted


def main():
    if not os.path.isfile(ANSWER):
        sys.exit(f"FAIL: {ANSWER} not written")
    try:
        answer = json.load(open(ANSWER))
    except ValueError as err:
        sys.exit(f"FAIL: {ANSWER} is not JSON: {err}")
    faulted = truth()
    inst = str(answer.get("instanceId", "")).strip()
    if inst not in faulted:
        sys.exit(f"FAIL: instanceId {inst!r} is not a faulted instance in {FOLDER} (expected one of {sorted(faulted)})")
    code = str(answer.get("errorCode", "")).strip()
    task = str(answer.get("taskName", "")).strip()
    for incident in faulted[inst]:
        if code == incident["errorCode"] and task == (incident["taskName"] or ""):
            print(f"PASS: {inst} faulted at {task!r} with {code}")
            return
    sys.exit(f"FAIL: answer {task!r}/{code!r} matches no open incident {faulted[inst]}")


if __name__ == "__main__":
    main()
