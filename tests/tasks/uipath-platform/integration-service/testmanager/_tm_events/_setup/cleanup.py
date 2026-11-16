#!/usr/bin/env python3
"""post_run cleanup for Test Manager connector event-trigger e2e tasks.

Runs whether or not the task passed, and deletes only what it can prove this run
created. result.json is written by the agent and seed.json sits in its sandbox,
so neither is trusted on its own:
  1. the solution deployment named in seed.json (drops the event subscription),
  2. this run's copy of the fixture test set (execution-driven tasks) and every
     execution of it, once the copy's own name is confirmed to carry the marker,
  3. each record in result.json `created` that passes an ownership check: a named
     record (Requirement / TestCase / TestSet) whose name starts with the marker,
     or a TestExecution of this run's test set copy. Anything else is kept,
  4. any TestSet / TestCase / Requirement still named with the marker (covers runs
     that died before writing result.json), following the connector's next-page
     token when the list returns one.

Never fails the task: every step is best-effort and the script exits 0.
Finishes inside the 300 s post_run cap: every call is bounded by a shared
deadline, and steps still pending when it runs out are skipped.
"""
import json
import re
import shutil
import subprocess
import time

# subprocess cannot run the Windows uip.cmd shim by bare name; resolve it first.
UIP = shutil.which("uip") or "uip"
CONNECTOR = "uipath-uipath-testmanager"
# Path-parameter casing differs per object in the connector's SR files.
PROJECT_PARAM = {
    "Requirement": "ProjectId",
    "TestCase": "ProjectId",
    "TestSet": "ProjectId",
    "TestExecution": "projectId",
    "TestCaseLog": "projectId",
}
NAMED = ("Requirement", "TestCase", "TestSet")
# Children before parents: executions reference test sets, test sets reference test cases.
DELETE_ORDER = ["TestExecution", "TestSet", "TestCase", "Requirement"]
MARKER_SWEEP = ["TestSet", "TestCase", "Requirement"]
# seed.py's marker shape. A shorter or edited marker would make the name checks match
# other runs' records, so cleanup refuses to sweep with anything else.
MARKER_RE = re.compile(r"DataEval-[0-9a-f]{8}")
NEXT_PAGE_KEYS = ("nextPage", "nextPageToken", "NextPageToken")
MAX_PAGES = 20
# post_run timeout is 300 s (schema maximum); keep headroom for interpreter start-up.
DEADLINE = time.monotonic() + 270


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def run_uip(*args, timeout=45):
    remaining = DEADLINE - time.monotonic()
    if remaining < 5:
        print(f"  skipped {' '.join(args[:4])}: cleanup time budget spent")
        return None
    timeout = min(timeout, remaining)
    cmd = [UIP, *args, "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  skipped {' '.join(args[:4])}: {exc}")
        return None
    try:
        envelope = json.loads(proc.stdout or "{}")
    except ValueError:
        envelope = {}
    if proc.returncode != 0:
        print(f"  {' '.join(args[:4])} exited {proc.returncode}: {(proc.stdout or proc.stderr)[:300]}")
        return None
    return envelope.get("Data", envelope) if isinstance(envelope, dict) else envelope


def items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "Items", "value", "data", "records"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def get_ci(obj, key):
    if not isinstance(obj, dict):
        return None
    for k, v in obj.items():
        if k.lower() == key.lower():
            return v
    return None


def resolve_connection(result):
    if result.get("connection_id"):
        return result["connection_id"]
    for conn in items(run_uip("is", "connections", "list", CONNECTOR, "--all-folders")):
        conn_id = get_ci(conn, "id") or get_ci(conn, "connectionId")
        if conn_id:
            return conn_id
    return None


def resolve_project(seed, result, connection_id):
    if result.get("project_id"):
        return result["project_id"]
    data = run_uip(
        "is", "resources", "run", "get", CONNECTOR, "GetProjectByPrefix",
        "--connection-id", connection_id, "--query", f"projectPrefix={seed.get('project_key', '')}",
    )
    return get_ci(data, "id") if isinstance(data, dict) else None


def get_record(connection_id, project_id, obj, record_id):
    data = run_uip(
        "is", "resources", "run", "get", CONNECTOR, obj,
        "--connection-id", connection_id, "--query", f"{PROJECT_PARAM[obj]}={project_id}&id={record_id}",
    )
    return data if isinstance(data, dict) else {}


def delete_record(connection_id, project_id, obj, record_id):
    ok = run_uip(
        "is", "resources", "run", "delete", CONNECTOR, obj,
        "--connection-id", connection_id, "--query", f"{PROJECT_PARAM[obj]}={project_id}&id={record_id}", "--yes",
    )
    print(f"  delete {obj} {record_id}: {'ok' if ok is not None else 'failed'}")


def owned_test_set_id(seed, connection_id, project_id):
    """This run's test set copy id, only if the record it names really carries the marker."""
    set_id = seed.get("execution_test_set_id")
    if not set_id:
        return None
    name = str(get_ci(get_record(connection_id, project_id, "TestSet", set_id), "name") or "")
    if not name.startswith(seed["marker"]):
        print(f"  kept test set {set_id}: named {name!r}, not this run's copy")
        return None
    return str(set_id)


def is_owned(seed, record, connection_id, project_id, copy_id):
    obj, record_id = record.get("object"), record.get("id")
    if obj in NAMED:
        name = str(get_ci(get_record(connection_id, project_id, obj, record_id), "name") or "")
        return name.startswith(seed["marker"])
    if obj == "TestExecution" and copy_id:
        test_set_id = str(get_ci(get_record(connection_id, project_id, obj, record_id), "testSetId") or "")
        return test_set_id.lower() == copy_id.lower()
    return False


def delete_copy(seed, copy_id):
    """Delete every execution of this run's test set copy, then the copy itself."""
    project_key = seed.get("project_key", "")
    listed = run_uip("tm", "executions", "list", "--project-key", project_key,
                     "--test-set-id", copy_id, "--limit", "100")
    for execution in items(listed):
        execution_id = get_ci(execution, "id")
        if execution_id:
            ok = run_uip("tm", "executions", "delete", "--execution-id", str(execution_id),
                         "--project-key", project_key, "--yes")
            print(f"  delete TestExecution {execution_id}: {'ok' if ok is not None else 'failed'}")
    ok = run_uip("tm", "testsets", "delete", "--test-set-key", seed["execution_test_set"])
    print(f"  delete test set copy {seed['execution_test_set']}: {'ok' if ok is not None else 'failed'}")


def list_all(connection_id, project_id, obj):
    """List obj records, following the connector's next-page token when the response has one."""
    query = f"{PROJECT_PARAM[obj]}={project_id}"
    records, token = [], None
    for _ in range(MAX_PAGES):
        page_query = f"{query}&nextPage={token}" if token else query
        data = run_uip("is", "resources", "run", "list", CONNECTOR, obj,
                       "--connection-id", connection_id, "--query", page_query)
        records += items(data)
        token = next((get_ci(data, k) for k in NEXT_PAGE_KEYS if get_ci(data, k)), None)
        if not token:
            return records
    print(f"  {obj} sweep stopped after {MAX_PAGES} pages")
    return records


def main():
    seed = load("seed.json")
    result = load("result.json")
    if not seed:
        print("cleanup: no seed.json — nothing to clean")
        return

    deployment = seed.get("deployment_name")
    if deployment:
        print(f"cleanup: uninstalling deployment {deployment}")
        run_uip("solution", "deploy", "uninstall", deployment, "--yes", timeout=150)

    if not MARKER_RE.fullmatch(str(seed.get("marker", ""))):
        print(f"cleanup: seed marker {seed.get('marker')!r} is not seed.py's shape — skipping record cleanup")
        return
    connection_id = resolve_connection(result)
    if not connection_id:
        print("cleanup: no Test Manager connection resolved — skipping record cleanup")
        return
    project_id = resolve_project(seed, result, connection_id)
    if not project_id:
        print("cleanup: project id not resolved — skipping record cleanup")
        return

    copy_id = owned_test_set_id(seed, connection_id, project_id)
    deleted = set()
    if copy_id:
        delete_copy(seed, copy_id)
        deleted.add(("TestSet", copy_id.lower()))

    created = [c for c in result.get("created", []) if isinstance(c, dict) and c.get("id")]
    created.sort(key=lambda c: DELETE_ORDER.index(c["object"]) if c.get("object") in DELETE_ORDER else len(DELETE_ORDER))
    for record in created:
        key = (record.get("object"), str(record["id"]).lower())
        if key in deleted:
            continue
        if is_owned(seed, record, connection_id, project_id, copy_id):
            delete_record(connection_id, project_id, record["object"], record["id"])
            deleted.add(key)
        else:
            print(f"  kept {record.get('object')} {record['id']}: not provably this run's")

    marker = seed["marker"]
    for obj in MARKER_SWEEP:
        for record in list_all(connection_id, project_id, obj):
            name = str(get_ci(record, "name") or "")
            record_id = str(get_ci(record, "id") or "")
            if name.startswith(marker) and record_id and (obj, record_id.lower()) not in deleted:
                delete_record(connection_id, project_id, obj, record_id)
    print("cleanup: done")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never fail the task on cleanup
        print(f"cleanup: unexpected error ignored: {exc}")
