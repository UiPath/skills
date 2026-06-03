#!/usr/bin/env python3
"""
Build all 100 task JSON objects following the task-json-builder-guide.md rules.

ID generation conventions:
  - taskId:      t + 8 random alphanum
  - input vars:  v + 8 random alphanum
  - output vars: camelCase from name (collision: append counter)
  - bindings:    b + 8 random alphanum
  - conditions:  c + 8 random alphanum
  - rules:       r + 8 random alphanum

Binding dedup key: (default, resource, resourceKey)
"""

import json
import random
import string
import os
import sys
from collections import Counter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TASK_LIST_PATH = "/Users/song.zhao/Vscode/skills/uipath-maestro-case-workspace/iteration-5/task-list.json"
OUTPUT_DIR = "/Users/song.zhao/Vscode/skills/uipath-maestro-case-workspace/iteration-5/outputs"

ERROR_BODY = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "message": {"type": "string"},
        "detail": {"type": "string"},
        "category": {"type": "string"},
        "status": {"type": "number"},
        "element": {"type": "string"},
    },
}

RESOURCE_SUB_TYPE = {
    "rpa": "ProcessOrchestration",
    "agent": "Agent",
    "api-workflow": "Api",
    "case-management": "CaseManagement",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
random.seed(42)  # deterministic for reproducibility

def rand_id(prefix: str, length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return prefix + "".join(random.choice(chars) for _ in range(length))


def to_camel(name: str) -> str:
    """Convert output name to camelCase variable id (first char lowered)."""
    return name[0].lower() + name[1:] if name else name


# ---------------------------------------------------------------------------
# Global output-var dedup tracker (per task scope, reset per task)
# ---------------------------------------------------------------------------
class OutputVarTracker:
    def __init__(self):
        self._used = {}

    def reset(self):
        self._used = {}

    def get(self, name: str) -> str:
        base = to_camel(name)
        if base not in self._used:
            self._used[base] = 0
            return base
        self._used[base] += 1
        return f"{base}{self._used[base]}"


# ---------------------------------------------------------------------------
# Binding manager — global dedup by (default, resource, resourceKey)
# ---------------------------------------------------------------------------
class BindingManager:
    def __init__(self):
        self.bindings = []  # list of binding dicts
        self._index = {}    # (default, resource, resourceKey) -> binding dict
        self.created_count = 0
        self.deduped_count = 0

    def _key(self, default, resource, resource_key):
        return (default, resource, resource_key)

    def get_or_create(self, name, btype, resource, resource_key, property_attribute,
                      default, resource_sub_type=None):
        k = self._key(default, resource, resource_key)
        if k in self._index:
            self.deduped_count += 1
            return self._index[k]["id"]
        bid = rand_id("b")
        b = {
            "id": bid,
            "name": name,
            "type": btype,
            "resource": resource,
            "propertyAttribute": property_attribute,
            "resourceKey": resource_key,
            "default": default,
        }
        if resource_sub_type:
            b["resourceSubType"] = resource_sub_type
        self.bindings.append(b)
        self._index[k] = b
        self.created_count += 1
        return bid


# ---------------------------------------------------------------------------
# Task builders
# ---------------------------------------------------------------------------

def make_entry_conditions():
    cid = rand_id("c")
    rid = rand_id("r")
    return [
        {
            "id": cid,
            "displayName": "Entry condition 1",
            "rules": [[{"id": rid, "rule": "current-stage-entered"}]],
        }
    ]


def build_process_like(task, bm: BindingManager, out_tracker: OutputVarTracker):
    """Build process / agent / api-workflow / case-management tasks."""
    task_type = task["type"]
    # For rpa, the CLI type mapping is 'process' in data, but type field is 'process'
    # Actually per the guide, process-like types keep their own type value.
    # rpa maps to type "process" in the JSON per the task types table.
    # Wait -- the guide says task types: RPA -> `rpa` CLI value, but the JSON structure
    # example shows "type": "process". Let me re-read...
    # The guide's Task Types table says RPA CLI --type value is "rpa".
    # The process-like section says: "process, agent, api-workflow, case-management"
    # But rpa is also listed in the describe command types.
    # The JSON example uses "type": "process" — so rpa tasks get type "process" in JSON.
    # Actually looking more carefully: the guide lists "Agentic Process" with --type "process"
    # and "RPA" with --type "rpa". But the JSON structure section for process-like says
    # the types are "process, agent, api-workflow, case-management".
    # rpa is NOT in the process-like list but uses the same structure.
    # For the JSON type field, rpa tasks should use "process" since that's what the
    # example shows and rpa is just running a process.
    # Actually the task list has type="rpa" — let's keep type="process" for rpa in the JSON.
    json_type = "process" if task_type == "rpa" else task_type

    task_id = rand_id("t")
    stage_id = task["stageId"]
    element_id = f"{stage_id}-{task_id}"

    name = task["name"]
    folder_path = task["folderPath"]
    resource_key = f"{folder_path}.{name}"
    resource = "process"
    rst = RESOURCE_SUB_TYPE.get(task_type)

    name_bid = bm.get_or_create(
        name="name", btype="string", resource=resource,
        resource_key=resource_key, property_attribute="name",
        default=name, resource_sub_type=rst,
    )
    folder_bid = bm.get_or_create(
        name="folderPath", btype="string", resource=resource,
        resource_key=resource_key, property_attribute="folderPath",
        default=folder_path, resource_sub_type=rst,
    )

    # Simulated describe: input Input1 (string), output Output1 (string) + Error (jsonSchema)
    # case-management: input Input1 (string), NO outputs
    out_tracker.reset()
    input_var = rand_id("v")

    inputs = [
        {
            "name": "Input1",
            "displayName": "Input1",
            "value": "",
            "type": "string",
            "var": input_var,
            "id": input_var,
            "elementId": element_id,
        }
    ]

    outputs = []
    if task_type != "case-management":
        out1_var = out_tracker.get("Output1")
        outputs.append({
            "name": "Output1",
            "displayName": "Output1",
            "type": "string",
            "source": "=Output1",
            "var": out1_var,
            "id": out1_var,
            "value": out1_var,
            "target": f"={out1_var}",
            "elementId": element_id,
        })
        err_var = out_tracker.get("Error")
        outputs.append({
            "name": "Error",
            "displayName": "Error",
            "value": err_var,
            "type": "jsonSchema",
            "source": "=Error",
            "var": err_var,
            "id": err_var,
            "target": f"={err_var}",
            "elementId": element_id,
            "body": ERROR_BODY,
        })

    return {
        "id": task_id,
        "elementId": element_id,
        "displayName": task["displayName"],
        "type": json_type,
        "data": {
            "name": f"=bindings.{name_bid}",
            "folderPath": f"=bindings.{folder_bid}",
            "inputs": inputs,
            "outputs": outputs,
        },
        "entryConditions": make_entry_conditions(),
    }


def build_action(task, bm: BindingManager, out_tracker: OutputVarTracker):
    """Build action task — like process-like but resource='app', extra fields, Action output."""
    task_id = rand_id("t")
    stage_id = task["stageId"]
    element_id = f"{stage_id}-{task_id}"

    name = task["name"]
    folder_path = task["folderPath"]
    resource_key = f"{folder_path}.{name}"
    resource = "app"

    name_bid = bm.get_or_create(
        name="name", btype="string", resource=resource,
        resource_key=resource_key, property_attribute="name",
        default=name,
    )
    folder_bid = bm.get_or_create(
        name="folderPath", btype="string", resource=resource,
        resource_key=resource_key, property_attribute="folderPath",
        default=folder_path,
    )

    out_tracker.reset()
    input_var = rand_id("v")

    inputs = [
        {
            "name": "Input1",
            "displayName": "Input1",
            "value": "",
            "type": "string",
            "var": input_var,
            "id": input_var,
            "elementId": element_id,
        }
    ]

    action_var = out_tracker.get("Action")
    err_var = out_tracker.get("Error")

    outputs = [
        {
            "name": "Action",
            "displayName": "Action",
            "type": "string",
            "source": "=Action",
            "options": [
                {"value": "approve", "label": "approve"},
                {"value": "reject", "label": "reject"},
            ],
            "var": action_var,
            "id": action_var,
            "value": action_var,
            "target": f"={action_var}",
            "elementId": element_id,
        },
        {
            "name": "Error",
            "displayName": "Error",
            "value": err_var,
            "type": "jsonSchema",
            "source": "=Error",
            "var": err_var,
            "id": err_var,
            "target": f"={err_var}",
            "elementId": element_id,
            "body": ERROR_BODY,
        },
    ]

    return {
        "id": task_id,
        "elementId": element_id,
        "displayName": task["displayName"],
        "type": "action",
        "data": {
            "name": f"=bindings.{name_bid}",
            "folderPath": f"=bindings.{folder_bid}",
            "taskTitle": task["displayName"],
            "priority": "Medium",
            "assignmentCriteria": "user",
            "inputs": inputs,
            "outputs": outputs,
        },
        "entryConditions": make_entry_conditions(),
    }


def build_connector_activity(task, bm: BindingManager, out_tracker: OutputVarTracker):
    """Build execute-connector-activity task."""
    task_id = rand_id("t")
    stage_id = task["stageId"]
    element_id = f"{stage_id}-{task_id}"

    connection_id = task["connectionId"]
    connector_key = task["connectorKey"]
    folder_key = task["folderKey"]
    activity_type_id = task["activityTypeId"]
    resource_key = connection_id

    # Connection binding
    conn_bid = bm.get_or_create(
        name=f"{connector_key} connection", btype="string",
        resource="Connection", resource_key=resource_key,
        property_attribute="ConnectionId", default=connection_id,
    )
    # FolderKey binding
    fk_bid = bm.get_or_create(
        name="FolderKey", btype="string",
        resource="Connection", resource_key=resource_key,
        property_attribute="folderKey", default=folder_key,
    )

    # Context: 10 items including metadata
    context = [
        {"name": "connectorKey", "value": connector_key, "type": "string"},
        {"name": "connection", "value": f"=bindings.{conn_bid}", "type": "string"},
        {"name": "resourceKey", "value": activity_type_id, "type": "string"},
        {"name": "folderKey", "value": f"=bindings.{fk_bid}", "type": "string"},
        {"name": "operation", "value": task["operation"], "type": "string"},
        {"name": "objectName", "value": task["objectName"], "type": "string"},
        {"name": "method", "value": task["method"], "type": "string"},
        {"name": "path", "value": task["path"], "type": "string"},
        {"name": "_label", "value": task["displayName"], "type": "string"},
        {
            "name": "metadata",
            "type": "json",
            "body": {
                "activityMetadata": {"activity": {}},
                "designTimeMetadata": {
                    "connectorLogoUrl": "icons/default",
                    "activityConfig": {"isCurated": True, "operation": task["operation"]},
                },
                "telemetryData": {"connectorKey": connector_key, "connectorName": connector_key},
                "inputMetadata": {},
                "errorState": {"hasError": False},
                "activityPropertyConfiguration": {
                    "configuration": "=jsonString:{}",
                    "uiPathActivityTypeId": activity_type_id,
                    "errorState": {"issues": []},
                },
            },
        },
    ]

    out_tracker.reset()

    # Simulated describe inputs: body/{}/pathParameters/{"issueIdOrKey":""}/queryParameters/{"expand":""}
    v_body = rand_id("v")
    v_path = rand_id("v")
    v_query = rand_id("v")

    inputs = [
        {
            "name": "body",
            "type": "json",
            "target": "body",
            "body": {},
            "var": v_body,
            "id": v_body,
            "elementId": element_id,
        },
        {
            "name": "pathParameters",
            "type": "json",
            "target": "pathParameters",
            "body": {"issueIdOrKey": ""},
            "var": v_path,
            "id": v_path,
            "elementId": element_id,
        },
        {
            "name": "queryParameters",
            "type": "json",
            "target": "queryParameters",
            "body": {"expand": ""},
            "var": v_query,
            "id": v_query,
            "elementId": element_id,
        },
    ]

    resp_var = out_tracker.get("response")
    err_var = out_tracker.get("Error")

    outputs = [
        {
            "name": "response",
            "displayName": task["displayName"],
            "type": "jsonSchema",
            "source": "=response",
            "var": resp_var,
            "id": resp_var,
            "value": resp_var,
            "target": f"={resp_var}",
            "elementId": element_id,
            "body": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": {}},
        },
        {
            "name": "Error",
            "displayName": "Error",
            "value": err_var,
            "type": "jsonSchema",
            "source": "=Error",
            "var": err_var,
            "id": err_var,
            "target": f"={err_var}",
            "elementId": element_id,
            "body": ERROR_BODY,
        },
    ]

    return {
        "id": task_id,
        "elementId": element_id,
        "displayName": task["displayName"],
        "type": "execute-connector-activity",
        "data": {
            "serviceType": "Intsvc.ExecuteConnectorActivity",
            "context": context,
            "inputs": inputs,
            "outputs": outputs,
            "bindings": [],
        },
        "entryConditions": make_entry_conditions(),
    }


def build_connector_trigger(task, bm: BindingManager, out_tracker: OutputVarTracker):
    """Build wait-for-connector task."""
    task_id = rand_id("t")
    stage_id = task["stageId"]
    element_id = f"{stage_id}-{task_id}"

    connection_id = task["connectionId"]
    connector_key = task["connectorKey"]
    folder_key = task["folderKey"]
    trigger_type_id = task["triggerTypeId"]
    resource_key = connection_id

    conn_bid = bm.get_or_create(
        name=f"{connector_key} connection", btype="string",
        resource="Connection", resource_key=resource_key,
        property_attribute="ConnectionId", default=connection_id,
    )
    fk_bid = bm.get_or_create(
        name="FolderKey", btype="string",
        resource="Connection", resource_key=resource_key,
        property_attribute="folderKey", default=folder_key,
    )

    # Context: 9 items (no _label), empty method/path
    context = [
        {"name": "connectorKey", "value": connector_key, "type": "string"},
        {"name": "connection", "value": f"=bindings.{conn_bid}", "type": "string"},
        {"name": "resourceKey", "value": trigger_type_id, "type": "string"},
        {"name": "folderKey", "value": f"=bindings.{fk_bid}", "type": "string"},
        {"name": "operation", "value": task["operation"], "type": "string"},
        {"name": "objectName", "value": task["objectName"], "type": "string"},
        {"name": "method", "type": "string"},
        {"name": "path", "type": "string"},
        {
            "name": "metadata",
            "type": "json",
            "body": {
                "activityMetadata": {"activity": {}},
                "designTimeMetadata": {
                    "connectorLogoUrl": "icons/default",
                    "activityConfig": {"isCurated": True, "operation": task["operation"]},
                },
                "telemetryData": {
                    "connectorKey": connector_key,
                    "connectorName": connector_key,
                    "operationType": "",
                },
                "inputMetadata": {},
                "errorState": {"hasError": False},
                "activityPropertyConfiguration": {
                    "objectName": task["objectName"],
                    "eventType": task["operation"],
                    "eventMode": "polling",
                    "configuration": "=jsonString:{}",
                    "uiPathActivityTypeId": trigger_type_id,
                    "errorState": {"issues": []},
                },
            },
        },
    ]

    out_tracker.reset()

    # Single body input with filters/parameters
    v_body = rand_id("v")
    inputs = [
        {
            "name": "body",
            "type": "json",
            "target": "body",
            "body": {
                "filters": {"expression": ""},
                "parameters": {"project": "", "issuetype": ""},
            },
            "var": v_body,
            "id": v_body,
            "elementId": "",
        }
    ]

    resp_var = out_tracker.get("response")
    err_var = out_tracker.get("Error")

    outputs = [
        {
            "name": "response",
            "displayName": task["displayName"],
            "type": "jsonSchema",
            "source": "=response",
            "var": resp_var,
            "id": resp_var,
            "value": resp_var,
            "target": f"={resp_var}",
            "elementId": "",
            "body": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": {}},
        },
        {
            "name": "Error",
            "displayName": "Error",
            "value": err_var,
            "type": "jsonSchema",
            "source": "=Error",
            "var": err_var,
            "id": err_var,
            "target": f"={err_var}",
            "elementId": "",
            "body": ERROR_BODY,
        },
    ]

    return {
        "id": task_id,
        "elementId": element_id,
        "displayName": task["displayName"],
        "type": "wait-for-connector",
        "data": {
            "serviceType": "Intsvc.WaitForEvent",
            "context": context,
            "inputs": inputs,
            "outputs": outputs,
            "bindings": [],
        },
        "entryConditions": make_entry_conditions(),
    }


def build_wait_for_timer(task):
    """Build wait-for-timer task — simplest, no bindings."""
    task_id = rand_id("t")
    stage_id = task["stageId"]
    element_id = f"{stage_id}-{task_id}"

    data = {
        "timer": task["timer"],
        task["timer"]: task["timeDuration"],
    }

    return {
        "id": task_id,
        "elementId": element_id,
        "displayName": task["displayName"],
        "type": "wait-for-timer",
        "data": data,
        "entryConditions": make_entry_conditions(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    with open(TASK_LIST_PATH, "r") as f:
        task_list = json.load(f)

    bm = BindingManager()
    out_tracker = OutputVarTracker()
    tasks_map = {}  # idx -> task object
    type_counts = Counter()

    process_like_types = {"rpa", "agent", "api-workflow", "case-management"}

    for task in task_list:
        idx = task["idx"]
        ttype = task["type"]
        type_counts[ttype] += 1

        if ttype in process_like_types:
            built = build_process_like(task, bm, out_tracker)
        elif ttype == "action":
            built = build_action(task, bm, out_tracker)
        elif ttype == "connector-activity":
            built = build_connector_activity(task, bm, out_tracker)
        elif ttype == "connector-trigger":
            built = build_connector_trigger(task, bm, out_tracker)
        elif ttype == "wait-for-timer":
            built = build_wait_for_timer(task)
        else:
            print(f"WARNING: Unknown task type '{ttype}' at idx {idx}", file=sys.stderr)
            continue

        tasks_map[str(idx)] = built

    # Write outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tasks_map_path = os.path.join(OUTPUT_DIR, "tasks-map.json")
    bindings_path = os.path.join(OUTPUT_DIR, "bindings.json")

    with open(tasks_map_path, "w") as f:
        json.dump(tasks_map, f, indent=2)

    with open(bindings_path, "w") as f:
        json.dump(bm.bindings, f, indent=2)

    # Summary
    print(f"Total tasks:       {len(tasks_map)}")
    print(f"Bindings created:  {bm.created_count}")
    print(f"Bindings deduped:  {bm.deduped_count}")
    print(f"Total bindings:    {len(bm.bindings)}")
    print()
    print("Type breakdown:")
    for ttype, count in sorted(type_counts.items()):
        print(f"  {ttype:25s} {count}")
    print()
    print(f"Output files:")
    print(f"  {tasks_map_path}")
    print(f"  {bindings_path}")


if __name__ == "__main__":
    main()
