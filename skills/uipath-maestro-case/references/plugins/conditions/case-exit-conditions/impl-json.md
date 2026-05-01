# case-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 3 only. Phase 2 does not write conditions. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the case-exit condition directly into the `root` object's `caseExitConditions[]` array in `caseplan.json`. No CLI command needed.

> **Nesting matters.** `caseExitConditions` MUST be a property of the `root` object — a sibling of `data`, `description`, `caseIdentifier`. Do NOT place it at the JSON top level (sibling of `root`, `nodes`, `edges`). The validator silently passes but Studio Web cannot render the case.

## Condition JSON Shape

> **ID format.** Condition `id` is `Condition_` + 6 random chars. Rule `id` is `Rule_` + 6 random chars.

```json
{
  "id": "Condition_xC1XyX",
  "displayName": "Case resolved",
  "marksCaseComplete": true,
  "rules": [
    [
      { "id": "Rule_jdBFrJ", "rule": "required-stages-completed" }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Procedure

1. Generate condition ID: `Condition_` + 6 alphanumeric chars
2. Generate rule ID: `Rule_` + 6 alphanumeric chars
3. Read `caseplan.json`. Locate the `root` object. Initialize `root.caseExitConditions = []` if absent — this array lives INSIDE `root`, not at the JSON top level
4. Read `rule-type` and `marks-case-complete` from tasks.md; pick the recipe below
5. Append the condition object to `root.caseExitConditions[]`

## Rule Types

### required-stages-completed — preferred completion

```json
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-stages-completed" } ]]
```

Requires `marksCaseComplete: true`. Completes when every stage flagged `data.isRequired: true` has completed.

### selected-stage-completed / selected-stage-exited — non-completing exit

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "selected-stage-completed",
    "selectedStageId": "Stage_aB3kL9"
  }
]]
```

Requires `marksCaseComplete: false`. Swap `rule` to `selected-stage-exited` for exit-without-completion semantics.

### wait-for-connector — external event

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "wait-for-connector",
    "conditionExpression": "event.type = 'case_closed'"
  }
]]
```

Valid for both `marksCaseComplete: true` and `false`.

## Rule-Type × marksCaseComplete Matrix

| `marksCaseComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-stages-completed` | — |
| `true` | `wait-for-connector` | — |
| `false` | `selected-stage-completed` | `selectedStageId` |
| `false` | `selected-stage-exited` | `selectedStageId` |
| `false` | `wait-for-connector` | — |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires.

## Post-Write Verification

Confirm `root.caseExitConditions[]` contains the new object with `id`, `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field.
