# case-exit-conditions — Implementation (Direct JSON Write)

> **Required reads** — open each in full (a single `cat`, or the `Read` tool) before writing this
> construct. These are not optional context; the checks that grade this work live in them.
> - [`bindings-and-expressions.md`](../../../bindings-and-expressions.md) — expression prefixes and the canonical form per sink
> - [`connector-trigger-impl.md`](../../../connector-trigger-impl.md) — connector rule/trigger JSON and the placeholder fallback
> - [`io-binding/impl-json.md`](../../variables/io-binding/impl-json.md) — output shapes, allocated ids, and `originalVar`

> **Phase split.** Phase 2 writes the condition. A `wait-for-connector` rule gets the canonical stub; Phase 3 Step 10.5 upgrades only its `uipath` when resolved. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the Phase 2 case-exit condition directly into `metadata.caseExitRules[]` in `caseplan.json`; this initial write needs no CLI call. Step 10.5 handles the separate connector-rule upgrade.

> **Destination + field name.** Array key is `caseExitRules`, lives under `metadata.caseExitRules` (top-level `metadata`). Plugin folder name `case-exit-conditions` follows the *concept*; the on-disk field is `caseExitRules`. Do NOT place at the JSON top level.

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
3. Read `caseplan.json`. Locate top-level `metadata` object (initialize `metadata: {}` if missing — should already exist from T01). Initialize `metadata.caseExitRules = []` if absent.
4. Read `rule-type` and `marks-case-complete` from tasks.md; pick the recipe below
5. Set `displayName`: use tasks.md `display-name` if present; else default by `marks-case-complete`: `true` → `Complete Rule {N}`, `false` → `Exit Rule {N}`. `N` = 1-based index **within the same label kind** — at append time, count existing entries in `metadata.caseExitRules[]` whose `marksCaseComplete` equals this condition's value, then `N = count + 1`. FE numbers complete and exit rules with independent counters — do NOT use the array's overall length. Never emit a blank or omitted `displayName`.
6. Append the condition object to `metadata.caseExitRules[]`

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

**A gate goes INSIDE the rule, not on the condition.** `conditionExpression` sits beside `rule` / `selectedStageId`, at the same level as the rule's own `id` — not next to the condition's `displayName` / `marksCaseComplete`. Every other field on a condition object is condition-scoped, which makes this the easy one to misplace, and a misplaced gate is invisible: the condition still parses, `uip maestro case validate` still passes, and the rule then fires **ungated** because nothing reads a condition-level `conditionExpression`.

```json
{
  "id": "Condition_xxxxxx",
  "displayName": "Reject after rework",
  "marksCaseComplete": false,
  "rules": [[
    {
      "id": "Rule_xxxxxx",
      "rule": "selected-stage-completed",
      "selectedStageId": "Stage_aB3kL9",
      "conditionExpression": "=js:vars.<producer output id> === \"reject\""
    }
  ]]
}
```

```json
// WRONG — gate hoisted to the condition; the rule fires unconditionally
{
  "id": "Condition_xxxxxx",
  "marksCaseComplete": false,
  "conditionExpression": "=js:vars.<id> === \"reject\"",
  "rules": [[ { "id": "Rule_xxxxxx", "rule": "selected-stage-completed", "selectedStageId": "Stage_aB3kL9" } ]]
}
```

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; keep this root-scoped rule's `elementId = root-<ruleId>` on BOTH final `uipath.inputs[]` and `uipath.outputs[]`. Valid for both `marksCaseComplete: true` and `false`; `conditionExpression` is preserved.

**Rule output binding.** Defer it with the stub. After the Phase 3 upgrade produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings. `elementId` stays `root-<ruleId>`.

## Rule-Type × marksCaseComplete Matrix

| `marksCaseComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-stages-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-stage-completed` | `selectedStageId` |
| `false` | `selected-stage-exited` | `selectedStageId` |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim). Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm `metadata.caseExitRules[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksCaseComplete`), `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. Verify no `root` key exists at the top level.

For `wait-for-connector`, Phase 2 verification expects the exact two-entry placeholder context plus empty inputs/outputs/bindings. After Phase 3, a resolved rule must have no `"placeholder"` values, inputs/outputs must use `root-<ruleId>`, and ConnectionId + FolderKey root bindings must exist; a remaining stub must map to a reported unresolved connector.

<!-- END: impl-json.md -->
