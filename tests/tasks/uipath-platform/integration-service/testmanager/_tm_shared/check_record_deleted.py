#!/usr/bin/env python3
"""Query the tenant: the record the agent created is gone after the run.

Usage: check_record_deleted.py <Requirement|TestSet>

Grades the cleanup step on its outcome. A command_executed check cannot: it sees
the exit code of the whole Bash call, so it fails a delete followed by a verify
get (404, exit 1) and passes a delete that never ran or failed.

Reads seed.json (project_key) and result.json (id), resolves the Test Manager
connection and project, then gets the record by id. Passes only on the
provider's 404 itemNotFound; any other failure (auth, missing connection
instance) fails closed as "could not verify".

Known gameability, accepted deliberately: result.json is written by the agent, so
an agent could record a fake id. check.py already trusts the same file.
"""
import json
import subprocess
import sys

CONNECTOR = "uipath-uipath-testmanager"
OBJECT_TYPES = ("Requirement", "TestSet")


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def uip_json(*args):
    try:
        r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        fail(f"uip {args[0]} {args[1]} did not run ({type(e).__name__})")
    raw = r.stdout or ""
    try:
        out = json.loads(raw[raw.index("{"):])
    except ValueError:
        fail(f"uip {' '.join(args[:4])} produced no JSON")
    if not isinstance(out, dict):
        fail(f"uip {' '.join(args[:4])} returned an unexpected JSON shape")
    return out


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in OBJECT_TYPES:
        fail(f"usage: check_record_deleted.py <{'|'.join(OBJECT_TYPES)}>")
    obj = sys.argv[1]
    try:
        seed = json.load(open("seed.json", encoding="utf-8"))
        res = json.load(open("result.json", encoding="utf-8"))
    except (OSError, ValueError):
        fail("seed.json or result.json missing or unreadable")
    if not isinstance(seed, dict) or not isinstance(res, dict):
        fail("seed.json or result.json is not a JSON object")
    rec_id = res.get("id")
    if not rec_id or not seed.get("project_key"):
        fail(f"no {obj} id in result.json or no project_key in seed.json")

    conns = [c for c in uip_json("is", "connections", "list", CONNECTOR).get("Data") or []
             if c.get("State") == "Enabled"]
    if not conns:
        fail(f"no enabled {CONNECTOR} connection to verify with")
    conn = next((c for c in conns if c.get("IsDefault") == "Yes"), conns[0])["Id"]

    proj = uip_json("is", "resources", "run", "get", CONNECTOR, "GetProjectByPrefix", "--connection-id", conn,
                    "--query", json.dumps({"projectPrefix": seed["project_key"]}))
    project_id = (proj.get("Data") or {}).get("id") if proj.get("Result") == "Success" else None
    if not project_id:
        fail(f"could not resolve project {seed['project_key']!r}")

    got = uip_json("is", "resources", "run", "get", CONNECTOR, obj, "--connection-id", conn,
                   "--query", json.dumps({"ProjectId": project_id, "id": rec_id}))
    if got.get("Result") == "Success":
        fail(f"{obj} {rec_id} still exists: the delete did not run or did not succeed")
    detail = f"{got.get('Message') or ''} {got.get('Instructions') or ''}"
    if (got.get("ErrorCode") == "not_found" or '"providerErrorCode":404' in detail) and "itemNotFound" in detail:
        print(f"OK: {obj} {rec_id} no longer exists")
        return
    fail(f"could not verify the delete: {got.get('ErrorCode')} {(got.get('Message') or '')[:120]}")


if __name__ == "__main__":
    main()
