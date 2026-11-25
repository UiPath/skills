#!/usr/bin/env python3
"""Scaffold a valid `MovieReportFlow` inside the coder-eval sandbox and
snapshot its initial state. Used by `smoke_update_existing_flow` to give
the agent a real brownfield artifact to edit + revert.

Runs from `pre_run` inside the sandbox cwd. Requires an authenticated `uip`
session and a healthy `uipath-uipath-dataservice` connection.

The flow body is a committed fixture (`movie_report_flow/`), not built with
CLI node commands: those (`flow node add` / `node configure`) are being retired.
The fixture is what `node add` + `node configure` + `format` wrote on
2026-11-23 (CLI 1.206.0), with the tenant values replaced by placeholders.
This script fills them in from the live connection, so the fixture works on
any tenant:

  __DF_CONNECTION_ID__    the connection's Id
  __DF_FOLDER_KEY__       the connection's FolderKey
  __DF_CONNECTION_NAME__  the connection's Name (also the resource file name)
  __FLOW_ID__             the id `flow init` gave this project
  __START_UNIQUE_ID__     the manual trigger's `uniqueId` from `flow init`
  __ENTRY_POINT_ID__      the manual trigger's `entryPointId` from `flow init`

Values are JSON-string-escaped before they are pasted into the templates.
The fixture freezes the connector `definitions[]` and `connectorVersion` of
the capture day; that is fine for a brownfield starting point (the checker
compares against pre_state.flow), but it will not pick up later connector or
registry changes on its own. Regenerate it if the task starts failing on a
stale definition.

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
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "movie_report_flow"
NODE_TYPE = "uipath.connector.uipath-uipath-dataservice.query-entity-records"


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
    """Return {Id, FolderKey, Name} of the first Enabled DF connection."""
    r = uip_json("is", "connections", "list", "uipath-uipath-dataservice",
                 "--all-folders",
                 "--output-filter",
                 "[?State=='Enabled'] | [0].{Id:Id, FolderKey:FolderKey, Name:Name}")
    data = r.get("Data") or {}
    if not data.get("Id"):
        print("FAIL: no Enabled uipath-uipath-dataservice connection found",
              file=sys.stderr)
        sys.exit(1)
    return data


def render(template, values):
    """Read a fixture template and fill in every placeholder."""
    text = (FIXTURE / template).read_text()
    for key, value in values.items():
        text = text.replace(key, json.dumps(value)[1:-1])
    if re.search(r"__[A-Z_]+__", text):
        print(f"FAIL: unfilled placeholder in {template}", file=sys.stderr)
        sys.exit(1)
    return text


def main():
    if os.path.exists("MovieReportSolution/MovieReportFlow/MovieReportFlow.flow"):
        print("OK: MovieReportFlow already scaffolded")
        return

    conn = find_connection()

    uip("solution", "init", "MovieReportSolution")
    os.chdir("MovieReportSolution")
    uip("maestro", "flow", "init", "MovieReportFlow")
    os.chdir("MovieReportFlow")

    with open("MovieReportFlow.flow") as f:
        inited = json.load(f)
    start = next(n for n in inited["nodes"] if n.get("type") == "core.trigger.manual")
    if "/" in conn["Name"] or "\\" in conn["Name"]:
        print(f"FAIL: connection name {conn['Name']!r} cannot be a file name", file=sys.stderr)
        sys.exit(1)
    values = {
        "__DF_CONNECTION_ID__": conn["Id"],
        "__DF_FOLDER_KEY__": conn["FolderKey"],
        "__DF_CONNECTION_NAME__": conn["Name"],
        "__FLOW_ID__": inited["id"],
        "__START_UNIQUE_ID__": start["uniqueId"],
        "__ENTRY_POINT_ID__": start["inputs"]["entryPointId"],
    }
    Path("MovieReportFlow.flow").write_text(
        render("MovieReportFlow.flow.template.json", values))
    Path("bindings_v2.json").write_text(
        render("bindings_v2.template.json", values))
    conn_dir = Path("../resources/solution_folder/connection/uipath-uipath-dataservice")
    conn_dir.mkdir(parents=True, exist_ok=True)
    (conn_dir / f"{conn['Name']}.json").write_text(
        render("connection.template.json", values))
    uip("maestro", "flow", "format", "MovieReportFlow.flow")

    with open("MovieReportFlow.flow") as f:
        node_id = next(n["id"] for n in json.load(f)["nodes"] if n.get("type") == NODE_TYPE)

    # Snapshot the initial state next to the flow
    shutil.copyfile("MovieReportFlow.flow", "pre_state.flow")
    print(f"OK: scaffolded MovieReportFlow with node {node_id!r} (pre_state snapshot saved)")


if __name__ == "__main__":
    main()
