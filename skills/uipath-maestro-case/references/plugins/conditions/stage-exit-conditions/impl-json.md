# stage-exit-conditions — Implementation (Direct JSON Write)

> **Phase split.** Written in Phase 2 (Step 10) — every StageId / TaskId / variable ID a condition references exists by then. `wait-for-connector` is the one exception: Phase 2 writes it with a stub `uipath`; Phase 3 Step 10.5 upgrades the stub in place. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the stage-exit condition directly to the target stage's `data.exitConditions[]`. No CLI command needed.

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
5. Read `type`, `exit-to-stage`, `marks-stage-complete`, and `rule-type` from tasks.md; pick the recipe below
6. Set `displayName`: use tasks.md `display-name` if present; else default by `marks-stage-complete`: `true` → `Complete Rule {N}`, `false` → `Exit Rule {N}`. `N` = 1-based index **within the same label kind** — at append time, count existing entries in `stageNode.data.exitConditions[]` whose `marksStageComplete` equals this condition's value, then `N = count + 1`. FE numbers complete and exit rules with independent counters — do NOT use the array's overall length. Never emit a blank or omitted `displayName`.
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

`selectedTasksIds` is a JSON string array, not a comma-separated string. Resolve only tasks in the same stage whose entry conditions are not `adhoc`. If a selected task is ad-hoc/manual, stop and repair the plan: required routing cannot depend on optional user-launched work.

### wait-for-connector — bind a connector event

Phase contract (stub at Step 10, real at Step 10.5, brownfield one-pass, output dispatch, two verification passes): [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract).

**Stage-scoped:** `elementId = <stageId>-<ruleId>`. Place the rule in the exit condition with `type` / `marksStageComplete` like the other exit rules above. Valid at both `marksStageComplete: true` (completer) and `false` (exit-only routing). `conditionExpression` optional.

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

The exception lane's entry is `selected-stage-exited("<origin>") + IF =js:(vars.<signal> === <exception-value>)`, `Interrupting: Yes`, exiting via `return-to-origin`. The two origin exits MUST be mutually exclusive: an ungated completion → dual-fire (next stage + lane both enter); a gated completion with no divert → deadlock (escalate path has no exit). `<signal>` is the producing task's own output — no §1.5 relay var. Inside the `=js:` expression it is written as the marker `vars.$xref('<Stage>','<Task>','<output>')` and resolved at Step 11.5, never as a bare `=vars.<id>`. See [`sdd-generation-rules.md` § Logical integrity step 5](../../../sdd-generation-rules.md#logical-integrity--stage-graph).

## Rule-Type × marksStageComplete Matrix

| `marksStageComplete` | `rule` | Required extra field |
|---|---|---|
| `true` | `required-tasks-completed` | — |
| `true` | `wait-for-connector` | `uipath` connector configuration |
| `false` | `selected-tasks-completed` | `selectedTasksIds` (array) |
| `false` | `wait-for-connector` | `uipath` connector configuration |

`conditionExpression` is optional on every rule — add it to any rule to further gate when it fires. Use bare `=js:<expr>` (no outer parens); for combined boolean expressions wrap each sub-clause in parens: `=js:(vars.X === 'foo') && (vars.Y > 5)`. **Use strict `===` / `!==`, never loose `==` / `!=` — normalize SDD shorthand like `approved == true` to `=js:vars.approved === true` (do not transcribe `==` verbatim).** Full per-sink rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

> **Cross-task output references inside a `=js:` expression use the marker, always.** Write `vars.$xref('Stage','Task','output')`, never a bare `=vars.<id>` — Step 11.5 resolves every marker once all outputs are minted and deduped (SKILL.md Rule 10, [bindings-and-expressions.md](../../../bindings-and-expressions.md)). This holds for connector and non-connector producers alike; a rule's own outputs are not addressable by a marker at all — bind them to a case variable with `->` and reference the variable.

## Post-Write Verification

Confirm target stage's `data.exitConditions[]` contains the new object with `id`, non-empty `displayName` (SDD value or `Complete Rule {N}` / `Exit Rule {N}` default keyed to `marksStageComplete`), `type`, `exitToStageId` (if set), `marksStageComplete` matching the T-entry, and `rules` carrying the expected `rule` value plus any required side field. For `wait-for-connector`, use the two-pass check in [connector-trigger-common.md § Condition-rule phase contract](../../../connector-trigger-common.md#condition-rule-phase-contract).
