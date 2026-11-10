# task-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes the condition. A `wait-for-connector` rule gets the canonical stub; Phase 3 Step 10.5 upgrades only its `uipath` when resolved. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the Phase 2 task-entry condition directly to the target task's `entryConditions[]`; no CLI call is needed. Step 10.5 separately upgrades connector rules.

## Condition JSON Shape

> **ID format.** Task-level condition `id` is `c` + 8 random chars; rule `id` is `r` + 8 random chars. Stage/case-level conditions use `Condition_`/`Rule_`.

```json
{
  "id": "c4fGhJ2Mn",
  "displayName": "After Approval",
  "rules": [[
    {"id": "rK9xQw3Lp", "rule": "selected-tasks-completed", "selectedTasksIds": ["t8GQTYo8O"]}
  ]]
}
```

Rules use DNF: outer arrays are OR; inner arrays are AND.

## Procedure

1. Generate a condition ID: `c` + 8 alphanumeric chars, and a rule ID: `r` + 8 alphanumeric chars.
2. Locate the target stage in `schema.nodes` by ID, then search every `stageNode.data.tasks[lane][index]` lane for the target task ID.
3. Initialize `task.entryConditions = []` if absent.
4. Read the rule type from the SDD's Entry Condition table and apply its recipe below.
5. Set `displayName` to the SDD row's `Display Name`, if present; otherwise use `Entry rule {N}`. `N` is case-wide: scan the whole `caseplan.case` for existing `Entry rule <number>` names in every stage's `data.entryConditions[]` and task's `entryConditions[]`; use highest + 1, or `1` if none. A per-task counter names every unnamed first condition `Entry rule 1` and fails `validate` — [case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness). Never emit a blank or omitted `displayName`.
6. Append the condition object to `task.entryConditions[]`.

## Rule Types

### current-stage-entered

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "current-stage-entered" } ]]
```

### selected-tasks-completed — sibling task gating

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "selected-tasks-completed",
    "selectedTasksIds": ["t8GQTYo8O", "tWm4Vx9Tp"]
  }
]]
```

`selectedTasksIds` is a JSON string array. Resolve every planned selector through `tasks/id-map.json`, using the task's EXACT SDD display name—never a paraphrase or shortened name. Resolve only same-stage tasks whose entry conditions are not `adhoc`. If a selected task is ad-hoc/manual, stop and repair the plan: required downstream flow cannot depend on optional user-launched work. Never write an empty or partially resolved `selectedTasksIds`; an unresolvable name is a stop-and-ask (AskUserQuestion: name the intended task, or repair the plan), never an empty emit. `uip maestro case validate`'s `has no task(s) selected` finding must never discover this; Step 12 Check 13 catches it first.

### adhoc — expression gate

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "adhoc",
    "conditionExpression": "=js:vars.riskScore > 700"
  }
]]
```

Use bare `=js:<expr>` (no outer parentheses), per FE condition convention. Put operators (`>`, `<`, `===`, etc.) and calls inline; use strict `===`/`!==`, never `==`/`!=`. Normalize SDD shorthand such as `approved == true` to `=js:vars.approved === true`; do not transcribe `==`. Parenthesize each sub-clause in combined expressions: `=js:(vars.X === 'foo') && (vars.Y > 5)`. See [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; final inputs/outputs use the owning stage's `elementId = <stageId>-<ruleId>`, not the task ID. Preserve optional `conditionExpression`.

The source of truth is [connector-trigger-impl.md § Target: connector-bound condition rule](../../../connector-trigger-impl.md#target-connector-bound-condition-rule). `rule.uipath` always has `serviceType` and the four arrays; connector identity belongs in `context[]`, never as flat `uipath` fields (`typeId` / `connectorKey` / `operation`). A flat shape passes `validate` but is not runnable.

Phase 2 stub (exact):

```json
"rules": [[
  {
    "id": "rxxxxxxxx",
    "rule": "wait-for-connector",
    "uipath": {
      "serviceType": "Intsvc.WaitForEvent",
      "context": [
        { "name": "connectorKey", "value": "placeholder", "type": "string" },
        { "name": "operation",    "value": "placeholder", "type": "string" }
      ],
      "inputs": [],
      "outputs": [],
      "bindings": []
    }
  }
]]
```

In Phase 3 Step 10.5, replace only `uipath` with the `case spec --type trigger --input-details` caseShape ([common § Procedure (Phase 3)](../../../connector-trigger-impl.md#procedure-phase-3)):

```json
"uipath": {
  "serviceType": "Intsvc.WaitForEvent",
  "context": "<caseShape.context — placeholders substituted>",
  "inputs": [
    {
      "name":   "<caseShape.inputs[i].name>",
      "type":   "<caseShape.inputs[i].type>",
      "target": "<caseShape.inputs[i].target>",
      "body":   "<caseShape.inputs[i].body, carried over unchanged>",
      "var": "vxxxxxxxx",
      "id":  "vxxxxxxxx",
      "elementId": "<stageId>-<ruleId>"
    }
  ],
  "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied>",
  "bindings": []
}
```

Defer rule output binding with the stub. After the Phase 3 upgrade produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings. `elementId` remains `<stageId>-<ruleId>`.

### runs-sequentially — sequential task chain

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "runs-sequentially" } ]]
```

The sequential/ordered-task-set rule is the task's only entry condition for strict sequences and parallel siblings starting after an immediate predecessor. Preserve task order in the stage's `data.tasks`. A strict chain uses consecutive single-task inner arrays (`[[A], [B], [C]]`); `parallel-after-predecessor` siblings after one predecessor share a later inner array (`[[A], [B, C], [D]]`) and each sibling carries `runs-sequentially`. In the first `runs-sequentially` set it means the current stage was entered; in later sets it means the preceding `runs-sequentially` set completed. Sets with no `runs-sequentially` task are skipped, so the predecessor A must be `runs-sequentially` too. When the predecessor is `runs-sequentially`, do not use `selected-tasks-completed` or an additional `current-stage-entered` rule for immediate-predecessor sequencing. After a non-sequential predecessor, give each follower `selected-tasks-completed` naming it, in its own set.

### sla-status-change — the `start-task` SLA response

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "sla-status-change", "slaId": "sla_aB3kL9Qx" } ]]
```

The task fires when the referenced SLA changes status—the direct `start-task` response shape ([sla-response-shapes.md](../../../sla-response-shapes.md)). The follow-up task is in the breached stage and activates on the SLA event; no stage re-entry occurs and other stage tasks do not re-run. Resolve `slaId` and any at-risk `escalationId` against objects written in Phase 2 Step 11. Use the stage's **own** SLA for a stage-scoped response or `root`'s for a case-scoped response.

`slaId` alone is a **breach** rule. For at-risk, add a concrete `escalationId` declared on that same SLA; never use the `"any"` sentinel. This is valid on uip 1.198.0-preview.102 for stage-owned and root SLAs.

If a *stage* should take the case, put the rule on its `entryConditions` ([stage-entry-conditions/impl-json.md](../stage-entry-conditions/impl-json.md)); that is `enter-stage`, not `start-task`.

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `current-stage-entered` | — |
| `selected-tasks-completed` | `selectedTasksIds` (array) |
| `wait-for-connector` | `uipath` connector configuration (see [common](../../../connector-trigger-impl.md#target-connector-bound-condition-rule)) |
| `adhoc` | — |
| `runs-sequentially` | — |
| `sla-status-change` | `slaId`; optional at-risk `escalationId` on that same SLA |

`conditionExpression` is optional on every rule and may further gate any rule.

## Post-Write Verification

Confirm the target task's `entryConditions[]` length equals the SDD's Entry Condition row count. Each entry must have an `id` prefixed `c`, a non-empty `displayName` (SDD value or `Entry rule {N}`), and `rules` with the expected `rule` and required side fields. For `wait-for-connector`, Phase 2 requires the exact stub; after Phase 3, a resolved rule must have no `"placeholder"` values, use the owning stage's `<stageId>-<ruleId>` on inputs/outputs, and carry root bindings. A remaining stub must correspond to a reported unresolved connector.

Count parity is insufficient: if Step 10 was skipped because of a Phase 1 planning gap, parity is zero and the task silently lacks an entry rule, causing `case debug` to hang without a build-time failure. [`implementation.md § Step 12 Check 15`](../../../implementation.md#step-12--end-of-phase-3-validator-pass) is the mandatory backstop; it independently re-derives the expected rule from the source SDD.

<!-- END: impl-json.md -->
