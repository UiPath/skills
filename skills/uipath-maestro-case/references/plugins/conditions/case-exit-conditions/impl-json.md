# case-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 3 only. Phase 2 does not write conditions. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the case-exit condition directly into the schema-appropriate location in `caseplan.json`. No CLI command needed.

> **Schema-dependent destination + field name.** Read `Schema:` header from `tasks.md` per Rule 18.
> - **v19** → array key is `caseExitConditions`, lives under `root.caseExitConditions` (sibling of `data`, `description`, `caseIdentifier`).
> - **v20** → array key is **`caseExitRules`** (renamed), lives under `metadata.caseExitRules` (top-level `metadata`).
>
> Plugin folder name `case-exit-conditions` follows the *concept* (case exit conditions), unchanged across schemas. Only the on-disk path and field name change. Do NOT place at the JSON top level under either schema.

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
3. Read `caseplan.json`. Read `Schema:` header from `tasks.md`.
   - **v19** → locate the `root` object. Initialize `root.caseExitConditions = []` if absent.
   - **v20** → locate top-level `metadata` object (initialize `metadata: {}` if missing — should already exist from T01). Initialize `metadata.caseExitRules = []` if absent.
4. Read `rule-type` and `marks-case-complete` from tasks.md; pick the recipe below
5. Append the condition object to the schema-appropriate array:
   - **v19** → `root.caseExitConditions[]`
   - **v20** → `metadata.caseExitRules[]`

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

Confirm the schema-appropriate array contains the new object with `id`, `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field:
- **v19** → `root.caseExitConditions[]`
- **v20** → `metadata.caseExitRules[]`

Verify NO leakage: in v19 mode there is no `metadata.caseExitRules`; in v20 mode there is no `root` key at all.
