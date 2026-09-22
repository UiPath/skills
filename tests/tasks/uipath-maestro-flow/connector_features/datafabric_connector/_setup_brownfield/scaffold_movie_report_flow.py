#!/usr/bin/env python3
"""Scaffold a valid `MovieReportFlow` inside the coder-eval sandbox and
snapshot its initial state. Used by `smoke_update_existing_flow` to give
the agent a real brownfield artifact to edit + revert.

Runs from `pre_run` inside the sandbox cwd. Requires an authenticated `uip`
session and a healthy `uipath-uipath-dataservice` connection.

After this script exits:
  - MovieReportSolution/MovieReportFlow/MovieReportFlow.flow exists and
    passes `uip maestro flow validate`
  - pre_state.flow (sibling of the .flow) is a byte-copy of the initial
    state that the verifier will diff against post-agent

The initial state has ONE `query-entity-records` node targeting
`FlowCodeEvalEntity` with no `queryExpression` and no `_sortFieldName`.
The agent's job (per the prompt) is to set both, then revert to this
state. The verifier's job is to prove the final state equals this state.
"""
import json
import os
import shutil
import subprocess
import sys


def uip(*args, capture=True):
    r = subprocess.run(["uip", *args], capture_output=capture, text=True)
    if r.returncode != 0:
        print(f"FAIL: uip {' '.join(args)}\n{r.stderr[:500] or r.stdout[:500]}",
              file=sys.stderr)
        sys.exit(r.returncode)
    return r


def uip_json(*args):
    r = uip(*args, "--output", "json")
    return json.loads(r.stdout)


def find_connection():
    """Return (connection_id, folder_key) for the first Enabled DF connection."""
    r = uip_json("is", "connections", "list", "uipath-uipath-dataservice",
                 "--all-folders",
                 "--output-filter",
                 "[?State=='Enabled'] | [0].{Id:Id, FolderKey:FolderKey}")
    data = r.get("Data") or {}
    if not data.get("Id"):
        print("FAIL: no Enabled uipath-uipath-dataservice connection found",
              file=sys.stderr)
        sys.exit(1)
    return data["Id"], data["FolderKey"]


def main():
    if os.path.exists("MovieReportSolution/MovieReportFlow/MovieReportFlow.flow"):
        print("OK: MovieReportFlow already scaffolded")
        return

    conn_id, folder_key = find_connection()

    uip("solution", "init", "MovieReportSolution")
    os.chdir("MovieReportSolution")
    uip("maestro", "flow", "init", "MovieReportFlow")
    os.chdir("MovieReportFlow")

    node_type = "uipath.connector.uipath-uipath-dataservice.query-entity-records"
    uip("maestro", "flow", "node", "add", "MovieReportFlow.flow", node_type,
        "--label", "Movie Report Query")

    # Discover the assigned node id
    with open("MovieReportFlow.flow") as f:
        doc = json.load(f)
    node_id = next(n["id"] for n in doc["nodes"] if n.get("type") == node_type)

    detail = json.dumps({
        "connectionId": conn_id,
        "folderKey": folder_key,
        "method": "POST",
        "endpoint": "/v2/{entityName}/qer",
        "pathParameters": {"entityName": "FlowCodeEvalEntity"},
        "queryParameters": {
            "start": 0, "limit": 100, "expansionLevel": 3, "isAscending": False
        },
        "customFieldsRequestDetails": {
            "objectActionName": "GenerateSchema",
            "parameterValues": [["entityName", "FlowCodeEvalEntity"]]
        }
    })
    uip("maestro", "flow", "node", "configure",
        "MovieReportFlow.flow", node_id, "--detail", detail)
    uip("maestro", "flow", "format", "MovieReportFlow.flow")

    # Snapshot the initial state next to the flow
    shutil.copyfile("MovieReportFlow.flow", "pre_state.flow")
    print(f"OK: scaffolded MovieReportFlow with node {node_id!r} (pre_state snapshot saved)")


if __name__ == "__main__":
    main()
