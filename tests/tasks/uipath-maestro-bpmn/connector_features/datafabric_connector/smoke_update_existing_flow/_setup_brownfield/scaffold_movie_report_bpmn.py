#!/usr/bin/env python3
"""Scaffold a valid `MovieReportBpmn` inside the coder-eval sandbox and
snapshot its initial state. Used by `smoke_update_existing_flow` (BPMN port)
to give the agent a real brownfield artifact to edit + revert.

Ported from Flow's `scaffold_movie_report_flow.py`. Flow builds the project
with structured CLI verbs (`flow init`, `flow node add`, `flow node
configure`); the BPMN CLI has no node-authoring verb (see
`uip maestro bpmn --help` -- only `init`/`format`/`validate`/`registry`/
`refresh`), so this scaffold builds the project with `uip maestro bpmn init`
and then hand-edits the generated XML the way
`skills/uipath-maestro-bpmn/references/registry-workflow.md` teaches an
agent to: fill a registry `xmlTemplate` shape and enrich a connector node
via `uip maestro bpmn registry get Intsvc.ActivityExecution --connection-id
<id> --object-name <object>`. The node shape and process-level bindings
below are modeled on a real CI-passing artifact for this exact activity
(`DataFabricSmokeQuery.bpmn`, Task_Query1: curated `QueryEntityRecordsCurated`
sendTask, `=bindings.<id>` connection reference, process-level
`<uipath:bindings>` block) with the query/sort inputs removed, since the
brownfield fixture must start with no filter and no sort.

Runs from `pre_run` inside the sandbox cwd. Requires an authenticated `uip`
session and a healthy `uipath-uipath-dataservice` connection.

After this script exits:
  - MovieReportSolution/MovieReportBpmn/MovieReportBpmn.bpmn exists and
    passes `uip maestro bpmn validate`
  - pre_state.bpmn (sibling of the .bpmn) is a byte-copy of the initial
    state that the verifier will diff against post-agent

The initial state has ONE `Intsvc.ActivityExecution` sendTask (curated
Query Entity Records, objectName `QueryEntityRecordsCurated`) targeting
`FlowCodeEvalEntity` with no `queryExpression` / filter input and no
`sortField` input (an `isAscending=false` flag is present, matching the
real curated activity's shape -- see `check_df_smoke_update_existing.py`
for why this is not itself "a sort"). The agent's job (per the prompt) is
to add a filter and a descending sort, then revert to this exact state.
The verifier's job is to prove the final state equals this state.
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


# Modeled on DataFabricSmokeQuery.bpmn's Task_Query1 (a real CI-passing
# QueryEntityRecordsCurated sendTask), with `queryExpression` and `sortField`
# omitted -- the brownfield fixture must start with no filter, no sort.
QUERY_TASK_XML = """    <bpmn:sendTask id="Task_Query" name="Movie Report Query">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-dataservice" />
            <uipath:input name="connection" type="string" value="=bindings.Binding_DataFabricConnection" />
            <uipath:input name="folderKey" type="string" value="=bindings.Binding_DataFabricFolder" />
            <uipath:input name="operation" type="string" value="Create" />
            <uipath:input name="objectName" type="string" value="QueryEntityRecordsCurated" />
            <uipath:input name="method" type="string" value="POST" />
            <uipath:input name="path" type="string" value="/v2/{entityName}/qer" />
            <uipath:input name="activityConfigurationVersion" type="string" value="v1" />
            <uipath:input name="metadata" type="json"><![CDATA[{}]]></uipath:input>
          </uipath:context>
          <uipath:input target="path" name="entityName" type="string" value="FlowCodeEvalEntity" />
          <uipath:input target="query" name="start" type="integer" value="0" />
          <uipath:input target="query" name="limit" type="integer" value="100" />
          <uipath:input target="query" name="expansionLevel" type="integer" value="3" />
          <uipath:input target="query" name="isAscending" type="boolean" value="false" />
          <uipath:output name="response" type="jsonSchema" source="=response" var="Var_MovieReportQuery" />
        </uipath:activity>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Start_Query</bpmn:incoming>
      <bpmn:outgoing>Flow_Query_End</bpmn:outgoing>
    </bpmn:sendTask>
    <bpmn:sequenceFlow id="Flow_Start_Query" sourceRef="Event_start" targetRef="Task_Query" />
    <bpmn:sequenceFlow id="Flow_Query_End" sourceRef="Task_Query" targetRef="_Implicit_EndEvent" />
"""

VARIABLES_XML = (
    '<uipath:variables version="v1">'
    '<uipath:inputOutput id="Var_MovieReportQuery" name="Movie Report Query" '
    'type="jsonSchema" elementId="Task_Query" />'
    "</uipath:variables>"
)


def bindings_xml(conn_id: str, folder_key: str) -> str:
    return (
        '<uipath:bindings version="v1">'
        f'<uipath:binding id="Binding_DataFabricConnection" resource="Connection" '
        f'propertyAttribute="ConnectionId" resourceKey="{conn_id}" default="{conn_id}" />'
        f'<uipath:binding id="Binding_DataFabricFolder" resource="Connection" '
        f'propertyAttribute="folderKey" resourceKey="{conn_id}" default="{folder_key}" />'
        "</uipath:bindings>"
    )


def main():
    if os.path.exists("MovieReportSolution/MovieReportBpmn/MovieReportBpmn.bpmn"):
        print("OK: MovieReportBpmn already scaffolded")
        return

    conn_id, folder_key = find_connection()

    uip("solution", "init", "MovieReportSolution")
    os.chdir("MovieReportSolution")
    uip("maestro", "bpmn", "init", "MovieReportBpmn")
    os.chdir("MovieReportBpmn")

    with open("MovieReportBpmn.bpmn") as f:
        text = f.read()

    # `uip maestro bpmn init` boilerplate: manual start -> implicit end,
    # empty <uipath:variables>/<uipath:bindings>. Splice the connector node
    # in between and populate the two extension blocks. Every replaced
    # string is asserted present first so a CLI boilerplate change fails
    # loudly here instead of silently producing a broken fixture.
    replacements = [
        ('<uipath:variables version="v1" />', VARIABLES_XML),
        ('<uipath:bindings version="v1" />', bindings_xml(conn_id, folder_key)),
        (
            "<bpmn:outgoing>_Implicit_EndEvent_Flow</bpmn:outgoing>",
            "<bpmn:outgoing>Flow_Start_Query</bpmn:outgoing>",
        ),
        (
            "<bpmn:incoming>_Implicit_EndEvent_Flow</bpmn:incoming>",
            "<bpmn:incoming>Flow_Query_End</bpmn:incoming>",
        ),
        (
            '<bpmn:sequenceFlow id="_Implicit_EndEvent_Flow" sourceRef="Event_start" '
            'targetRef="_Implicit_EndEvent" />',
            QUERY_TASK_XML.rstrip("\n"),
        ),
    ]

    for old, new in replacements:
        if old not in text:
            print(f"FAIL: expected uip maestro bpmn init boilerplate not found: {old!r}",
                  file=sys.stderr)
            sys.exit(1)
        text = text.replace(old, new, 1)

    with open("MovieReportBpmn.bpmn", "w") as f:
        f.write(text)

    uip("maestro", "bpmn", "format", "MovieReportBpmn.bpmn")

    # Snapshot the initial state next to the .bpmn
    shutil.copyfile("MovieReportBpmn.bpmn", "pre_state.bpmn")
    print("OK: scaffolded MovieReportBpmn with Task_Query (pre_state snapshot saved)")


if __name__ == "__main__":
    main()
