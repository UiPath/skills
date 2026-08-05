# case-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Written in Phase 2 (Step 10) — every StageId / TaskId / variable ID a condition references exists by then. `wait-for-connector` is the one exception: Phase 2 writes it with a stub `uipath`; Phase 3 Step 10.5 upgrades the stub in place. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the case-exit condition directly into `metadata.caseExitRules[]` in `caseplan.json`. No CLI command needed.

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

### wait-for-connector — bind a connector event

Phase contract (stub at Step 10, real at Step 10.5, brownfield one-pass, output dispatch, two verification passes): [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract).

**Root-scoped:** `elementId = root-<ruleId>` on BOTH `uipath.inputs[]` and `uipath.outputs[]` (not a stage id; the input `body` gets it too, not only the outputs). Valid for both `marksCaseComplete: true` and `false`. `conditionExpression` optional.

## Rule-Type × marksCaseComplete Matrix

| `marksCaseComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-stages-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-stage-completed` | `selectedStageId` |
| `false` | `selected-stage-exited` | `selectedStageId` |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim). Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

> **Cross-task output references inside a `=js:` expression use the marker, always.** Write `vars.$xref('Stage','Task','output')`, never a bare `=vars.<id>` — Step 11.5 resolves every marker once all outputs are minted and deduped (SKILL.md Rule 10, [bindings-and-expressions.md](../../../bindings-and-expressions.md)). This holds for connector and non-connector producers alike; a rule's own outputs are not addressable by a marker at all — bind them to a case variable with `->` and reference the variable.

## Post-Write Verification

Confirm `metadata.caseExitRules[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksCaseComplete`), `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. Verify no `root` key exists at the top level.

For `wait-for-connector`, use the two-pass check in [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract). Full `validate` flags a missing `rule.uipath`/`context` (`connector activity missing`) but not its internals (a wrong `serviceType` passes) — confirm the connector resolves in Studio Web.
