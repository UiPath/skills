# stage-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes the condition. A `wait-for-connector` rule gets the canonical stub; Phase 3 Step 10.5 upgrades only its `uipath` when resolved. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the Phase 2 stage-entry condition directly to the target stage's `data.entryConditions[]`; no CLI call is needed. Step 10.5 performs the separate connector-rule upgrade.

## Condition JSON Shape

Condition `id` is `Condition_` + 6 random chars; rule `id` is `Rule_` + 6 random chars. Rules use DNF: outer array = OR, inner array = AND. Map each SDD entry-condition row to one `entryConditions[]` object; never merge rows into one condition or AND group.

```json
{"id":"Condition_xC1XyX","displayName":"After Triage","isInterrupting":false,"rules":[[{"id":"Rule_jdBFrJ","rule":"selected-stage-exited","selectedStageIds":["Stage_aB3kL9"]}]]}
```

## Procedure

1. Generate `Condition_` + 6 alphanumeric chars for the condition ID.
2. Generate `Rule_` + 6 alphanumeric chars for the rule ID.
3. Locate the target stage in `schema.nodes` by ID.
4. Initialize `stageNode.data.entryConditions = []` if absent (regular Stage is created without this key — see [`../../stages/impl-json.md`](../../stages/impl-json.md)).
5. Read the SDD Stage Entry Conditions row's rule type and interrupting flag and apply its recipe below.
6. Set `displayName` to the row's `Display Name`, or `Entry rule {N}` when absent. `N` is case-wide: scan every stage's `data.entryConditions[]` and every task's `entryConditions[]` in the whole `caseplan.case` for existing `Entry rule <number>` names; use highest + 1, or `1` when none. Never emit a blank or omitted name. A per-stage counter collides with defaulted task conditions — [case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness).
7. Append the condition to `stageNode.data.entryConditions[]`; repeat steps 1–7 once per row and append one object per row. Never fold rows into one `rules` group.

## Rule Types

### case-entered — first-stage entry

Use:

```json
"rules":[[{"id":"Rule_xxxxxx","rule":"case-entered"}]]
```

### selected-stage-completed / selected-stage-exited — upstream stage trigger

Use `selected-stage-completed` when completion semantics are required; otherwise use `selected-stage-exited`. Both require `selectedStageIds` as an array, including for one stage:

```json
"rules":[[{"id":"Rule_xxxxxx","rule":"selected-stage-exited","selectedStageIds":["Stage_aB3kL9"]}]]
```

### user-selected-stage — target of a `wait-for-user` exit

Use:

```json
"rules":[[{"id":"Rule_xxxxxx","rule":"user-selected-stage"}]]
```

It fires when an upstream stage exits via a `wait-for-user` exit condition and the user selects this stage. Only stages declaring `user-selected-stage` appear in the picker.

### sla-status-change — case/stage SLA at-risk or breach

Resolve `(sla-target, sla-display-name)` against the SLA object written in Phase 2 Step 11, then cross-check the same ID in `id-map.json`; `slaId` is always required and must never be matched by array index. Resolve `(sla-target, escalation-display-name)` only for a row that has one (at-risk). A breach element has no escalation field; do not invent one.

Persist breach with `slaId` alone:

```json
"rules":[[{"id":"Rule_xxxxxx","rule":"sla-status-change","slaId":"sla_aB3kL9Qx"}]]
```

Persist at-risk with `slaId` and a concrete escalation declared on that SLA:

```json
"rules":[[{"id":"Rule_xxxxxx","rule":"sla-status-change","slaId":"sla_aB3kL9Qx","escalationId":"esc_xY2mNp"}]]
```

`isInterrupting` comes from the SDD row, not SLA scope; the SLA may be on `root` or any stage, and `validate` passes with either `isInterrupting` value. Never emit Case Designer's `"any"` escalation sentinel: released `validate` rejects it as a missing escalation. Use separate rows for both statuses.

**This scope is the `enter-stage` response — a stage takes the case.** A `start-task` response puts the same rule on the follow-up **task's** `entryConditions` instead ([task-entry-conditions/impl-json.md](../task-entry-conditions/impl-json.md)). Do **not** author `start-task` as a stage-entry rule on the breached stage: although `validate` accepts it, re-entering the stage reruns every task whose `shouldRunOnlyOnce` is `false` (the default), not only the intended follow-up. Response choice, status shape, interrupting semantics, and defects `validate` cannot see: [sla-response-shapes.md](../../../sla-response-shapes.md). Non-interrupting lanes retain `data.stageType: "secondary"` and `isRequired: false`; never demote them to a regular stage.

> **Global scope.** The rule can fire while any stage covered by the referenced SLA is active. Do not add matching stage-exit conditions or duplicate escalation tasks on every primary stage.

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; final inputs/outputs use stage-scoped `elementId = <stageId>-<ruleId>`. Preserve optional `conditionExpression` and `isInterrupting`.

Defer rule output binding with the stub. After Phase 3 produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings; `elementId` remains `<stageId>-<ruleId>`.

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `case-entered` | — |
| `selected-stage-completed` | `selectedStageIds` (array, even for one stage) |
| `selected-stage-exited` | `selectedStageIds` (array, even for one stage) |
| `user-selected-stage` | — |
| `sla-status-change` | `slaId` from the Step 11 SLA object; `escalationId` **at-risk only** (omit for breach) |
| `wait-for-connector` | `uipath` connector configuration (see [common](../../../connector-trigger-impl.md#target-connector-bound-condition-rule)) |

`conditionExpression` is optional on every rule. When present, add it to further gate firing with strict `===` / `!==`, never loose `==` / `!=`; normalize SDD shorthand such as `approved == true` to `=js:vars.approved === true` rather than transcribing `==`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm the target stage's `data.entryConditions[]` contains the new object with an ID, non-empty `displayName` (SDD value or `Entry rule {N}`), SDD-matching `isInterrupting`, and `rules` containing the expected `rule` and required fields. For `sla-status-change`, verify `slaId` resolves to an object on the declared SLA target and `isInterrupting` matches the declared response; at-risk requires an `escalationId` resolving on that SLA, while breach requires none. Missing `escalationId` on breach is correct—do not add one, which silently converts it to at-risk ([sla-response-shapes.md § defects `validate` cannot see](../../../sla-response-shapes.md)).

For `wait-for-connector`, Phase 2 must contain the exact stub. After Phase 3, a resolved rule must have no `"placeholder"` values, use `<stageId>-<ruleId>` for inputs/outputs, and carry root bindings. A remaining stub must map to a reported unresolved connector.

<!-- END: impl-json.md -->