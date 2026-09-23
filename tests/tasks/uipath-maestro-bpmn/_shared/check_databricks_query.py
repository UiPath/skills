#!/usr/bin/env python3
"""DatabricksQuery (BPMN): structural checks for the JDBC Execute-Query sendTask.

Ported from Flow
`connector_features/jdbc_databricks_query/jdbc_databricks_query.yaml`'s
`check_databricks_query.py`: same scenario (a Databricks-via-JDBC aggregate
SQL query must route through the Database Hub / JDBC gateway connector
`uipath-uipath-jdbc`, not the native Databricks connector or a manual HTTP
call), translated from a JSON node/edge walk to an XML walk over the
registry-driven `Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4).

Catalog checked read-only via `uip is activities list uipath-uipath-jdbc
--output json`: the connector exposes exactly one curated activity capable
of running raw SQL -- `ExecuteQuerySynchronously` (ObjectName `query`,
MethodName `POST`, IsCurated `Yes`). Its record-CRUD siblings
(DeleteRecord/GetRecord/InsertRecord/ListAllRecords/ReplaceRecord) cannot
express the prompt's GROUP BY / HAVING / AVG / ORDER BY aggregate, so there
is no generic-CRUD alternate form to also accept here (contrast the Data
Service ports' curated-or-generic duality).

Assertion map (Flow -> BPMN):
  F check_databricks_query.py:66 assert_flow_uses_connector_target(JDBC_KEY)
    -- native `uipath.connector.<key>.*` node-type match
    (flow_check.py:743-744)
        -> connector_tasks() finds >=1 bpmn:sendTask carrying Intsvc.ActivityExecution
                                                                                  with context connectorKey ==
                                                                                  uipath-uipath-jdbc
  F check_databricks_query.py:72-78 _references_op (node type OR
    inputs.detail JSON contains "execute-query-synchronously")
        -> references_op() matches the catalog's curated objectName+method
                                                                                  ("query"/"POST") OR an
                                                                                  "executequerysynchronously" token
                                                                                  anywhere in
                                                                                  the node's inputs (name/value/text,
                                                                                  any depth)
  F check_databricks_query.py:83-86 native-Databricks guard
    (NATIVE_DATABRICKS_KEY not in any node type)
        -> no sendTask context connectorKey == uipath-databricks-databricks
  I  locate/parse .bpmn (file exists, well-formed XML)                       -> parse_bpmn("DatabricksQuery")
  T  inputs collected at any depth under uipath:activity (Flow read a
     single JSON `inputs.detail` dict; BPMN may nest context/path/query/
     body inputs)
         -> context_inputs() / node_text_blob() walk `.//uipath:input`
  T  curated objectName/method spelling as an alternate to a literal
     operation-name token match (registry curated activity; no
     generic-CRUD alternate form exists for this operation)                  -> references_op()

  DROPPED  connection/folderKey binding presence check -- Flow's
           assert_flow_uses_connector_target only enforces non-empty
           connection id + folder key on the generic core.action.http
           fallback branch (flow_check.py:757-764); the native
           `uipath.connector.*` node-type branch this task actually
           exercises returns on connectorKey match alone
           (flow_check.py:743-744), with no binding check.                    (not enforced by Flow for this node shape)
  DROPPED  require_no_private_connector_values / require_sequence_integrity
           / require_di_for_visible_elements                                  (not in Flow; `bpmn validate` criterion
           covers structure)
  DROPPED  a distinct "HTTP-fallback with connector auth" acceptance path
           (Flow's assert_flow_uses_connector_target has one for
           core.action.http nodes)                                            (no separate BPMN wrapper for
           connector-authenticated HTTP exists --
                                                                                   confirmed by CI run 35500726138:
                                                                                   all catalog
                                                                                   connector activities, including
                                                                                   HTTP-connector-mode ones, route
                                                                                   through the same
                                                                                   Intsvc.ActivityExecution shell)

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-uipath-jdbc.
  3. That node (or another uipath-uipath-jdbc node) references the Execute
     Query Synchronously operation.
  4. No sendTask carries connectorKey uipath-databricks-databricks (the
     native Databricks connector) -- Databricks SQL must route through the
     JDBC gateway, per the special-SDK-case the prompt exercises.

The prompt asks for an aggregate over the `employees` table (group by
department, keep departments with two or more employees, order by average
salary) -- a shape expressible only via raw SQL, not the generic record
activities. As in the Flow original, the exact SQL the agent authors is not
asserted here; this checker validates only the connector wiring described
above.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, context_inputs, context_value, elements, fail, has_type, parse_bpmn  # noqa: E402

JDBC_KEY = "uipath-uipath-jdbc"
NATIVE_DATABRICKS_KEY = "uipath-databricks-databricks"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
OP_TOKEN = "executequerysynchronously"


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def node_text_blob(task: ET.Element) -> str:
    # Serialize only the uipath:activity payload (context + inputs/outputs),
    # not the enclosing bpmn:sendTask's own id/name attributes -- a node's
    # free-text display name (e.g. a human label) is not wiring evidence and
    # must not satisfy the operation-token fallback below.
    activity = task.find(".//uipath:activity", NS)
    return ET.tostring(activity if activity is not None else task, encoding="unicode")


def connector_tasks(root: ET.Element, connector_key: str) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_type(task, ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == connector_key
    ]


def references_op(task: ET.Element) -> bool:
    object_name = context_value(task, "objectName").strip().lower()
    method = context_value(task, "method").strip().upper()
    if object_name == "query" and method == "POST":
        return True
    return OP_TOKEN in _normalize(node_text_blob(task))


def main() -> None:
    path, root = parse_bpmn("DatabricksQuery")

    jdbc_tasks = connector_tasks(root, JDBC_KEY)
    if not jdbc_tasks:
        fail(f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key {JDBC_KEY!r}")
    print(f"OK: {JDBC_KEY} sendTask present")

    if not any(references_op(task) for task in jdbc_tasks):
        fail(
            f"no {JDBC_KEY} node references the Execute Query Synchronously "
            "operation (expected objectName=query + method=POST, or an "
            "ExecuteQuerySynchronously token in the node's inputs)"
        )
    print(
        f"OK: {JDBC_KEY} node references Execute Query Synchronously "
        "(objectName=query, method=POST)"
    )

    native_tasks = connector_tasks(root, NATIVE_DATABRICKS_KEY)
    if native_tasks:
        fail(
            "process references the native Databricks connector "
            f"({NATIVE_DATABRICKS_KEY}) -- Databricks SQL must route through "
            "the JDBC gateway, not the native key"
        )
    print("OK: no native Databricks connector node present")

    print(
        f"OK: {path} wires {JDBC_KEY}.ExecuteQuerySynchronously with no "
        "native-Databricks fallback"
    )


if __name__ == "__main__":
    main()
