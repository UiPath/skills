#!/usr/bin/env python3
"""post_run cleanup for Test Manager connector event-trigger e2e tasks.

Runs whether or not the task passed. Removes everything the run created:
  1. the solution deployment named in seed.json (drops the event subscription),
  2. every TM record listed in result.json `created`,
  3. any TestCase / TestSet / Requirement in the project still carrying the
     seeded marker (covers runs that died before writing result.json).

Never fails the task: every step is best-effort and the script exits 0.
"""
import json
import subprocess

CONNECTOR = "uipath-uipath-testmanager"
# Path-parameter casing differs per object in the connector's SR files.
PROJECT_PARAM = {
    "Requirement": "ProjectId",
    "TestCase": "ProjectId",
    "TestSet": "ProjectId",
    "TestExecution": "projectId",
    "TestCaseLog": "projectId",
}
# Children before parents: executions reference test sets, test sets reference test cases.
DELETE_ORDER = ["TestExecution", "TestSet", "TestCase", "Requirement"]
MARKER_SWEEP = ["TestSet", "TestCase", "Requirement"]


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def run_uip(*args, timeout=180):
    cmd = ["uip", *args, "--output", "json"]
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


def delete_record(connection_id, project_id, obj, record_id):
    param = PROJECT_PARAM.get(obj, "ProjectId")
    ok = run_uip(
        "is", "resources", "run", "delete", CONNECTOR, obj,
        "--connection-id", connection_id, "--query", f"{param}={project_id}&id={record_id}", "--yes",
    )
    print(f"  delete {obj} {record_id}: {'ok' if ok is not None else 'failed'}")


def main():
    seed = load("seed.json")
    result = load("result.json")
    if not seed:
        print("cleanup: no seed.json — nothing to clean")
        return

    deployment = seed.get("deployment_name")
    if deployment:
        print(f"cleanup: uninstalling deployment {deployment}")
        run_uip("solution", "deploy", "uninstall", deployment, "--yes", timeout=600)

    connection_id = resolve_connection(result)
    if not connection_id:
        print("cleanup: no Test Manager connection resolved — skipping record cleanup")
        return
    project_id = resolve_project(seed, result, connection_id)
    if not project_id:
        print("cleanup: project id not resolved — skipping record cleanup")
        return

    created = [c for c in result.get("created", []) if isinstance(c, dict) and c.get("id")]
    created.sort(key=lambda c: DELETE_ORDER.index(c["object"]) if c.get("object") in DELETE_ORDER else len(DELETE_ORDER))
    for record in created:
        delete_record(connection_id, project_id, record["object"], record["id"])

    marker = seed.get("marker", "")
    deleted = {(c.get("object"), str(c.get("id"))) for c in created}
    for obj in MARKER_SWEEP:
        listed = run_uip(
            "is", "resources", "run", "list", CONNECTOR, obj,
            "--connection-id", connection_id, "--query", f"{PROJECT_PARAM[obj]}={project_id}",
        )
        for record in items(listed):
            name = str(get_ci(record, "name") or "")
            record_id = str(get_ci(record, "id") or "")
            if marker and name.startswith(marker) and record_id and (obj, record_id) not in deleted:
                delete_record(connection_id, project_id, obj, record_id)
    print("cleanup: done")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never fail the task on cleanup
        print(f"cleanup: unexpected error ignored: {exc}")
