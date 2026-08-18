# case-exit-conditions — Implementation (Direct JSON Write)

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

### required-stages-completed — close when all required stages complete

```json
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-stages-completed" } ]]
```

Requires `marksCaseComplete: true`. Completes when every stage flagged `data.isRequired: true` has completed.

> **Brittle — check before choosing it.** This compiles to a literal list of every `isRequired` primary stage, and an **exited** stage never satisfies it. One stage that routes onward through a `marksStageComplete: false` exit (an SLA bump, stall, escalation or rework route) blocks this rule permanently, with no validation error. Use it only when every required stage is unbypassable; otherwise key the closure on terminal stages — see [§ Multi-terminal closure](#multi-terminal-closure--selected-stages-plural).

### selected-stage-completed / selected-stage-exited — close on a named stage

```json
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "selected-stage-completed",
    "selectedStageId": "Stage_aB3kL9"
  }
]]
```

Legal with `marksCaseComplete` **either** `true` or `false` — the flag does not gate the rule type. Swap `rule` to `selected-stage-exited` to key on a stage that left without completing.

> `selected-stage-exited` compiles to `StagesExited`, which is a different condition type from `StagesCompleted` — a completed stage does not satisfy it, and an exited stage does not satisfy a `StagesCompleted` rule. The two runtime sets are disjoint.

### Multi-terminal closure — `selected-stages` (plural)

When `tasks.md` carries `selected-stages: [...]`, emit **one condition** containing **one rule-set per stage name**. The outer array is OR, so any listed terminal closes the case:

```json
{
  "id": "Condition_xC1XyX",
  "displayName": "Case Closed",
  "marksCaseComplete": true,
  "rules": [
    [ { "id": "Rule_aaaaaa", "rule": "selected-stage-completed", "selectedStageId": "Stage_ExeWrp" } ],
    [ { "id": "Rule_bbbbbb", "rule": "selected-stage-completed", "selectedStageId": "Stage_RejWrp" } ],
    [ { "id": "Rule_cccccc", "rule": "selected-stage-completed", "selectedStageId": "Stage_WdrWrp" } ]
  ]
}
```

Each rule-set gets its own `Rule_` id. Do **not** split these across separate `caseExitRules[]` entries: OR across rule-sets within one condition is verified; OR across separate conditions is not.

### sla-status-change — close on an SLA breach or at-risk escalation

```json
"rules": [[
  { "id": "Rule_xxxxxx", "rule": "sla-status-change", "slaId": "sla_xxxxxx" }
]]
```

`slaId` alone is the Breached shape; add that SLA's at-risk `escalationId` for an at-risk close. **Contingent** — it fires only if the clock runs out, so never let it be the only completion rule. Offered by the Studio Web "Complete case when" picker (verified 2026-08-14); not probed against this skill's v27 emission target.

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; keep this root-scoped rule's `elementId = root-<ruleId>` on BOTH final `uipath.inputs[]` and `uipath.outputs[]`. Valid for both `marksCaseComplete: true` and `false`; `conditionExpression` is preserved.

**Rule output binding.** Defer it with the stub. After the Phase 3 upgrade produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings. `elementId` stays `root-<ruleId>`.

## Rule-Type × marksCaseComplete Matrix

`marksCaseComplete` does **not** gate the rule type. Every rule below is legal with `true`; every one except `required-stages-completed` is also legal with `false`.

| `rule` | `marksCaseComplete: true` | `marksCaseComplete: false` | Required extra field | Deterministic? |
|---|---|---|---|---|
| `required-stages-completed` | ✅ | — | — | yes |
| `selected-stage-completed` | ✅ | ✅ | `selectedStageId` | yes |
| `selected-stage-exited` | ✅ | ✅ | `selectedStageId` | yes |
| `sla-status-change` | ✅ | ✅ | `slaId`, optional `escalationId` | **no — contingent** |
| `wait-for-connector` | ✅ | ✅ | `uipath` connector configuration | **no — contingent** |

Emit at least one **deterministic** completion rule unless `metadata.caseManagerData.enabled` is `true`. A case whose only closure is contingent hangs whenever the external event never arrives.

## `marksCaseComplete` is designer-only — never model runtime behaviour on it

The converter emits **every** `metadata.caseExitRules[]` entry into `case.completionConditions`, unfiltered by `marksCaseComplete`. The flag is read only by FE validation (at least one `true` required, else "Case has no completion rules") and by the rules table's "Complete Case" / "Exit Case" column. It is not serialized into the executable plan.

So a `marksCaseComplete: false` rule **still closes the case** at runtime. Use `false` to express intent for rejection / withdrawal / cancellation and to keep the designer readable — never to prevent closure. The completed-vs-exited outcome the runtime acts on is `caseResolution.type`, produced by the scheduler, not by this flag.

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim). Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm `metadata.caseExitRules[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksCaseComplete`), `marksCaseComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. Verify no `root` key exists at the top level.

For `wait-for-connector`, Phase 2 verification expects the exact two-entry placeholder context plus empty inputs/outputs/bindings. After Phase 3, a resolved rule must have no `"placeholder"` values, inputs/outputs must use `root-<ruleId>`, and ConnectionId + FolderKey root bindings must exist; a remaining stub must map to a reported unresolved connector.

<!-- END: impl-json.md -->
