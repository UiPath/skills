# stage-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Phase 2 writes the condition. A `wait-for-connector` rule gets the canonical stub; Phase 3 Step 10.5 upgrades only its `uipath` when resolved. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the Phase 2 stage-exit condition directly to the target stage's `data.exitConditions[]`; this initial write needs no CLI call. Step 10.5 handles the separate connector-rule upgrade.

## Condition JSON Shape

> **ID format.** Condition `id` is `Condition_` + 6 random chars. Rule `id` is `Rule_` + 6 random chars.

```json
{
  "id": "Condition_xC1XyX",
  "displayName": "All tasks done",
  "type": "exit-only",
  "marksStageComplete": true,
  "rules": [
    [
      { "id": "Rule_jdBFrJ", "rule": "required-tasks-completed" }
    ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Procedure

1. Generate condition ID: `Condition_` + 6 alphanumeric chars
2. Generate rule ID: `Rule_` + 6 alphanumeric chars
3. Locate the target stage in `schema.nodes` by ID
4. Initialize `stageNode.data.exitConditions = []` if absent (regular Stage is created without this key — see [`../../stages/impl-json.md`](../../stages/impl-json.md))
5. Read the exit type, exit-to-stage, marks-stage-complete, and rule type from the SDD's Stage Exit Conditions row; pick the recipe below. `exit-to-stage` is a stage **name** — resolve it to `exitToStageId` through `tasks/id-map.json`; never derive the id from the label (`Stage_<name>`).
6. Set `displayName`: use the SDD row's `Display Name` if present; else default by `marks-stage-complete`: `true` → `Complete Rule {N}`, `false` → `Exit Rule {N}`. FE keeps the two kinds on independent counters, but each counts **case-wide**, not within this stage: scan the whole `caseplan.json` for that kind's pattern across `metadata.caseExitRules[]` and every stage's `data.exitConditions[]`, then `N` = highest + 1 (`1` when none). A per-stage counter restarts at `1` in each stage and fails `validate` — [case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness). Never emit a blank or omitted `displayName`.
7. Append the condition object to `stageNode.data.exitConditions[]`

## Exit Types

| `type` | When to pick |
|---|---|
| `exit-only` | Default — stage exits normally; next stage resolves via entry conditions (or `exitToStageId` when set). No edges. |
| `wait-for-user` | Manual user decision required |
| `return-to-origin` | Rework / exception loop — sends the case back to the previous stage |

## Rule Types

### required-tasks-completed — default completion

```json
"type": "exit-only",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

### selected-tasks-completed — routing on specific tasks

```json
"type": "exit-only",
"marksStageComplete": false,
"rules": [[
  {
    "id": "Rule_xxxxxx",
    "rule": "selected-tasks-completed",
    "selectedTasksIds": ["t8GQTYo8O", "tWm4Vx9Tp"]
  }
]]
```

`selectedTasksIds` is a JSON string array, not a comma-separated string. Resolve each planned selector to its taskId via `tasks/id-map.json` using the task's EXACT SDD display name — never a paraphrase or shortened form (a rule labeled `Determine sign-off level` does not match a task named `Confirm funds and determine sign-off level`; the selector carries the task's exact name). Resolve only tasks in the same stage whose entry conditions are not `adhoc`. If a selected task is ad-hoc/manual, stop and repair the plan: required routing cannot depend on optional user-launched work. **Never write a `selected-tasks-completed` rule with an empty or partially resolved `selectedTasksIds`** — an unresolvable name is a stop-and-ask (AskUserQuestion: name the intended task, or repair the plan), never an empty emit. `uip maestro case validate`'s `has no task(s) selected` finding must never be the discovery mechanism (Step 12 Check 13 catches it first).

### wait-for-connector — bind a connector event

In Phase 2, always write the canonical stub from [connector-trigger-impl.md § Condition-rule phase contract](../../../connector-trigger-impl.md#condition-rule-phase-contract), regardless of connector resolution. In Phase 3 Step 10.5, a resolved connector replaces only `rule.uipath`; final inputs/outputs use stage-scoped `elementId = <stageId>-<ruleId>`. Preserve the exit condition's `type`, `marksStageComplete`, and optional `conditionExpression`.

**Rule output binding.** Defer it with the stub. After the Phase 3 upgrade produces real outputs, dispatch them per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../../variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), before root bindings. `elementId` stays `<stageId>-<ruleId>`.

### wait-for-user — manual decision gate

```json
"type": "wait-for-user",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

The case pauses after the rule fires; the user picks the next stage from candidates that carry a `user-selected-stage` entry rule.

### return-to-origin — rework loop

```json
"type": "return-to-origin",
"marksStageComplete": true,
"rules": [[ { "id": "Rule_xxxxxx", "rule": "required-tasks-completed" } ]]
```

Routes the case back to the originating stage.

Write this object directly. Do not rely on `uip maestro case stage-exit-conditions add --type return-to-origin` defaults: without the explicit completion rule and `marksStageComplete: true`, the CLI can persist an empty or non-rendering return shape.

### Divert into an exception lane (gated routing exit)

To route the **origin** stage into a decision/signal-routed exception lane (the lane then returns via `return-to-origin`), the origin carries TWO mutually-exclusive exits: a gated divert (`marksStageComplete: false`) into the lane, and a completion gated by the inverse `IF`.

```json
// origin divert → exception lane (escalate path)
{ "id": "Condition_xxxxxx", "displayName": "Escalate", "type": "exit-only",
  "marksStageComplete": false, "exitToStageId": "Stage_<exceptionLane>",
  "rules": [[ { "id": "Rule_xxxxxx", "rule": "selected-tasks-completed",
    "selectedTasksIds": ["t_<deciderTask>"],
    "conditionExpression": "=js:(vars.<signal> === <exception-value>)" } ]] }

// origin completion (normal path) — gated by the inverse IF
{ "id": "Condition_yyyyyy", "displayName": "Complete Rule 1", "type": "exit-only",
  "marksStageComplete": true,
  "rules": [[ { "id": "Rule_yyyyyy", "rule": "required-tasks-completed",
    "conditionExpression": "=js:(vars.<signal> !== <exception-value>)" } ]] }
```

The exception lane's entry is `selected-stage-exited("<origin>") + IF =js:(vars.<signal> === <exception-value>)`, `Interrupting: Yes`, exiting via `return-to-origin`. The two origin exits MUST be mutually exclusive: an ungated completion → dual-fire (next stage + lane both enter); a gated completion with no divert → deadlock (escalate path has no exit). `<signal>` is read directly from the producing task's output (no §1.5 relay var). See the design-side divert-and-return contract (case SDD content contract § Logical integrity step 5, `uipath-planner`).

## Rule-Type × marksStageComplete Matrix

| `marksStageComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-tasks-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-tasks-completed` | `selectedTasksIds` (array) |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); for combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. **Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim).** Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

## Post-Write Verification

Confirm target stage's `data.exitConditions[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksStageComplete`), `type`, `exitToStageId` (if set), `marksStageComplete` matching the SDD row, and `rules` carrying the expected `rule` value plus any required side field. For `wait-for-connector`, Phase 2 expects the exact stub; after Phase 3, a resolved rule must have no `"placeholder"` values, use `<stageId>-<ruleId>` on inputs/outputs, and carry root bindings. A remaining stub must map to a reported unresolved connector.

<!-- END: impl-json.md -->
