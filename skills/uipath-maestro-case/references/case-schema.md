# Case Management JSON Schema — Cross-Cutting Reference

Structural reference for the case definition JSON. Shared across all node types. Per-task-type and per-condition-type field shapes live in each plugin's `impl-json.md`.

## Top-level shape

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "23.0.0",
  "name": "<case name>",
  "description": "<optional>",
  "metadata": {
    "caseIdentifier": "<MORT>",
    "caseIdentifierType": "constant",
    "caseAppEnabled": false,
    "publishVersion": 2,
    "caseUnifiedSchemaEnabled": true,
    "caseDirectlyPassTaskOutputs": true,
    "intsvcActivityConfig": "v2",
    "slaRules": [ ... ],
    "caseExitRules": [ ... ]
  },
  "bindings": [ ... ],
  "variables": { "inputs": [], "outputs": [], "inputOutputs": [] },
  "nodes": [ ... ],
  "edges": [],
  "layout": {}
}
```

### Layout-strip (Rule 18)

Node-level layout fields move to a top-level `layout` block. The frontend transformer `transformCaseInMemoryJsonToDiskJson.ts` does this stripping when round-tripping through canvas; skill emits clean nodes from the start.

**Stripped from each node** (skill MUST NOT emit):
- `position`
- `style`
- `measured`
- `width`
- `height`
- `zIndex`

**Stripped from each edge** (skill MUST NOT emit):
- `data.waypoints`

**Lifted to** `layout.nodes[<nodeId>] = { position, style, measured, width, height }` and `layout.edges[<edgeId>] = { waypoints }` — but skill emits empty `layout: {}` because FE auto-layouts on canvas load. Skill is not a layout authority.

---

**ID format (cross-cutting).** All generated IDs follow the CLI's `prefixedId(prefix, count)` scheme: a fixed prefix followed by `count` random characters from `[A-Za-z0-9]`. Direct-JSON-write must use the same format — the frontend's `generateNextId(prefix, count)` depends on it.

| Entity | Prefix | Suffix length | Example |
|---|---|---|---|
| Stage (regular + exception) | `Stage_` | 6 | `Stage_aB3kL9` |
| Trigger (added after initial) | `trigger_` | 6 | `trigger_xY2mNp` |
| Task | `t` | 8 | `t8GQTYo8O` |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` |
| Stage/case/task condition | `Condition_` | 6 | `Condition_xC1XyX` |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` |
| Binding | `b` | 8 | `b3KmNp7Q9` |

---

## 1. Top-level + metadata

Metadata and configuration for the case definition. Top-level fields (`id`, `version`, `name`, `description`) sit alongside the `metadata` block.

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "23.0.0",
  "name": "Loan Approval",
  "description": "case description",
  "metadata": {
    "caseIdentifier": "LOAN",
    "caseIdentifierType": "constant",
    "caseAppEnabled": false,
    "publishVersion": 2,
    "caseUnifiedSchemaEnabled": true,
    "caseDirectlyPassTaskOutputs": true,
    "intsvcActivityConfig": "v2",
    "slaRules": [
      { "expression": "=js:true", "count": 5, "unit": "d" }
    ],
    "caseExitRules": []
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID, `case-` + 10 random chars (auto-generated) |
| `version` | string | Schema version — `"23.0.0"`. Emitted by the `case` plugin at T01. |
| `name` | string | Human-readable name |
| `description` | string? | Case description |
| `metadata.caseIdentifier` | string | Runtime identifier. `constant` → literal prefix. `external` → `=`-prefixed expression. See § Case identifier below. |
| `metadata.caseIdentifierType` | `"constant"` \| `"external"` | Selects how `caseIdentifier` is read. Default `constant`. |
| `metadata.caseAppEnabled` | boolean | Whether the Case App UI is enabled |
| `metadata.publishVersion` | number? | Publish version — `2` for current schema |
| `metadata.caseUnifiedSchemaEnabled` | boolean? | Unified-schema flag (`true`) |
| `metadata.caseDirectlyPassTaskOutputs` | boolean? | Passes task outputs directly through messages instead of shared variables, fixing race conditions on task outputs in cases with parallel tasks. Schema-optional, defaults `true` when absent; skill emits the T01 `directly-pass-task-outputs` value (`true` unless sdd.md requested `false`). |
| `metadata.intsvcActivityConfig` | string? | Integration-service activity configuration payload |
| `metadata.slaRules` | SlaRuleEntry[]? | Conditional + default SLA rules for the case. Default SLA lives here as the trailing entry with `expression: "=js:true"`. Escalations attach inside each rule's `escalationRule[]`. See §6. |
| `metadata.caseExitRules` | CaseExitCondition[]? | Conditions that mark the case as complete |

### Case identifier (constant vs external)

`caseIdentifierType` picks how `caseIdentifier` resolves at runtime:

- **`constant`** (default) — `caseIdentifier` is a literal 2-4 char prefix (`"LOAN"`). Runtime emits the case external id as `<prefix>-<generated>`.
- **`external`** — `caseIdentifier` is a `=`-prefixed expression (bare `=vars.<id>` or `=js:<expr>`). Runtime evaluates it; the result becomes the case external id verbatim (no prefix). Same `=vars.<id>` / `=js:` convention as [bindings-and-expressions.md](bindings-and-expressions.md) — no other engine. Field lives under `metadata`. Authoring forms + variable eligibility: [`plugins/case/planning.md` § External identifier value](plugins/case/planning.md).

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

Entry point. Written by the triggers plugin at T02. Exactly one per case (single-trigger cases); additional triggers use the `trigger_` ID prefix.

```json
{
  "id": "trigger_xY2mNp",
  "type": "case-management:Trigger",
  "data": {
    "label": "Start",
    "uipath": { "serviceType": "None" }
  }
}
```

No `position`, `style`, `measured`, `width`, `zIndex`, or `parentElement` on Trigger nodes (Rule 18 layout-strip).

`serviceType` values: `"None"`, `"Intsvc.EventTrigger"`, `"Intsvc.TimerTrigger"`. The specific binding/config shape for each trigger kind lives in the corresponding trigger plugin's `impl-json.md`.

> **Placeholder form (`Intsvc.EventTrigger` only):** when an event trigger's IS connection is unresolved, `data.uipath` carries `serviceType` only — no `context[]`, `metadata`, `inputs[]`, `outputs[]`, or `bindings[]`. See [`triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md).

### b) Stage Node — `"case-management:Stage"`

Standard workflow stage. Contains tasks.

```json
{
  "id": "Stage_aB3kL9",
  "type": "case-management:Stage",
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

No `position`, `style`, `measured`, `width`, `height`, or `zIndex` at the node level (Rule 18 layout-strip).

**`StageNodeData` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string? | Display label |
| `description` | string? | Stage description |
| `isRequired` | boolean? | Whether the stage must complete before case exit (used by case-exit rule `required-stages-completed`) |
| `parentElement` | `{id,type}` | Always `{ id: "root", type: "case-management:root" }`. The literal `"root"` is canvas-side — there is no `"root"` node on disk. |
| `isInvalidDropTarget` | boolean | Always `false` (UI drag-drop flag) |
| `isPendingParent` | boolean | Always `false` (UI drag-drop flag) |
| `tasks` | Task[][] | 2D array: `tasks[lane][index]`. Default: one task per lane (`tasks[0][0]`, `tasks[1][0]`, …) so the FE lays them out in separate columns; lane is layout-only, sequencing comes from task-entry conditions. Exception: tasks in a `runs-sequentially` group that should execute in parallel share the same lane — there, shared lane carries execution semantics (parallel siblings inside the sequential group). Empty array `[]` when no tasks yet. |
| `slaRules` | SlaRuleEntry[]? | Conditional + default SLA rules for this stage. Default SLA is the trailing `"=js:true"` entry. Escalations nest inside each rule. See §6. |
| `entryConditions` | EntryCondition[]? | See §3. Not initialized on regular Stage creation — added later by the conditions plugins. |
| `exitConditions` | ExitCondition[]? | See §3. Not initialized on regular Stage creation — added later by the conditions plugins. |
| `instanceIdPrefix` | string? | Prefix for instance IDs |

> **Regular `Stage` is created without `entryConditions`/`exitConditions`.** Match this by not emitting empty arrays for those fields when writing a regular stage. They are added later by the condition plugins when entry/exit conditions are written. See §3 for the condition shapes. Transitions are driven entirely by these conditions — edges are retired and `edges` stays `[]` (§4).

### c) Exception Stage Node — `"case-management:ExceptionStage"`

Same top-level and render fields as regular Stage. Adds `entryConditions`, `exitConditions` initialized at creation time.

**Additional `ExceptionStageNodeData` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `entryConditions` | EntryCondition[] | Initialized to `[]` on create; see §3 |
| `exitConditions` | ExitCondition[] | Initialized to `[]` on create; see §3 |

> **SLA on ExceptionStage** — the runtime accepts `slaRules[]` on `ExceptionStage` the same way it does on regular `Stage`. Author per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

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

All conditions share the same shape but attach at different levels. Per-level field tables and `--rule-type` semantics live in the corresponding condition plugin's `impl-json.md`.

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

See `metadata.caseExitRules` in §1.

---

## 4. edges (two types, discriminated on `type`)

> **The skill does not author edges — `edges` stays `[]`.** Stage transitions derive entirely from `entryConditions` / `exitConditions` (§3); the case start derives from the first stage's `case-entered` entry condition, not a `TriggerEdge`. The structures below are **reference-only** — the empty `edges[]` array remains in the schema for frontend compatibility, and the FE auto-derives canvas connectors from the conditions. The two edge shapes are documented here only so a canvas-round-tripped file (where the FE may have materialized edges) is still readable.

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
| `wait-for-connector` | `id?`, `uipath` (connector config — **required**; absent → `connector activity missing`. Unresolved → **stub** placeholder, not bare — see § Placeholder fallback), `conditionExpression?` | Wait for an external connector event — see § Connector-bound rule below |
| `case-entered` | `id?`, `conditionExpression?` | Fires when the case is first entered |
| `selected-stage-completed` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has completed |
| `selected-stage-exited` | `id?`, `selectedStageId?`, `conditionExpression?` | A specific stage has been exited |
| `selected-tasks-completed` | `id?`, `selectedTasksIds?`, `conditionExpression?` | Specific tasks have all completed |
| `required-tasks-completed` | `id?`, `conditionExpression?` | All required tasks in the stage have completed |
| `required-stages-completed` | `id?`, `conditionExpression?` | All required stages have completed |
| `current-stage-entered` | `id?`, `conditionExpression?` | The current stage was just entered |
| `user-selected-stage` | `id?`, `conditionExpression?` | Fires when a user manually selects/routes to this stage |
| `adhoc` | `id?`, `conditionExpression?` | Ad-hoc expression-based condition |
| `runs-sequentially` | `id?`, `conditionExpression?` | Sequential tasks run in the order they appear in the stage from top to bottom | 

Not every rule type is valid at every level — see each condition plugin's `impl-json.md` for the allowed subset per location.

```json
{ "rule": "case-entered", "id": "<id>" }
{ "rule": "selected-stage-completed", "id": "<id>", "selectedStageId": "<stageId>" }
{ "rule": "selected-tasks-completed", "id": "<id>", "selectedTasksIds": ["<taskId1>", "<taskId2>"] }
{ "rule": "adhoc", "id": "<id>", "conditionExpression": "=js:vars.score > 700" }
```

### Connector-bound `wait-for-connector` rule

A `wait-for-connector` rule binds an IS connector trigger under **`uipath`** — the same block the in-stage `wait-for-connector` task carries under `data`. A bare rule (no `uipath`) is rejected by Studio Web (the FE validator requires the connector activity to resolve). It is authored from a `case spec --type trigger` scaffold; the CLI does not bind it (`buildRule` emits the bare form). `conditionExpression` is an optional `=js:` gate on **case state** (`vars.X` / `metadata`) — NOT the event payload (no `event` namespace). Inputs/outputs `elementId` = `<stageId>-<ruleId>` (stage-entry / stage-exit / task-entry — all stage-scoped) or `root-<ruleId>` (case-exit). Full recipe: [connector-trigger-common.md § Target: connector-bound condition rule](connector-trigger-common.md#target-connector-bound-condition-rule).

```json
{
  "rule": "wait-for-connector",
  "id": "<ruleId>",
  "uipath": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [ { "name": "connectorKey", "value": "<key>", "type": "string" }, { "name": "connection", "value": "=bindings.<id>", "type": "string" }, { "name": "resourceKey", "value": "<connection-id>", "type": "string" }, { "name": "folderKey", "value": "=bindings.<id>", "type": "string" }, { "name": "method", "value": "<httpMethod>", "type": "string" }, { "name": "path", "value": "<path>", "type": "string" }, { "name": "objectName", "value": "<object>", "type": "string" }, { "name": "operation", "value": "<eventOperation>", "type": "string" }, { "name": "metadata", "type": "json", "body": { } } ],
    "inputs": [ ],
    "outputs": [ ],
    "bindings": []
  },
  "conditionExpression": "=js:<optional case-state gate, e.g. vars.X — NOT the event payload>"
}
```

> Full `validate` requires `rule.uipath` + `context` (absent → `connector activity missing`); the check is satisfied by `context` entries named `connectorKey` + `operation`, and does not inspect internals (a wrong `serviceType` passes). Confirm the connector resolves via Studio Web. The exact `context` field set is CLI-emitted and varies by connector — splice it verbatim from `case spec`; the 9 fields above are illustrative of an HTTP-event connector, not a fixed schema.

---

## 6. SLA and Escalation

All SLA data on a target (root or stage) lives in a single `slaRules[]` array. The default SLA is the trailing entry with `expression: "=js:true"`; conditional overrides sit before it in priority order. Escalations nest inside each rule's `escalationRule[]`.

```json
"slaRules": [
  {
    "expression": "=js:vars.priority === 'Urgent'",
    "count": 30,
    "unit": "min",
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

> **SLA capabilities** — escalation rules can attach to any rule (not only the default `"=js:true"`). `slaRules[]` is supported on `ExceptionStage`. A single `EscalationRule` may carry multiple `recipients[]`. See [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

---

## 7. Tasks — BaseTask shape (shared)

All tasks inside a stage share this envelope. Per-type `data` fields live in each task plugin's `impl-json.md`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique task ID, `t` + 8 random chars (e.g. `t8GQTYo8O`) |
| `elementId` | string | Composite `${stageId}-${taskId}` (e.g. `Stage_aB3kL9-t8GQTYo8O`) |
| `displayName` | string? | Human-readable label shown in the UI |
| `type` | string | Task type — see task plugins under `plugins/tasks/` |
| `data` | object | Type-specific configuration — see corresponding plugin's `impl-json.md`. For connector tasks, `data.bindings` references the root-level bindings array. |
| `skipCondition` | string? | Expression — skip the task when truthy |
| `entryConditions` | TaskEntryCondition[]? | See §3. Written by the task-entry-conditions plugin from the SDD's authored Entry Condition rows — applied uniformly across task types (no auto-injection by task type). |
| `shouldRunOnlyOnce` | boolean? | Run the task at most once per case, even if the stage is re-entered |
| `shouldRunOnReEntry` | boolean? | *(deprecated — use `shouldRunOnlyOnce`)* Re-run when stage is re-entered |
| `isRequired` | boolean? | Whether the task must complete for the stage to complete |
| `description` | string? | Task description |

**Positioning:** tasks have no `x`/`y`. They live in `stageNode.data.tasks[laneIndex][]` — a 2D array where the outer index is the lane (rendering column) and the inner index is the order within the lane. Default convention: one task per lane. Exception: within a `runs-sequentially` group, tasks that should run in parallel share the same lane (shared lane = parallel siblings, carries execution semantics).

**Task type catalog** (full shape in each plugin's `impl-json.md`):

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

> **Not supported yet — do NOT author.** `external-agent`, `external-workflow`, `document-extraction`, `flow-process`. None of these are valid in `caseplan.json` (SKILL.md Rule 16).

---

## 8. Minimal example

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "23.0.0",
  "name": "Simple Case",
  "metadata": {
    "caseIdentifier": "Simple Case",
    "caseIdentifierType": "constant",
    "caseAppEnabled": false,
    "publishVersion": 2,
    "caseUnifiedSchemaEnabled": true,
    "caseDirectlyPassTaskOutputs": true,
    "intsvcActivityConfig": "v2"
  },
  "bindings": [],
  "variables": { "inputs": [], "outputs": [], "inputOutputs": [] },
  "nodes": [
    {
      "id": "trigger_xY2mNp",
      "type": "case-management:Trigger",
      "data": { "label": "Start" }
    },
    {
      "id": "Stage_aB3kL9",
      "type": "case-management:Stage",
      "data": {
        "label": "Process",
        "parentElement": { "id": "root", "type": "case-management:root" },
        "isInvalidDropTarget": false,
        "isPendingParent": false,
        "tasks": []
      }
    }
  ],
  "edges": []
}
```

`edges` is empty: the skill authors no edges. The case starts because `Stage_aB3kL9` carries a `case-entered` entry condition (added by the stage-entry-conditions plugin), not because a `TriggerEdge` connects the trigger to it.
