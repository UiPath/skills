# stage-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Written in Phase 2 (Step 10) — every StageId / TaskId / variable ID a condition references exists by then. `wait-for-connector` is the one exception: Phase 2 writes it with a stub `uipath`; Phase 3 Step 10.5 upgrades the stub in place. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the stage-entry condition directly to the target stage's `data.entryConditions[]`. No CLI command needed.

## Condition JSON Shape

> **ID format.** Condition `id` is `Condition_` + 6 random chars. Rule `id` is `Rule_` + 6 random chars.

```json
{
  "id": "Condition_xC1XyX",
  "displayName": "After Triage",
  "isInterrupting": false,
  "rules": [
    [
      {
        "id": "Rule_jdBFrJ",
        "rule": "selected-stage-exited",
        "selectedStageId": "Stage_aB3kL9"
      }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

> **One row = one condition object.** Each entry-condition row in tasks.md/SDD maps to a **separate** object in `entryConditions[]`. Never merge multiple rows into a single condition's `rules` AND group.

## Procedure

1. Generate condition ID: `Condition_` + 6 alphanumeric chars
2. Generate rule ID: `Rule_` + 6 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Initialize `stageNode.data.entryConditions = []` if absent (regular Stage is created without this key — see [`../../stages/impl-json.md`](../../stages/impl-json.md))
5. Read `rule-type` and `is-interrupting` from tasks.md; pick the recipe below
6. Set `displayName`: use tasks.md `display-name` if present; else default to `Entry Rule {N}`, where `N` = the 1-based index this condition takes in `stageNode.data.entryConditions[]` (i.e. `entryConditions.length + 1` at append time). Never emit a blank or omitted `displayName`.
7. Append the condition object to `stageNode.data.entryConditions[]`. **When the table has multiple rows, repeat steps 1–7 once per row** — append one condition object per row. Never fold multiple rows into a single condition's `rules` group.

## Rule Types

### case-entered — first-stage entry

```json
"rules": [[ { "id": "Rule_xxxxxx", "rule": "case-entered" } ]]
```

### selected-stage-completed / selected-stage-exited — upstream stage trigger

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "selected-stage-exited",
    "selectedStageId": "Stage_aB3kL9"
  }
]]
```

Swap `rule` to `selected-stage-completed` when completion semantics are required.

### user-selected-stage — target of a `wait-for-user` exit

```json
"rules": [[ { "id": "Rule_xxxxxx", "rule": "user-selected-stage" } ]]
```

Fires when an upstream stage exits via a `wait-for-user` exit condition and the user picks this stage as the next one. The stage must opt in by declaring this rule — only stages with `user-selected-stage` are presented in the picker.

### sla-status-change — case/stage SLA at-risk or breach

Resolve the T-entry's `(sla-target, sla-display-name)` against `tasks.md §4.8`, then read the preallocated ID from `id-map.json` (Step 9.9). `slaId` is always required; never match by array index. Resolve `(sla-target, escalation-display-name)` **only when the T-entry carries one** — an at-risk response. A breach T-entry has no escalation field, and none is invented.

Breach — `slaId` alone:

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "sla-status-change",
    "slaId": "sla_aB3kL9Qx"
  }
]]
```

At-risk — adds a concrete escalation declared on that same SLA:

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "sla-status-change",
    "slaId": "sla_aB3kL9Qx",
    "escalationId": "esc_xY2mNp"
  }
]]
```

Escalation presence carries the status: `slaId` alone is a **breach** rule (an absent `escalationId` is the persisted representation of Breached); `slaId` plus a concrete **at-risk** `escalationId` on that SLA is an at-risk rule. Never emit the Case Designer's `"any"` escalation sentinel — released `validate` rejects it as a missing escalation. Use separate entry-condition rows when the same stage handles both statuses. Set the containing condition's `isInterrupting` from the T-entry, not from the SLA's scope. The referenced SLA may live on `root` or on any stage; `validate` passes with `isInterrupting` either value.

**This scope is the `enter-stage` response — a stage takes the case.** A `start-task` response puts the same rule on the follow-up **task's** `entryConditions` instead ([task-entry-conditions/impl-json.md](../task-entry-conditions/impl-json.md)). Do **not** author `start-task` as a stage-entry rule on the breached stage: `validate` accepts it, but re-entering the stage re-runs every task in it whose `shouldRunOnlyOnce` is `false` (the default), not just the intended follow-up. Response choice, status shape, interrupting semantics, and the defects `validate` cannot see: [sla-response-shapes.md](../../../sla-response-shapes.md). Non-interrupting lanes keep `data.stageType: "secondary"` and `isRequired: false` — never demote them to a regular stage.

> **Global scope.** This one entry rule can fire while any stage covered by the referenced SLA is active. Do not add matching stage-exit conditions or duplicate escalation tasks on every primary stage.

### wait-for-connector — bind a connector event

Phase contract (stub at Step 10, real at Step 10.5, brownfield one-pass, output dispatch, two verification passes): [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract).

**Stage-scoped:** `elementId = <stageId>-<ruleId>` on inputs and outputs. `conditionExpression` is optional — an extra `=js:` gate on **case state** (`vars.X`), NOT the event payload (no `event` namespace). Set `isInterrupting: true` on the condition for exception/fraud/escalation lanes.

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `case-entered` | — |
| `selected-stage-completed` | `selectedStageId` |
| `selected-stage-exited` | `selectedStageId` |
| `user-selected-stage` | — |
| `sla-status-change` | `slaId` from Step 9.9 `id-map.json`; `escalationId` **at-risk only** (omit for breach) |
| `wait-for-connector` | `uipath` connector configuration (see [common](../../../connector-trigger-common.md#target-connector-bound-condition-rule)) |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. **Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim).** Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

> **Cross-task output references inside a `=js:` expression use the marker, always.** Write `vars.$xref('Stage','Task','output')`, never a bare `=vars.<id>` — Step 11.5 resolves every marker once all outputs are minted and deduped (SKILL.md Rule 10, [bindings-and-expressions.md](../../../bindings-and-expressions.md)). This holds for connector and non-connector producers alike; a rule's own outputs are not addressable by a marker at all — bind them to a case variable with `->` and reference the variable.

## Post-Write Verification

Confirm target stage's `data.entryConditions[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Entry Rule {N}` default), `isInterrupting` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. For `sla-status-change`, run the journey-dependent check in [sla-response-shapes.md § Post-write check for an `sla-status-change` rule](../../../sla-response-shapes.md#6-post-write-check-for-an-sla-status-change-rule). Scope-specific: `isInterrupting` on the containing condition must match the declared response (this field is stage-level only — see [case-schema.md](../../../case-schema.md)). For `wait-for-connector`, use the two-pass check in [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract). Full `validate` flags a missing `rule.uipath`/`context` (`connector activity missing`) but not its internals (a wrong `serviceType` passes) — confirm the connector resolves in Studio Web.
