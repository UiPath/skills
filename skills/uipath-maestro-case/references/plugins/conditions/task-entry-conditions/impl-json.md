# task-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes the condition. A `wait-for-connector` rule gets the canonical stub; Phase 3 Step 10.5 upgrades only its `uipath` when resolved. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the Phase 2 task-entry condition directly to the target task's `entryConditions[]`; this initial write needs no CLI call. Step 10.5 handles the separate connector-rule upgrade.

## Condition JSON Shape

> **ID format.** Task-level condition `id` is `c` + 8 random chars. Rule `id` is `r` + 8 random chars. These differ from stage/case-level conditions (`Condition_`/`Rule_`).

```json
{
  "id": "c4fGhJ2Mn",
  "displayName": "After Approval",
  "rules": [
    [
      {
        "id": "rK9xQw3Lp",
        "rule": "selected-tasks-completed",
        "selectedTasksIds": ["t8GQTYo8O"]
      }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Procedure

1. Generate condition ID: `c` + 8 alphanumeric chars
2. Generate rule ID: `r` + 8 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Locate the target task inside `stageNode.data.tasks[lane][index]` (search every lane until the task ID is found)
5. Initialize `task.entryConditions = []` if absent
6. Read the rule type from the SDD's Entry Condition table; pick the recipe below
7. Set `displayName`: use the SDD row's `Display Name` if present; else default to `Entry Rule {N}`, where `N` = the 1-based index this condition takes in `task.entryConditions[]` (i.e. `entryConditions.length + 1` at append time). Never emit a blank or omitted `displayName`.
8. Append the condition object to `task.entryConditions[]`

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

`selectedTasksIds` is a JSON string array. Resolve each planned selector to its taskId via `tasks/id-map.json` using the task's EXACT SDD display name — never a paraphrase or shortened form. Resolve only tasks in the same stage whose entry conditions are not `adhoc`. If a selected task is ad-hoc/manual, stop and repair the plan: required downstream flow cannot depend on optional user-launched work. **Never write a `selected-tasks-completed` rule with an empty or partially resolved `selectedTasksIds`** — an unresolvable name is a stop-and-ask (AskUserQuestion: name the intended task, or repair the plan), never an empty emit. `uip maestro case validate`'s `has no task(s) selected` finding must never be the discovery mechanism (Step 12 Check 13 catches it first).

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

`conditionExpression` uses bare `=js:<expr>` (no outer parens) — per FE convention for conditions. Operators (`>`, `<`, `===`, etc.) and function calls go inline. Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim). For combined boolean expressions, wrap each sub-clause in parens before joining: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; final inputs/outputs use the owning stage's `elementId = <stageId>-<ruleId>` (not the task ID). Preserve the optional `conditionExpression`.

Both shapes re-stated below from [connector-trigger-impl.md § Target: connector-bound condition rule](../../../connector-trigger-impl.md#target-connector-bound-condition-rule) (source of truth — keep in sync). `rule.uipath` is ALWAYS `serviceType` + the four arrays; connector identity lives inside `context[]` entries, never as flat fields (`typeId` / `connectorKey` / `operation` directly on `uipath`) — a flat shape passes `validate` but is not runnable.

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

Phase 3 Step 10.5 — replace only `uipath` with the `case spec --type trigger --input-details` caseShape ([common § Procedure (Phase 3)](../../../connector-trigger-impl.md#procedure-phase-3)):

```json
"uipath": {
  "serviceType": "Intsvc.WaitForEvent",
  "context": "<caseShape.context — placeholders substituted>",
  "inputs":  "<caseShape.inputs  — var/id/elementId minted>",
  "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied>",
  "bindings": []
}
```

**Rule output binding.** Defer it with the stub. After the Phase 3 upgrade produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings. `elementId` stays `<stageId>-<ruleId>`.

### runs-sequentially — sequential task chain

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "runs-sequentially" } ]]
```

**Frontend toggle semantics:** The sequential/ordered-task-set rule is the task's only entry condition for strict sequences and for parallel siblings that start after an immediate predecessor. Preserve the task's order in the stage's `data.tasks` structure. A strict chain uses consecutive single-task inner arrays (`[[A], [B], [C]]`); explicitly parallel siblings after the same predecessor share one later inner array (`[[A], [B, C], [D]]`) and each sibling carries `runs-sequentially`. On the first task set, `runs-sequentially` means the current stage was entered; on subsequent task sets, it means the preceding task set completed. Do not use `selected-tasks-completed` or an additional `current-stage-entered` rule to express immediate-predecessor sequencing.

### sla-status-change — the `start-task` SLA response

```json
"rules": [[ { "id": "rxxxxxxxx", "rule": "sla-status-change", "slaId": "sla_aB3kL9Qx" } ]]
```

The task fires when the referenced SLA changes status — the direct shape for a `start-task` response ([sla-response-shapes.md](../../../sla-response-shapes.md)): the follow-up task lives in the breached stage and activates on the SLA event itself, so no stage re-entry is involved and the stage's other tasks do not re-run. Resolve `slaId` (and an at-risk `escalationId`) against the objects already written in Phase 2 Step 11. Reference the stage's **own** SLA for a stage-scoped response, or `root`'s for a case-scoped one.

`slaId` alone is a **breach** rule; add a concrete at-risk `escalationId` declared on that same SLA for an at-risk rule. Never the `"any"` sentinel. Verified valid on uip 1.198.0-preview.102 for both stage-owned and root SLAs.

When a *stage* should take the case instead, the rule goes on the stage's `entryConditions` ([stage-entry-conditions/impl-json.md](../stage-entry-conditions/impl-json.md)) — that is `enter-stage`, not `start-task`.

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `current-stage-entered` | — |
| `selected-tasks-completed` | `selectedTasksIds` (array) |
| `wait-for-connector` | `uipath` connector configuration (see [common](../../../connector-trigger-impl.md#target-connector-bound-condition-rule)) |
| `adhoc` | — |
| `runs-sequentially` | — |
| `sla-status-change` | `slaId`; optional at-risk `escalationId` on that same SLA |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires.

## Post-Write Verification

Confirm target task's `entryConditions[]` length equals the number of Entry Condition rows the SDD declares for this task. Each entry carries `id` (prefix `c`), non-empty `displayName` (SDD value or `Entry Rule {N}` default), and `rules` with the expected `rule` value plus any required side field. For `wait-for-connector`, Phase 2 expects the exact stub; after Phase 3, a resolved rule must have no `"placeholder"` values, use the owning stage's `<stageId>-<ruleId>` on inputs/outputs, and carry root bindings. A remaining stub must map to a reported unresolved connector.

**This count-parity check is not a safety net on its own** — it only confirms Step 10 wrote what the SDD's condition rows asked for; if the write was skipped entirely (a Phase 1 planning gap), parity holds at zero and the task silently ends up with no entry rule, which hangs `case debug` indefinitely instead of failing any build-time check. [`implementation.md § Step 12 Check 15`](../../../implementation.md#step-12--end-of-phase-3-validator-pass) is the mandatory backstop that re-derives the expected rule from the source SDD independent of whether Step 10 ran.

<!-- END: impl-json.md -->
