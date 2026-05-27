# stage-entry-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 3 only. Phase 2 does not write conditions. See [`../../../phased-execution.md`](../../../phased-execution.md).

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

## Procedure

1. Generate condition ID: `Condition_` + 6 alphanumeric chars
2. Generate rule ID: `Rule_` + 6 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Initialize `stageNode.data.entryConditions = []` if absent (regular Stage is created without this key — see [`../../stages/impl-json.md`](../../stages/impl-json.md))
5. Read `rule-type` and `is-interrupting` from tasks.md; pick the recipe below
6. Append the condition object to `stageNode.data.entryConditions[]`

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

### wait-for-connector — interrupting on external event

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "wait-for-connector",
    "conditionExpression": "=js:event.fraudScore > 0.8"
  }
]]
```

Set `isInterrupting: true` for exception/fraud/escalation flows.

`conditionExpression` uses bare `=js:<expr>` (no outer parens). For combined boolean expressions, wrap each sub-clause in parens before joining: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Rule-Type Catalog

| `rule` | Required extra field |
|---|---|
| `case-entered` | — |
| `selected-stage-completed` | `selectedStageId` |
| `selected-stage-exited` | `selectedStageId` |
| `user-selected-stage` | — |
| `wait-for-connector` | — |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires.

## Post-Write Verification

Confirm target stage's `data.entryConditions[]` contains the new object with `id`, `isInterrupting` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field.
