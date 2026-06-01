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
5. Set `displayName`: use tasks.md `display-name` if present; else default by `marks-case-complete`: `true` → `Complete Rule {N}`, `false` → `Exit Rule {N}`. `N` = 1-based index **within the same label kind** — at append time, count existing entries in the schema-appropriate array whose `marksCaseComplete` equals this condition's value, then `N = count + 1`. FE numbers complete and exit rules with independent counters — do NOT use the array's overall length. Never emit a blank or omitted `displayName`.
6. Append the condition object to the schema-appropriate array:
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

### wait-for-connector — bind a connector event

Write `rule.uipath` per [connector-trigger-common.md § Target: connector-bound condition rule](../../../connector-trigger-common.md#target-connector-bound-condition-rule) (canonical rule JSON + procedure there) — a bare rule (no `uipath`) is rejected by Studio Web. **Root-scoped: `elementId = root-<ruleId>` on BOTH `uipath.inputs[]` and `uipath.outputs[]`** (not a stage id; the input `body` gets it too, not only the outputs). Valid for both `marksCaseComplete: true` and `false`. `conditionExpression` optional. If `type-id` / `connection-id` / `connector-key` is `<UNRESOLVED>`, omit `uipath` (rule emitted without its connector configuration; see [connector-trigger-common.md § Placeholder fallback](../../../connector-trigger-common.md#placeholder-fallback)).

**Rule output binding.** If the T-entry has `outputs:`, dispatch `rule.uipath.outputs[]` per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) **as the last step — after rule write, before root bindings**. `elementId` stays `root-<ruleId>` on every output entry. Skip when `uipath` is absent.

## Rule-Type × marksCaseComplete Matrix

| `marksCaseComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-stages-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-stage-completed` | `selectedStageId` |
| `false` | `selected-stage-exited` | `selectedStageId` |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm the schema-appropriate array contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksCaseComplete`), `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field:
- **v19** → `root.caseExitConditions[]`
- **v20** → `metadata.caseExitRules[]`

Verify NO leakage: in v19 mode there is no `metadata.caseExitRules`; in v20 mode there is no `root` key at all.

For `wait-for-connector`: verify `rule.uipath.serviceType` is `"Intsvc.WaitForEvent"`, `rule.uipath.context[]` is populated (placeholders substituted), inputs/outputs `elementId` is `root-<ruleId>`, and ConnectionId + FolderKey root bindings exist. CLI `validate` does NOT check `rule.uipath` — confirm via Studio Web.
