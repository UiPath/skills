# Case Management JSON Schema — Cross-Cutting Reference

Structural reference for the case definition JSON. Shared across all node types. Per-task-type and per-condition-type field shapes live in each plugin's `impl-cli.md` / `impl-json.md`.

## Top-level structure

```json
{
  "root": { ... },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

---

**ID format (cross-cutting).** All generated IDs follow the CLI's `prefixedId(prefix, count)` scheme: a fixed prefix followed by `count` random characters from `[A-Za-z0-9]`. Direct-JSON-write must use the same format — the frontend's `generateNextId(prefix, count)` depends on it.

| Entity | Prefix | Suffix length | Example |
|---|---|---|---|
| Stage (regular + exception) | `Stage_` | 6 | `Stage_aB3kL9` |
| Trigger (added after initial) | `trigger_` | 6 | `trigger_xY2mNp` |
| Edge | `edge_` | 6 | `edge_Qz7hVr` |
| Task | `t` | 8 | `t8GQTYo8O` |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` |
| Stage/case/task condition | `Condition_` | 6 | `Condition_xC1XyX` |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` |
| Binding | `b` | 8 | `b3KmNp7Q9` |

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
    "slaRules": [
      { "expression": "=js:true", "count": 5, "unit": "d" }
    ],
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
| `version` | string | Schema version — `"v17"` for current schema. Emitted by `uip maestro case cases add`. |
| `publishVersion` | number? | Publish version — `2` for current schema |
| `data.slaRules` | SlaRuleEntry[]? | Conditional + default SLA rules for the case. Default SLA lives here as the trailing entry with `expression: "=js:true"`. Escalations attach inside each rule's `escalationRule[]`. See §6. |
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

Entry point. Created automatically by `uip maestro case cases add`. Exactly one per case (single-trigger cases); additional triggers added via `uip maestro case stages add --type trigger` use the `trigger_` ID prefix.

```json
{
  "id": "trigger_xY2mNp",
  "type": "case-management:Trigger",
  "position": { "x": 200, "y": 0 },
  "data": {
    "label": "Start",
    "uipath": { "serviceType": "None" }
  }
}
```

`position` is fixed at `{ x: 200, y: 0 }` — not stateful like Stage.

No `style`, `measured`, `width`, `zIndex`, or `parentElement` on Trigger nodes (unlike Stage).

`serviceType` values: `"None"`, `"Intsvc.EventTrigger"`, `"Intsvc.TimerTrigger"`. The specific binding/config shape for each trigger kind lives in the corresponding trigger plugin's `impl-cli.md` / `impl-json.md`.

### b) Stage Node — `"case-management:Stage"`

Standard workflow stage. Contains tasks.

```json
{
  "id": "Stage_aB3kL9",
  "type": "case-management:Stage",
  "position": { "x": 100, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "Review Application",
    "description": "...",
    "isRequired": false,
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": [ [ { "...": "task" } ] ],
    "slaRules": [
      { "expression": "=js:true", "count": 2, "unit": "d" }
    ]
  }
}
```

**Top-level node fields:**

| Field | Type | Description |
|-------|------|-------------|
| `position` | `{x,y}` | Auto-computed by CLI as `{ x: 100 + existingStageCount * 500, y: 200 }`. Direct-JSON-write must count existing stages before writing. |
| `style` | object | Hard-coded `{ width: 304, opacity: 0.8 }`. |
| `measured` | object | Hard-coded `{ width: 304, height: 128 }`. |
| `width` | number | Hard-coded `304` (separate from `style.width` and `measured.width`). |
| `zIndex` | number | Hard-coded `1001`. |

**`StageNodeData` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string? | Display label |
| `description` | string? | Stage description |
| `isRequired` | boolean? | Whether the stage must complete before case exit (used by case-exit rule `required-stages-completed`) |
| `parentElement` | `{id,type}` | Always `{ id: "root", type: schema.root.type }` |
| `isInvalidDropTarget` | boolean | Always `false` (UI drag-drop flag) |
| `isPendingParent` | boolean | Always `false` (UI drag-drop flag) |
| `tasks` | Task[][] | 2D array: `tasks[lane][index]`. The skill places one task per lane (`tasks[0][0]`, `tasks[1][0]`, …) so the FE lays them out in separate columns. Lane has no execution meaning — sequencing and parallelism live in task-entry conditions. Empty array `[]` when no tasks yet. |
| `slaRules` | SlaRuleEntry[]? | Conditional + default SLA rules for this stage. Default SLA is the trailing `"=js:true"` entry. Escalations nest inside each rule. See §6. |
| `entryConditions` | EntryCondition[]? | See §3. Not initialized on regular Stage creation — added later by the conditions plugins. |
| `exitConditions` | ExitCondition[]? | See §3. Not initialized on regular Stage creation — added later by the conditions plugins. |
| `instanceIdPrefix` | string? | Prefix for instance IDs |

> **Regular `Stage` is created without `entryConditions`/`exitConditions`.** The CLI's `stages add` initializes these fields only for `ExceptionStage`. Regular stages acquire them later when `stage-entry-conditions add` / `stage-exit-conditions add` runs against them — the fields are created at that point, not at stage-creation time. See §3 for the condition shapes and §2b for how edge transitions reference the source stage's `exitConditions`.

### c) Exception Stage Node — `"case-management:ExceptionStage"`

Same top-level and render fields as regular Stage. Adds `entryConditions`, `exitConditions` initialized at creation time.

**Additional `ExceptionStageNodeData` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `entryConditions` | EntryCondition[] | Initialized to `[]` on create; see §3 |
| `exitConditions` | ExitCondition[] | Initialized to `[]` on create; see §3 |

> **SLA on ExceptionStage** — the runtime accepts `slaRules[]` on `ExceptionStage` the same way it does on regular `Stage`, but the CLI's `sla set --stage-id` blocks it. Use the JSON strategy to author it. See [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

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

All conditions share the same shape but attach at different levels. Per-level field tables and `--rule-type` semantics live in the corresponding condition plugin's `impl-cli.md` / `impl-json.md`.

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
  "id": "edge_Qz7hVr",
  "type": "case-management:TriggerEdge",
  "source": "trigger_xY2mNp",
  "target": "Stage_aB3kL9",
  "sourceHandle": "trigger_xY2mNp____source____right",
  "targetHandle": "Stage_aB3kL9____target____left",
  "data": { "label": "Start" }
}
```

### b) Edge — `"case-management:Edge"`

Connects Stage → Stage. Transition conditions live on the source stage's `exitConditions`, not on the edge.

```json
{
  "id": "edge_pK2mLq",
  "type": "case-management:Edge",
  "source": "Stage_aB3kL9",
  "target": "Stage_cD4mNt",
  "sourceHandle": "Stage_aB3kL9____source____right",
  "targetHandle": "Stage_cD4mNt____target____left",
  "data": { "label": "Approved" }
}
```

**Handle format:** `<nodeId>____source____<direction>` or `<nodeId>____target____<direction>` — exactly **four underscores** on each side of `source` / `target`. Directions: `right`, `left`, `top`, `bottom`. Defaults used by the CLI: source=`right`, target=`left`.

**Edge type is inferred from the source node:** Trigger source → `TriggerEdge`; Stage source → `Edge`.

**`zIndex`** (number, optional) — omitted unless explicitly set.

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

Not every rule type is valid at every level — see each condition plugin's `impl-cli.md` / `impl-json.md` for the allowed subset per location.

```json
{ "rule": "case-entered", "id": "<id>" }
{ "rule": "selected-stage-completed", "id": "<id>", "selectedStageId": "<stageId>" }
{ "rule": "selected-tasks-completed", "id": "<id>", "selectedTasksIds": ["<taskId1>", "<taskId2>"] }
{ "rule": "adhoc", "id": "<id>", "conditionExpression": "in.Score > 700" }
```

---

## 6. SLA and Escalation

All SLA data on a target (root or stage) lives in a single `slaRules[]` array. The default SLA is the trailing entry with `expression: "=js:true"`; conditional overrides sit before it in priority order. Escalations nest inside each rule's `escalationRule[]`.

```json
"slaRules": [
  {
    "expression": "=js:vars.priority === 'Urgent'",
    "count": 30,
    "unit": "m",
    "escalationRule": [
      {
        "id": "esc_aB3kL9",
        "triggerInfo": { "type": "sla-breached" },
        "action": {
          "type": "notification",
          "recipients": [
            { "scope": "User", "target": "<user-uuid>", "value": "manager@corp.com" }
          ]
        }
      }
    ]
  },
  {
    "expression": "=js:true",
    "count": 5,
    "unit": "d",
    "escalationRule": [
      {
        "id": "esc_xY2mNp",
        "displayName": "Notify manager",
        "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 },
        "action": {
          "type": "notification",
          "recipients": [
            { "scope": "User", "target": "<user-uuid>", "value": "manager@corp.com" }
          ]
        }
      }
    ]
  }
]
```

Time units: `"min"` (minutes), `"h"` (hours), `"d"` (days), `"w"` (weeks), `"m"` (months).
Escalation `triggerInfo.type`: `"at-risk"` or `"sla-breached"`. `atRiskPercentage` is required when `type === "at-risk"` and omitted otherwise.
Escalation `action.recipients[].scope`: `"User"` or `"UserGroup"`. `target` is the user / group UUID; `value` is the display string (email or group name).

### SlaRuleEntry

| Field | Type | Description |
|-------|------|-------------|
| `expression` | string | Rule predicate. `"=js:true"` marks the default / fallback rule. |
| `count` | number? | SLA duration count (optional — a bare escalation-only rule may omit this). |
| `unit` | `"min" \| "h" \| "d" \| "w" \| "m"` ? | SLA duration unit (optional — paired with `count`). |
| `escalationRule` | EscalationRule[]? | Notifications to fire at-risk or on breach. Runtime attaches escalations to whichever rule is active. |

Evaluated in array order; the first truthy expression wins. The trailing `"=js:true"` entry acts as the default.

> **CLI vs JSON divergences for SLA** — CLI's `sla escalation add` can only attach to the default `"=js:true"` rule. CLI's `sla set --stage-id` rejects `ExceptionStage`. CLI emits one `EscalationRule` per recipient (single-element `recipients[]`). The JSON strategy lifts all three limits — see [`plugins/sla/impl-json.md § Known CLI divergences`](plugins/sla/impl-json.md).

---

## 7. Tasks — BaseTask shape (shared)

All tasks inside a stage share this envelope. Per-type `data` fields live in each task plugin's `impl-cli.md` / `impl-json.md`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique task ID, `t` + 8 random chars (e.g. `t8GQTYo8O`) |
| `elementId` | string | Composite `${stageId}-${taskId}` (e.g. `Stage_aB3kL9-t8GQTYo8O`) |
| `displayName` | string? | Human-readable label shown in the UI |
| `type` | string | Task type — see task plugins under `plugins/tasks/` |
| `data` | object | Type-specific configuration — see corresponding plugin's `impl-cli.md` / `impl-json.md`. For connector tasks, `data.bindings` references the root-level bindings array. |
| `skipCondition` | string? | Expression — skip the task when truthy |
| `entryConditions` | TaskEntryCondition[]? | See §3. **Connector tasks (`execute-connector-activity`, `wait-for-connector`) receive a default `current-stage-entered` entry condition on creation. Non-connector tasks do NOT.** |
| `shouldRunOnlyOnce` | boolean? | Run the task at most once per case, even if the stage is re-entered |
| `shouldRunOnReEntry` | boolean? | *(deprecated — use `shouldRunOnlyOnce`)* Re-run when stage is re-entered |
| `isRequired` | boolean? | Whether the task must complete for the stage to complete |
| `description` | string? | Task description |

**Positioning:** tasks have no `x`/`y`. They live in `stageNode.data.tasks[laneIndex][]` — a 2D array where the outer index is the lane (rendering column) and the inner index is the order within the lane. The skill convention is one task per lane.

**Task type catalog** (full shape in each plugin's `impl-cli.md` / `impl-json.md`):

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
    "id": "Case_aBcDeF",
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
      "id": "trigger_xY2mNp",
      "type": "case-management:Trigger",
      "position": { "x": 200, "y": 0 },
      "data": { "label": "Start" }
    },
    {
      "id": "Stage_aB3kL9",
      "type": "case-management:Stage",
      "position": { "x": 100, "y": 200 },
      "style": { "width": 304, "opacity": 0.8 },
      "measured": { "width": 304, "height": 128 },
      "width": 304,
      "zIndex": 1001,
      "data": {
        "label": "Process",
        "parentElement": { "id": "root", "type": "case-management:root" },
        "isInvalidDropTarget": false,
        "isPendingParent": false,
        "tasks": []
      }
    }
  ],
  "edges": [
    {
      "id": "edge_Qz7hVr",
      "type": "case-management:TriggerEdge",
      "source": "trigger_xY2mNp",
      "target": "Stage_aB3kL9",
      "sourceHandle": "trigger_xY2mNp____source____right",
      "targetHandle": "Stage_aB3kL9____target____left",
      "data": {}
    }
  ]
}
```
