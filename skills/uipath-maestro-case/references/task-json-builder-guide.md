# Task JSON Builder Guide

This reference describes how to build the task JSON data object for each supported task type in a case management JSON file. The parent skill invokes this procedure when adding tasks to stages.

## Overview

Building a task involves two steps:

1. **Fetch input/output metadata** — Use `uip case tasks describe` to get the input/output schema for a given task type and type ID. This returns what fields the task needs as input and what it produces as output.
2. **Build the task object** — Construct the full task JSON with generated IDs, element IDs, display names, and the fetched metadata.

## Task Types

| Task type | CLI `--type` value | Description |
|---|---|---|
| Process | `process` | Run a UiPath process |
| Action | `action` | Human action / approval task |
| Agent | `agent` | Run an AI agent |
| API Workflow | `api-workflow` | Run an API workflow |
| Agentic Process | `external-agent` | Run an external agentic process |
| Case Management | `case-management` | Run a sub-case |
| Wait for Connector | `wait-for-connector` | Wait for a connector event (trigger) |
| Execute Connector | `execute-connector-activity` | Execute a connector action |
| Wait for Timer | `wait-for-timer` | Wait for a time condition |

---

## Step 1: Fetch Input/Output Metadata

Before building the task, fetch its input/output schema to know what fields it expects.

### For process-like tasks (process, agent, action, api-workflow, case-management)

```bash
uip case tasks describe --type <TASK_TYPE> --id <ENTITY_KEY> --output json
```

- `--type`: One of `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`
- `--id`: The entityKey (for process types) or action-app ID (for action type)

### For connector tasks

```bash
uip case tasks describe --type connector-activity --id <ACTIVITY_TYPE_ID> --connection-id <CONNECTION_UUID> --output json
uip case tasks describe --type connector-trigger --id <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> --output json
```

- `--id`: The `uiPathActivityTypeId` UUID from the TypeCache
- `--connection-id`: The connection UUID

### Response format

```json
{
  "inputs": [
    { "name": "Content", "type": "string", "displayName": "Content", "value": "", ... },
    ...
  ],
  "outputs": [
    { "name": "Error", "type": "jsonSchema", "displayName": "Error", "source": "=Error", ... },
    ...
  ]
}
```

The `describe` response may include a `required` field on inputs. Strip `required` before building the task JSON — it is not part of the task data structure.

---

## Step 2: Build Task JSON

### ID Generation

- **Task ID**: `t` prefix + 8 random alphanumeric chars (e.g., `tNEHpGDYd`)
- **Element ID**: `{stageId}-{taskId}` (e.g., `stage_1-tNEHpGDYd`)
- **Variable IDs for inputs**: `v` prefix + 8 random alphanumeric chars (e.g., `v3YSGGSc9`)
- **Variable IDs for outputs**: Unique camelCase derived from output name (e.g., `error`, `action`, `comment`). If collision, append counter (e.g., `error1`)
- **Binding IDs**: `b` prefix + 8 random alphanumeric chars (e.g., `bXYZ1234`)

### UiPathBinding Schema

```typescript
export interface UiPathBinding {
  id: string;
  name: string;
  type: string;
  resource: string;           // "Connection" | "process" | "app" | "queue"
  resourceKey: string;        // e.g., "folderPath.ProcessName" or connection UUID
  propertyAttribute: string;  // "name" | "folderPath" | "ConnectionId" | "folderKey" | "Key"
  resourceSubType?: string;   // "ProcessOrchestration" | "Agent" | "Api" | "CaseManagement"
  default?: string;
}
```

### Common BaseTask Fields

Every task shares these fields:

```json
{
  "id": "<taskId>",
  "elementId": "<stageId>-<taskId>",
  "displayName": "<display name>",
  "type": "<task type>",
  "data": { ... },
  "entryConditions": [
    {
      "id": "<conditionId>",
      "displayName": "Entry condition 1",
      "rules": [[{ "id": "<ruleId>", "rule": "current-stage-entered" }]]
    }
  ]
}
```

Optional fields: `shouldRunOnReEntry`, `skipCondition`.

---

## Process-like Tasks

These task types share the same data structure: `process`, `agent`, `api-workflow`, `case-management`.

### Build procedure

1. Generate task ID and element ID
2. Fetch metadata via `uip case tasks describe --type <TYPE> --id <ENTITY_KEY> --output json`
3. Create name + folderPath bindings and set `data.name` / `data.folderPath` to `=bindings.<id>` references (see Binding Construction below)

### Task JSON structure

```json
{
  "id": "tABCDEFGH",
  "elementId": "stage_1-tABCDEFGH",
  "displayName": "Run MyProcess",
  "type": "process",
  "data": {
    "name": "=bindings.bXYZ12345",
    "folderPath": "=bindings.bABC67890",
    "inputs": [
      {
        "name": "InputArg",
        "displayName": "InputArg",
        "value": "",
        "type": "string",
        "var": "vRaNdOmId",
        "id": "vRaNdOmId",
        "elementId": "stage_1-tABCDEFGH"
      }
    ],
    "outputs": [
      {
        "name": "OutputArg",
        "displayName": "OutputArg",
        "type": "string",
        "source": "=OutputArg",
        "var": "outputArg",
        "id": "outputArg",
        "value": "outputArg",
        "target": "=outputArg",
        "elementId": "stage_1-tABCDEFGH"
      },
      {
        "name": "Error",
        "displayName": "Error",
        "value": "error",
        "type": "jsonSchema",
        "source": "=Error",
        "var": "error",
        "id": "error",
        "target": "=error",
        "elementId": "stage_1-tABCDEFGH",
        "body": {
          "type": "object",
          "properties": {
            "code": { "type": "string" },
            "message": { "type": "string" },
            "detail": { "type": "string" },
            "category": { "type": "string" },
            "status": { "type": "number" },
            "element": { "type": "string" }
          }
        }
      }
    ]
  }
}
```

### Process-like Binding Construction

Create name + folderPath bindings when building the task. Dedup against existing `root.data.uipath.bindings[]`.

1. Determine `resource`: `"process"` for process/agent/api-workflow/case-management, `"app"` for action
2. Compute `resourceKey` = `"{folderPath}.{name}"`
3. Check dedup: does a binding with the same (`default`, `resource`, `resourceKey`) already exist in `root.data.uipath.bindings[]`?
4. If found, reuse the existing binding ID
5. If not, create two new bindings and push to `root.data.uipath.bindings[]`:
   ```json
   { "id": "b<random>", "name": "name", "type": "string", "resource": "<resource>",
     "propertyAttribute": "name", "resourceKey": "<folderPath>.<name>", "default": "<name>" }
   { "id": "b<random>", "name": "folderPath", "type": "string", "resource": "<resource>",
     "propertyAttribute": "folderPath", "resourceKey": "<folderPath>.<name>", "default": "<folderPath>" }
   ```
6. Set `data.name` = `"=bindings.<nameBindingId>"`, `data.folderPath` = `"=bindings.<folderPathBindingId>"`

`resourceSubType` values by task type:
- `process` → `"ProcessOrchestration"`
- `agent` → `"Agent"`
- `api-workflow` → `"Api"`
- `case-management` → `"CaseManagement"`

**Dedup example:** Two tasks referencing the same process:
- Task A creates binding `bXYZ` for `"MyProcess"` → `taskA.data.name = "=bindings.bXYZ"`
- Task B finds `bXYZ` already exists for `("MyProcess", "process", "Shared.MyProcess")` → `taskB.data.name = "=bindings.bXYZ"`

---

## Action Task

Same as process-like, but with additional fields in `data`. Uses `resource: "app"` for bindings (not `"process"`).

```json
{
  "type": "action",
  "data": {
    "name": "=bindings.bXYZ12345",
    "folderPath": "=bindings.bABC67890",
    "taskTitle": "Approval Request",
    "priority": "Medium",
    "assignmentCriteria": "user",
    "inputs": [ ... ],
    "outputs": [
      {
        "name": "Action",
        "displayName": "Action",
        "type": "string",
        "source": "=Action",
        "options": [
          { "value": "approve", "label": "approve" },
          { "value": "reject", "label": "reject" }
        ],
        ...
      },
      { "name": "Error", ... }
    ]
  }
}
```

The `Action` output has its type derived from the first outcome of the action schema. Outcome options are included in the `options` array.

Binding construction follows the same process-like pattern above, with `resource: "app"`.

---

## Connector Activity Task (execute-connector-activity)

### Build procedure

1. Generate task ID and element ID
2. Run `uip case tasks add-connector <FILE> <STAGE_ID> --type activity --type-id <UUID> --connection-id <CONN_UUID> --output json`
3. Or build manually using enrichment data

### Task JSON structure

```json
{
  "id": "tABCDEFGH",
  "elementId": "stage_1-tABCDEFGH",
  "displayName": "Get Issue",
  "type": "execute-connector-activity",
  "data": {
    "serviceType": "Intsvc.ExecuteConnectorActivity",
    "context": [
      { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
      { "name": "connection", "value": "=bindings.bYrtrMEvs", "type": "string" },
      { "name": "resourceKey", "value": "0d93ddc9-a512-4b60-8483-4a3a8fbee20e", "type": "string" },
      { "name": "folderKey", "value": "=bindings.bePaAIvP8", "type": "string" },
      { "name": "operation", "value": "list", "type": "string" },
      { "name": "objectName", "value": "curated_get_issue", "type": "string" },
      { "name": "method", "value": "GET", "type": "string" },
      { "name": "path", "value": "/api/...", "type": "string" },
      { "name": "_label", "value": "Get Issue", "type": "string" },
      {
        "name": "metadata",
        "type": "json",
        "body": {
          "activityMetadata": { "activity": { "...TypeCache entry..." } },
          "designTimeMetadata": {
            "connectorLogoUrl": "icons/...",
            "activityConfig": { "isCurated": true, "operation": "list" }
          },
          "telemetryData": { "connectorKey": "...", "connectorName": "..." },
          "inputMetadata": {},
          "errorState": { "hasError": false },
          "activityPropertyConfiguration": {
            "configuration": "=jsonString:{...}",
            "uiPathActivityTypeId": "<uuid>",
            "errorState": { "issues": [] }
          }
        }
      }
    ],
    "inputs": [
      {
        "name": "body",
        "type": "json",
        "target": "body",
        "body": { "field1": "", "field2": "" },
        "var": "vRaNdOmId",
        "id": "vRaNdOmId",
        "elementId": "stage_1-tABCDEFGH"
      },
      {
        "name": "pathParameters",
        "type": "json",
        "target": "pathParameters",
        "body": { "issueIdOrKey": "" },
        "var": "vRaNdOm02",
        "id": "vRaNdOm02",
        "elementId": "stage_1-tABCDEFGH"
      },
      {
        "name": "queryParameters",
        "type": "json",
        "target": "queryParameters",
        "body": { "expand": "" },
        "var": "vRaNdOm03",
        "id": "vRaNdOm03",
        "elementId": "stage_1-tABCDEFGH"
      }
    ],
    "outputs": [
      {
        "name": "response",
        "displayName": "Get Issue",
        "type": "jsonSchema",
        "source": "=response",
        "var": "response",
        "id": "response",
        "value": "response",
        "target": "=response",
        "elementId": "stage_1-tABCDEFGH",
        "body": { "$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": { "..." } }
      },
      {
        "name": "Error",
        "displayName": "Error",
        "value": "error",
        "type": "jsonSchema",
        "source": "=Error",
        "var": "error",
        "id": "error",
        "target": "=error",
        "elementId": "stage_1-tABCDEFGH",
        "body": { "type": "object", "properties": { "code": { "type": "string" }, "..." } }
      }
    ],
    "bindings": []
  }
}
```

### Key differences from process-like tasks

- Has `serviceType` field (resolved from Elements API, or defaults to `"Intsvc.ExecuteConnectorActivity"`)
- Has `context[]` array with connector config, binding references, and metadata
- Has `bindings: []` (task-level, always empty — bindings go to root)
- Inputs are structured as `body`, `pathParameters`, `queryParameters` (JSON objects with field names as keys)
- Outputs include per-field entries + `response` (jsonSchema with swagger body) + `Error`

### Connector Binding Construction

Connector bindings are created at task build time because the enrichment context (connector key name, connection UUID, folder key) is only available during this step. Dedup against existing `root.data.uipath.bindings[]`.

1. Check dedup: does a ConnectionId binding with the same (`default`, `resource: "Connection"`, `resourceKey`) already exist?
2. If found, reuse the existing binding ID
3. If not, create a ConnectionId binding:
   ```json
   { "id": "b<random>", "name": "<connectorKey> connection", "type": "string",
     "resource": "Connection", "propertyAttribute": "ConnectionId",
     "resourceKey": "<connectionId>", "default": "<connectionId>" }
   ```
4. Same dedup check for FolderKey binding (if the connection has a folder key):
   ```json
   { "id": "b<random>", "name": "FolderKey", "type": "string",
     "resource": "Connection", "propertyAttribute": "folderKey",
     "resourceKey": "<connectionId>", "default": "<folderKey>" }
   ```
5. Push new bindings to `root.data.uipath.bindings[]`
6. Set context entries to reference bindings:
   - `connection` → `=bindings.<connectionBindingId>`
   - `folderKey` → `=bindings.<folderKeyBindingId>`

**Dedup example:** Two connector tasks using the same Jira connection share the same ConnectionId and FolderKey bindings.

---

## Connector Trigger Task (wait-for-connector)

### Build procedure

1. Generate task ID and element ID
2. Run `uip case tasks add-connector <FILE> <STAGE_ID> --type trigger --type-id <UUID> --connection-id <CONN_UUID> --output json`
3. Or build manually using enrichment data

### Task JSON structure

```json
{
  "id": "tABCDEFGH",
  "elementId": "stage_1-tABCDEFGH",
  "displayName": "Issue Created",
  "type": "wait-for-connector",
  "data": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
      { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
      { "name": "connection", "value": "=bindings.b4Hu9FHiu", "type": "string" },
      { "name": "resourceKey", "value": "0d93ddc9-a512-4b60-8483-4a3a8fbee20e", "type": "string" },
      { "name": "folderKey", "value": "=bindings.bNJUKpA2t", "type": "string" },
      { "name": "operation", "value": "ISSUE_CREATED", "type": "string" },
      { "name": "objectName", "value": "curated_get_issue", "type": "string" },
      { "name": "method", "type": "string" },
      { "name": "path", "type": "string" },
      {
        "name": "metadata",
        "type": "json",
        "body": {
          "activityMetadata": { "activity": { "...TypeCache entry..." } },
          "designTimeMetadata": {
            "connectorLogoUrl": "icons/...",
            "activityConfig": { "isCurated": true, "operation": "ISSUE_CREATED" }
          },
          "telemetryData": { "connectorKey": "...", "connectorName": "...", "operationType": "" },
          "inputMetadata": {},
          "errorState": { "hasError": false },
          "activityPropertyConfiguration": {
            "objectName": "curated_get_issue",
            "eventType": "ISSUE_CREATED",
            "eventMode": "polling",
            "configuration": "=jsonString:{...}",
            "uiPathActivityTypeId": "<uuid>",
            "errorState": { "issues": [] }
          }
        }
      }
    ],
    "inputs": [
      {
        "name": "body",
        "type": "json",
        "target": "body",
        "body": {
          "filters": { "expression": "" },
          "parameters": { "project": "", "issuetype": "" }
        },
        "var": "vRaNdOmId",
        "id": "vRaNdOmId",
        "elementId": ""
      }
    ],
    "outputs": [
      {
        "name": "response",
        "displayName": "Issue Created",
        "type": "jsonSchema",
        "source": "=response",
        "var": "response",
        "id": "response",
        "value": "response",
        "target": "=response",
        "elementId": "",
        "body": { "$schema": "http://json-schema.org/draft-07/schema#", "..." }
      },
      {
        "name": "Error",
        "displayName": "Error",
        "value": "error",
        "type": "jsonSchema",
        "source": "=Error",
        "var": "error",
        "id": "error",
        "target": "=error",
        "elementId": "",
        "body": { "type": "object", "properties": { "code": { "type": "string" }, "..." } }
      }
    ],
    "bindings": []
  }
}
```

### Key differences from connector activity

- `serviceType` is always `"Intsvc.WaitForEvent"`
- Context has no `_label` entry
- Context `method` and `path` are empty (triggers don't have HTTP endpoints)
- Context `operation` comes from `config.eventOperation` (not resolved via Elements API)
- `activityPropertyConfiguration` has additional top-level `objectName`, `eventType`, `eventMode` fields
- Inputs have a single `body` with `filters.expression` and `parameters` (event filter params)
- Outputs are always: `response` (with optional JSON Schema from swagger) + `Error`
- Connector bindings: same inline construction as connector activity (see above)

---

## Wait for Timer Task

Simplest task type — no enrichment, no bindings.

```json
{
  "id": "tABCDEFGH",
  "displayName": "Wait 5 minutes",
  "type": "wait-for-timer",
  "data": {
    "timer": "timeDuration",
    "timeDuration": "PT5M"
  }
}
```

Timer options:
- `timeDuration`: ISO 8601 duration (e.g., `PT5M`, `PT1H`)
- `timeDate`: ISO 8601 datetime
- `timeCycle`: ISO 8601 repeating interval (e.g., `R/PT1S`)

---

## Error Output Schema

All non-case-management tasks include a standard Error output. The body schema is:

```json
{
  "type": "object",
  "properties": {
    "code": { "type": "string" },
    "message": { "type": "string" },
    "detail": { "type": "string" },
    "category": { "type": "string" },
    "status": { "type": "number" },
    "element": { "type": "string" }
  }
}
```

Case-management sub-tasks do NOT get outputs (outputs are stripped during enrichment).

---

## Setting Input Values

Setting input values for all task types is documented in `hook-input-guide.md`.

---

## Variable ID Assignment Pipeline

After fetching raw inputs/outputs from enrichment, variable IDs are assigned:

### Inputs
Each input gets:
- `id` = `var` = `v` + 8 random alphanumeric chars
- `elementId` = `{stageId}-{taskId}`

### Outputs
Each output gets:
- `id` = `var` = `value` = unique camelCase derived from output `name` (e.g., `"Error"` → `"error"`, `"Action"` → `"action"`)
- `target` = `={id}`
- `elementId` = `{stageId}-{taskId}`
- `body` = resolved from `_jsonSchema` if type is `jsonSchema`

After ID assignment, `_jsonSchema` is removed from the output (moved into `body`).
