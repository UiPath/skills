# Case Management JSON Schema Reference

A case definition JSON file is the **source of truth** for a Case Management workflow. It is edited locally using `uip case` commands and then deployed to Orchestrator.

## Top-level structure

```json
{
  "root": { ... },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

---

## 1. root

Metadata and configuration for the case definition.

```json
{
  "id": "<shortId>",
  "name": "Loan Approval",
  "type": "case-management:root",
  "caseIdentifier": "LOAN",
  "caseAppEnabled": false,
  "caseIdentifierType": "constant",
  "version": "v12",
  "data": {
    "sla": { "count": 5, "unit": "d" },
    "slaRules": [],
    "uipath": {
      "bindings": [],
      "variables": { "inputs": [], "outputs": [], "inputOutputs": [] }
    }
  },
  "caseExitConditions": [],
  "description": "case description"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (auto-generated) |
| `name` | string | Human-readable name |
| `type` | `"case-management:root"` | Literal — do not change |
| `caseIdentifier` | string | Identifier used at runtime |
| `caseIdentifierType` | `"constant"` \| `"external"` | How the identifier is resolved |
| `caseAppEnabled` | boolean | Whether the Case App UI is enabled |
| `version` | string | Schema version — `"v12"` for current schema |
| `data.sla` | SlaSchema? | Default SLA for the case |
| `data.slaRules` | SlaRuleEntry[]? | Expression-driven SLA rules |
| `data.uipath` | object? | Variable and binding declarations |
| `caseExitConditions` | CaseExitCondition[]? | Conditions that mark the case as complete |
| `description` | string? | Case description |

### CaseExitCondition

```json
{
  "id": "<id>",
  "displayName": "Case resolved",
  "rules": [],
  "marksCaseComplete": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules? | DNF rule set (see §5) |
| `marksCaseComplete` | boolean? | Whether this condition closes the case |

---

## 2. nodes

Discriminated union on `type`. Three node types exist.

### a) Trigger Node — `"case-management:Trigger"`

Entry point. Created automatically by `uip case cases add`. There should be exactly one.

```json
{
  "id": "<shortId>",
  "type": "case-management:Trigger",
  "position": { "x": 200, "y": 0 },
  "data": {
    "label": "Start",
    "uipath": {
      "serviceType": "None"
    }
  }
}
```

`serviceType` options: `"None"`, `"Intsvc.EventTrigger"`, `"Intsvc.TimerTrigger"`.

### b) Stage Node — `"case-management:Stage"`

Standard workflow stage. Contains tasks organized in parallel lanes.

```json
{
  "id": "<shortId>",
  "type": "case-management:Stage",
  "position": { "x": 600, "y": 200 },
  "data": {
    "label": "Review Application",
    "tasks": [
      [
        { "id": "<taskId>", "type": "process", "displayName": "Run KYC", "data": { "name": "KYC", "folderPath": "Shared" } }
      ]
    ],
    "sla": { "count": 2, "unit": "d" },
    "entryConditions": [],
    "exitConditions": [],
    "description": "some desc"
  }
}
```

`tasks` is a 2D array: `tasks[lane][index]`. Outer = parallel lanes, inner = sequential tasks per lane.

**StageNodeData fields:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string? | Display label |
| `tasks` | Task[][]? | 2D array of tasks (lanes × sequential) |
| `sla` | SlaSchema? | SLA for this stage |
| `entryConditions` | EntryCondition[]? | Conditions for entering the stage |
| `exitConditions` | ExitCondition[]? | Conditions for exiting the stage |
| `instanceIdPrefix` | string? | Prefix for instance IDs |
| `description` | string? | Stage description |

### c) Exception Stage Node — `"case-management:ExceptionStage"`

Like a Stage but also supports expression-driven SLA rules.

```json
{
  "id": "<shortId>",
  "type": "case-management:ExceptionStage",
  "position": { "x": 1100, "y": 200 },
  "data": {
    "label": "Handle Rejection",
    "tasks": [],
    "entryConditions": [
      { "id": "<id>", "displayName": "Fraud detected", "rules": [], "isInterrupting": true }
    ],
    "exitConditions": [
      {
        "id": "<id>",
        "displayName": "Return to review",
        "type": "return-to-origin",
        "rules": []
      }
    ],
    "slaRules": []
  }
}
```

ExceptionStage `data` extends StageNodeData with:

| Field | Type | Description |
|-------|------|-------------|
| `slaRules` | SlaRuleEntry[]? | Expression-driven SLA rules for this exception stage |

### EntryCondition

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules? | DNF rule set (see §5) |
| `isInterrupting` | boolean? | Whether this condition interrupts the current stage |

### ExitCondition

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules? | DNF rule set (see §5) |
| `type` | string? | `"exit-only"` \| `"wait-for-user"` \| `"return-to-origin"` |
| `exitToStageId` | string? | Target stage ID when routing to a specific stage |
| `marksStageComplete` | boolean? | Whether this exit marks the stage complete |

---

## 3. edges

Discriminated union on `type`. Two edge types exist.

### a) TriggerEdge — `"case-management:TriggerEdge"`

Connects Trigger → Stage. No rules.

```json
{
  "id": "<shortId>",
  "type": "case-management:TriggerEdge",
  "source": "<trigger-node-id>",
  "target": "<stage-node-id>",
  "sourceHandle": "<trigger-id>____source____right",
  "targetHandle": "<stage-id>____target____left",
  "data": { "label": "Start" }
}
```

### b) Edge — `"case-management:Edge"`

Connects Stage → Stage. Transition conditions are defined via ExitConditions on the source stage node, not on the edge itself.

```json
{
  "id": "<shortId>",
  "type": "case-management:Edge",
  "source": "<stage-id>",
  "target": "<next-stage-id>",
  "sourceHandle": "<stage-id>____source____right",
  "targetHandle": "<next-stage-id>____target____left",
  "data": { "label": "Approved" }
}
```

**EdgeData fields:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string? | Display label on the edge |
| `waypoints` | unknown? | Visual routing waypoints |

Handle format: `<nodeId>____source____<direction>` or `<nodeId>____target____<direction>`.
Directions: `right`, `left`, `top`, `bottom`.

---

## 4. Tasks

All tasks share a `BaseTask`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique task ID (auto-generated) |
| `elementId` | string? | Element ID |
| `displayName` | string? | Human-readable label shown in the UI |
| `type` | string | Task type (see below) |
| `data` | object | Type-specific configuration |
| `skipCondition` | string? | Expression — skip the task when truthy |
| `entryConditions` | TaskEntryCondition[]? | Conditions controlling task entry |
| `conditions` | TaskCondition[]? | **Deprecated** — use `entryConditions` instead |
| `shouldRunOnReEntry` | boolean? | Re-run when stage is re-entered |
| `description` | string? | Task description |

### Task types

| Type | `data` fields |
|------|---------------|
| `process` | `name?`, `folderPath?`, `inputs?`, `outputs?`, `context?` |
| `action` | `name?`, `folderPath?`, `taskTitle?`, `labels?`, `priority?`, `actionCatalogName?`, `recipient?` |
| `agent` | `name?`, `folderPath?`, `inputs?`, `outputs?`, `context?` |
| `api-workflow` | `name?`, `folderPath?`, `inputs?`, `outputs?`, `context?` |
| `rpa` | `name?`, `folderPath?`, `inputs?`, `outputs?`, `context?` |
| `external-agent` | `name?`, `folderPath?`, `serviceType?`, `bindings?` |
| `wait-for-timer` | `timer?`, `timeDuration?`, `timeDate?`, `timeCycle?` |
| `wait-for-connector` | `name?`, `folderPath?`, `serviceType?`, `bindings?` |
| `execute-connector-activity` | `name?`, `folderPath?`, `serviceType?`, `bindings?` |
| `case-management` | `name?`, `folderPath?`, `inputs?`, `outputs?`, `context?` |

### TaskEntryCondition

```json
{
  "id": "<id>",
  "displayName": "Run only if not verified",
  "rules": [[{ "rule": "current-stage-entered" }]]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules? | DNF rule set (see §5) |

### TaskCondition (deprecated)

```json
{
  "id": "<id>",
  "displayName": "Skip if already verified",
  "actionType": "skip",
  "rules": [[{ "rule": "current-stage-entered" }]]
}
```

---

## 5. Rules (DNF: OR of AND-clauses)

Rules are used in entry/exit conditions and task conditions.

```
Rules = Rule[][]
  Outer array = OR groups
  Inner array = AND conditions within a group
```

### Rule types

| `rule` | Additional fields | Description |
|--------|-------------------|-------------|
| `wait-for-connector` | `id?`, `conditionExpression?`, `uipath?` | Wait for an external connector event |
| `case-entered` | `id?`, `conditionExpression?` | Fires when the case is first entered |
| `selected-stage-completed` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has completed |
| `selected-stage-exited` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has been exited |
| `selected-tasks-completed` | `id?`, `selectedTasksIds?`, `conditionExpression?` | Specific tasks have all completed |
| `current-stage-entered` | `id?`, `conditionExpression?` | The current stage was just entered |
| `adhoc` | `id?`, `conditionExpression?` | Ad-hoc expression-based condition |

```json
{ "rule": "case-entered", "id": "<id>" }

{ "rule": "selected-stage-completed", "id": "<id>", "selectedStageId": "<stageId>" }

{ "rule": "selected-tasks-completed", "id": "<id>", "selectedTasksIds": ["<taskId1>", "<taskId2>"] }

{ "rule": "adhoc", "id": "<id>", "conditionExpression": "in.Score > 700" }

{
  "rule": "wait-for-connector",
  "id": "<id>",
  "uipath": {
    "serviceType": "Intsvc.EventTrigger",
    "outputs": [],
    "bindings": []
  }
}
```

---

## 6. SLA and Escalation

```json
"sla": {
  "count": 2,
  "unit": "d",
  "escalationRule": [
    {
      "id": "<id>",
      "displayName": "Notify manager",
      "action": {
        "type": "notification",
        "recipients": [{ "scope": "User", "target": "manager@corp.com", "value": "manager@corp.com" }]
      },
      "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 }
    }
  ]
}
```

Time units: `"h"` (hours), `"d"` (days), `"w"` (weeks), `"m"` (months).

Escalation `triggerInfo.type`: `"at-risk"` or `"sla-breached"`.

Escalation `action.recipients[].scope`: `"User"` or `"UserGroup"`.

### SlaRuleEntry

Expression-driven SLAs allow per-case-instance SLA overrides:

```json
{
  "expression": "in.Priority == 'High'",
  "count": 1,
  "unit": "d"
}
```

---

## Minimal example

```json
{
  "root": {
    "id": "abc12345678",
    "name": "Simple Case",
    "type": "case-management:root",
    "caseIdentifier": "Simple Case",
    "caseAppEnabled": false,
    "caseIdentifierType": "constant",
    "version": "v12",
    "data": {}
  },
  "nodes": [
    {
      "id": "trig0000000",
      "type": "case-management:Trigger",
      "position": { "x": 200, "y": 0 },
      "data": {}
    },
    {
      "id": "stg00000001",
      "type": "case-management:Stage",
      "position": { "x": 600, "y": 200 },
      "data": { "label": "Process", "tasks": [] }
    }
  ],
  "edges": [
    {
      "id": "edg00000001",
      "type": "case-management:TriggerEdge",
      "source": "trig0000000",
      "target": "stg00000001",
      "sourceHandle": "trig0000000____source____right",
      "targetHandle": "stg00000001____target____left",
      "data": {}
    }
  ]
}
```