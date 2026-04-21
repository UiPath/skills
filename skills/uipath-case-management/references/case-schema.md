# Case Management JSON Schema — Cross-Cutting Reference

Structural reference for the case definition JSON. Shared across all node types. Per-task-type and per-condition-type field shapes live in each plugin's `impl.md`.

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
  "version": "v17",
  "publishVersion": 2,
  "data": {
    "sla": { "count": 5, "unit": "d" },
    "slaRules": [],
    "intsvcActivityConfig": "v2",
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
| `version` | string | Schema version — `"v17"` for current schema |
| `publishVersion` | number? | Publish version — `2` for current schema |
| `data.sla` | SlaSchema? | Default SLA for the case (see §5) |
| `data.slaRules` | SlaRuleEntry[]? | Expression-driven SLA rules (see §5) |
| `data.intsvcActivityConfig` | string? | Integration-service activity configuration payload |
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

Rule structure uses DNF — see §4.

---

## 2. nodes (four types, discriminated on `type`)

### a) Trigger Node — `"case-management:Trigger"`

Entry point. Created automatically by `uip maestro case cases add`. Exactly one per case.

```json
{
  "id": "<shortId>",
  "type": "case-management:Trigger",
  "position": { "x": 200, "y": 0 },
  "data": {
    "label": "Start",
    "uipath": { "serviceType": "None" }
  }
}
```

`serviceType` values: `"None"`, `"Intsvc.EventTrigger"`, `"Intsvc.TimerTrigger"`. The specific binding/config shape for each trigger kind lives in the corresponding trigger plugin's `impl.md`.

### b) Stage Node — `"case-management:Stage"`

Standard workflow stage. Contains tasks.

```json
{
  "id": "<shortId>",
  "type": "case-management:Stage",
  "position": { "x": 600, "y": 200 },
  "data": {
    "label": "Review Application",
    "tasks": [ [ { ... task ... } ] ],
    "sla": { "count": 2, "unit": "d" },
    "entryConditions": [],
    "exitConditions": [],
    "description": "..."
  }
}
```

**StageNodeData fields:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string? | Display label |
| `tasks` | Task[][]? | 2D array: `tasks[lane][index]`. The skill places one task per lane (`tasks[0][0]`, `tasks[1][0]`, …) so the FE lays them out in separate columns. Lane has no execution meaning — sequencing and parallelism live in task-entry conditions. |
| `sla` | SlaSchema? | SLA for this stage |
| `entryConditions` | EntryCondition[]? | See §3 |
| `exitConditions` | ExitCondition[]? | See §3 |
| `instanceIdPrefix` | string? | Prefix for instance IDs |
| `isRequired` | boolean? | Whether the stage must complete for the case to complete |
| `description` | string? | Stage description |

### c) Exception Stage Node — `"case-management:ExceptionStage"`

Like a Stage but also supports expression-driven SLA rules.

Extends StageNodeData with:

| Field | Type | Description |
|-------|------|-------------|
| `slaRules` | SlaRuleEntry[]? | Expression-driven SLA rules for this exception stage |

### d) Sticky Note Node — `"case-management:StickyNote"`

Free-floating annotation node. Ignored at execution time; surfaced only in the authoring canvas.

```json
{
  "id": "<shortId>",
  "type": "case-management:StickyNote",
  "position": { "x": 400, "y": 400 },
  "data": {
    "label": "Note",
    "color": "yellow",
    "content": "Reminder: confirm SLA with ops before publishing."
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.label` | string? | Display label |
| `data.color` | string? | Sticky note color |
| `data.content` | string? | Note body |

---

## 3. Conditions (cross-cutting)

All conditions share the same shape but attach at different levels. Per-level field tables and `--rule-type` semantics live in the corresponding condition plugin's `impl.md`.

### EntryCondition (stage-level)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules | DNF rule set — see §4 |
| `isInterrupting` | boolean? | Whether the condition interrupts the current stage |

### ExitCondition (stage-level)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules | DNF rule set — see §4 |
| `type` | string? | `"exit-only"` \| `"wait-for-user"` \| `"return-to-origin"` |
| `exitToStageId` | string? | Target stage ID when routing to a specific stage |
| `marksStageComplete` | boolean? | Whether this exit marks the stage complete |

### TaskEntryCondition (task-level)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique ID |
| `displayName` | string? | Human-readable label |
| `rules` | Rules | DNF rule set — see §4 |

### CaseExitCondition (case-level)

See `root.caseExitConditions` in §1.

---

## 4. edges (two types, discriminated on `type`)

### a) TriggerEdge — `"case-management:TriggerEdge"`

Connects Trigger → Stage. No rules.

```json
{
  "id": "<shortId>",
  "type": "case-management:TriggerEdge",
  "source": "<trigger-id>",
  "target": "<stage-id>",
  "sourceHandle": "<trigger-id>____source____right",
  "targetHandle": "<stage-id>____target____left",
  "data": { "label": "Start" }
}
```

### b) Edge — `"case-management:Edge"`

Connects Stage → Stage. Transition conditions live on the source stage's `exitConditions`, not on the edge.

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

Handle format: `<nodeId>____source____<direction>` or `<nodeId>____target____<direction>`. Directions: `right`, `left`, `top`, `bottom`.

---

## 5. Rules (DNF — OR of AND-clauses)

Used by every condition type (entry, exit, task-entry, case-exit).

```
Rules = Rule[][]
  Outer array = OR groups
  Inner array = AND conditions within a group
```

### Rule types (cross-cutting catalog)

| `rule` | Additional fields | Description |
|--------|-------------------|-------------|
| `wait-for-connector` | `id?`, `conditionExpression?`, `uipath?` | Wait for an external connector event |
| `case-entered` | `id?`, `conditionExpression?` | Fires when the case is first entered |
| `selected-stage-completed` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has completed |
| `selected-stage-exited` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has been exited |
| `selected-tasks-completed` | `id?`, `selectedTasksIds?`, `conditionExpression?` | Specific tasks have all completed |
| `required-tasks-completed` | `id?`, `conditionExpression?` | All required tasks in the stage have completed |
| `required-stages-completed` | `id?`, `conditionExpression?` | All required stages have completed |
| `current-stage-entered` | `id?`, `conditionExpression?` | The current stage was just entered |
| `user-selected-stage` | `id?`, `conditionExpression?` | Fires when a user manually selects/routes to this stage |
| `adhoc` | `id?`, `conditionExpression?` | Ad-hoc expression-based condition |

Not every rule type is valid at every level — see each condition plugin's `impl.md` for the allowed subset per location.

```json
{ "rule": "case-entered", "id": "<id>" }
{ "rule": "selected-stage-completed", "id": "<id>", "selectedStageId": "<stageId>" }
{ "rule": "selected-tasks-completed", "id": "<id>", "selectedTasksIds": ["<taskId1>", "<taskId2>"] }
{ "rule": "adhoc", "id": "<id>", "conditionExpression": "in.Score > 700" }
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

### SlaRuleEntry (expression-driven overrides)

```json
{
  "expression": "in.Priority == 'High'",
  "count": 1,
  "unit": "d"
}
```

Evaluated in array order; the first truthy expression wins. The trailing entry with `expression: "=js:true"` (or equivalent) acts as the default.

---

## 7. Tasks — BaseTask shape (shared)

All tasks inside a stage share this envelope. Per-type `data` fields live in each task plugin's `impl.md`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string? | Unique task ID (auto-generated) |
| `elementId` | string? | Element ID |
| `displayName` | string? | Human-readable label shown in the UI |
| `type` | string | Task type — see task plugins under `plugins/tasks/` |
| `data` | object | Type-specific configuration — see corresponding plugin's `impl.md` |
| `skipCondition` | string? | Expression — skip the task when truthy |
| `entryConditions` | TaskEntryCondition[]? | See §3 |
| `shouldRunOnlyOnce` | boolean? | Run the task at most once per case, even if the stage is re-entered |
| `shouldRunOnReEntry` | boolean? | *(deprecated — use `shouldRunOnlyOnce`)* Re-run when stage is re-entered |
| `isRequired` | boolean? | Whether the task must complete for the stage to complete |
| `description` | string? | Task description |

**Task type catalog** (full shape in each plugin's `impl.md`):

| Task `type` | Plugin |
|-------------|--------|
| `process` | `plugins/tasks/process/` |
| `action` | `plugins/tasks/action/` |
| `agent` | `plugins/tasks/agent/` |
| `rpa` | `plugins/tasks/rpa/` |
| `api-workflow` | `plugins/tasks/api-workflow/` |
| `case-management` | `plugins/tasks/case-management/` |
| `execute-connector-activity` | `plugins/tasks/connector-activity/` |
| `wait-for-connector` | `plugins/tasks/connector-trigger/` |
| `wait-for-timer` | `plugins/tasks/wait-for-timer/` |
| `external-agent` | *(reserved — not covered in current milestone)* |

---

## 8. Minimal example

```json
{
  "root": {
    "id": "abc12345678",
    "name": "Simple Case",
    "type": "case-management:root",
    "caseIdentifier": "Simple Case",
    "caseAppEnabled": false,
    "caseIdentifierType": "constant",
    "version": "v17",
    "publishVersion": 2,
    "data": {
      "intsvcActivityConfig": "v2",
      "uipath": {
        "variables": {},
        "bindings": []
      }
    }
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
