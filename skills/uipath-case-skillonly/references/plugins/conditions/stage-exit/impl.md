# Stage Exit Conditions — Implementation

Exit conditions are placed in `stage.data.exitConditions`. Each entry has:

| Field | Required | Notes |
|---|---|---|
| `id` | ✓ | `Condition_<6chars>` |
| `displayName` | ✓ | Human label shown in the rules table |
| `type` | ✓ | One of the 6 exit types listed below |
| `marksStageComplete` | optional | `true` = exit counts as stage completion; `false` = exit fires but stage stays open or doesn't count toward `required-stages-completed` |
| `exitToStageId` | required for `send-to-stage` and `rework-stage-and-return` | Target stage UUID |
| `rules` | ✓ | `rules[][]` — outer array = OR groups, inner array = AND group |

### Stage exit `type` values

| `type` | When to use | Companion fields |
|---|---|---|
| `exit-only` | Default. Stage exits and case continues along the configured edge. Use `exitToStageId` for explicit routing. | `exitToStageId` (optional) |
| `wait-for-user` | Stage finishes its tasks then waits for a human to pick the next stage in the UI. | — |
| `return-to-origin` | Stage returns to whatever stage triggered it (ExceptionStages and re-entry loops). | — |

**Deprecated (do not use):**

| `type` | Deprecated because | Migration |
|---|---|---|
| `terminal` | Confuses stage exit with case end | Use `caseExitConditions` on root instead. Create a case exit condition with `marksCaseComplete: true` that fires when this stage completes. |
| `send-to-stage` | Implicit routing is hard to trace | Use `exit-only` with `exitToStageId`, plus an explicit `entryCondition` on the target stage with `selected-stage-exited` rule. |
| `rework-stage-and-return` | Complex implicit behavior | Use `exit-only` to route to the rework stage, plus `return-to-origin` exit on the rework stage. The origin stage needs a re-entry entry condition. |

### Rule type — `selected-tasks-completed` vs `required-tasks-completed`

Both are valid. They differ in semantics:

| Rule | When | Companion field |
|---|---|---|
| `selected-tasks-completed` | Wait for a specific subset of tasks (V12 author format — preferred for new code) | `selectedTasksIds: [<taskId>, ...]` |
| `required-tasks-completed` | Shortcut: wait for **all** tasks marked `isRequired: true` in this stage — common on `marksStageComplete: true` exits | — |

## exit-only — Standard Completion

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Required tasks completed",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## exit-only with Specific Tasks

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Assessment and approval done",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "selected-tasks-completed",
      "id": "Rule_<6chars>",
      "selectedTasksIds": ["tJJETUgZ2", "tYXPi6r8U"]
    }]]
  }
]
```

## exit-only with Expression Filter

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Approved and tasks done",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.action === 'approved'"
    }]]
  }
]
```

## exit-only with Explicit Target Stage

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Route to final stage",
    "type": "exit-only",
    "exitToStageId": "Stage_zlZulP",
    "marksStageComplete": true,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## wait-for-user — Human Selects Next Stage

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Awaiting user routing decision",
    "type": "wait-for-user",
    "marksStageComplete": false,
    "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
  }
]
```

## return-to-origin — Returns to Calling Stage

Used on **any stage** that is part of a re-entry loop, not just ExceptionStages. Two common patterns:

**Pattern A — ExceptionStage returning to whatever stage triggered it.** This is the classic use case (e.g., "Pending with customer" exception returns to Intake / Review / Settlement depending on which one entered it). See [exception stages](../../stage-types/exception-stage/impl.md).

**Pattern B — Regular Stage with a re-entry loop.** A regular stage exits via `return-to-origin` when it has been re-entered (e.g., Intake re-runs after a customer responds with missing docs, then loops back to wherever the customer-pending exception came from). Detected by counting prior runs in a variable like `vars.finishedRunCountIntake`:

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Re-entry exit — return to caller",
    "type": "return-to-origin",
    "marksStageComplete": false,
    "rules": [[{
      "rule": "selected-tasks-completed",
      "id": "Rule_<6chars>",
      "selectedTasksIds": ["<followupTaskId>"],
      "conditionExpression": "=js:(vars.finishedRunCountIntake != null && vars.finishedRunCountIntake > 0)"
    }]]
  }
]
```

| Setting | When |
|---|---|
| `marksStageComplete: true` | First-pass return — counts as a successful exit of this stage |
| `marksStageComplete: false` | Re-entry loop return — does NOT mark complete, since the original "complete" exit will fire on the first pass |

> Standard exit example with `marksStageComplete: true` for ExceptionStage:
> ```json
> { "displayName": "Return to origin", "type": "return-to-origin", "marksStageComplete": true,
>   "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]] }
> ```

## terminal — DEPRECATED

> **DEPRECATED.** Do not use `terminal` exit type. Use `caseExitConditions` on the root node instead.

**Migration:** Instead of a `terminal` stage exit, add a `caseExitConditions` entry on root that fires when this stage completes:

```json
// On root.caseExitConditions:
{
  "id": "Condition_<6chars>",
  "displayName": "Case closed when Closure stage completes",
  "marksCaseComplete": true,
  "rules": [[{
    "rule": "selected-stage-completed",
    "id": "Rule_<6chars>",
    "selectedStageId": "Stage_closure"
  }]]
}
```

This explicitly ties case completion to stage completion at the case level, making the flow easier to audit.

## send-to-stage — DEPRECATED

> **DEPRECATED.** Do not use `send-to-stage`. Use `exit-only` with `exitToStageId` plus explicit entry conditions.

**Migration:** Use `exit-only` with `exitToStageId` on the source stage, and add a `selected-stage-exited` entry condition on the target stage:

```json
// Source stage exitConditions:
{
  "id": "Condition_<6chars>",
  "displayName": "Route to escalation",
  "type": "exit-only",
  "exitToStageId": "Stage_escalation",
  "marksStageComplete": false,
  "rules": [[{
    "rule": "selected-tasks-completed",
    "id": "Rule_<6chars>",
    "selectedTasksIds": ["tFlagEscalation"],
    "conditionExpression": "=js:vars.priority === 'high'"
  }]]
}

// Target stage (Stage_escalation) entryConditions:
{
  "id": "Condition_<6chars>",
  "displayName": "Enter from Review when priority is high",
  "isInterrupting": true,
  "rules": [[{
    "rule": "selected-stage-exited",
    "id": "Rule_<6chars>",
    "selectedStageId": "Stage_review",
    "conditionExpression": "=js:vars.priority === 'high'"
  }]]
}
```

This makes routing explicit on both ends, improving traceability.

## rework-stage-and-return — DEPRECATED

> **DEPRECATED.** Do not use `rework-stage-and-return`. Build the rework loop explicitly with separate exit/entry conditions.

**Migration:** Instead of a single `rework-stage-and-return` exit:

1. **Source stage:** Use `exit-only` with `exitToStageId` to route to the rework stage
2. **Rework stage:** Use `return-to-origin` exit to return to caller
3. **Source stage:** Add an `entryCondition` with `selected-stage-exited` from the rework stage for re-entry

```json
// Source stage (Review) exitConditions — route to rework:
{
  "id": "Condition_exitToRework",
  "displayName": "Send to Coverage Check",
  "type": "exit-only",
  "exitToStageId": "Stage_coverageCheck",
  "marksStageComplete": false,
  "rules": [[{
    "rule": "selected-tasks-completed",
    "id": "Rule_<6chars>",
    "selectedTasksIds": ["tInitialReview"],
    "conditionExpression": "=js:vars.needsCoverageRecheck === true"
  }]]
}

// Rework stage (Coverage Check) exitConditions — return to origin:
{
  "id": "Condition_return",
  "displayName": "Return to origin",
  "type": "return-to-origin",
  "marksStageComplete": true,
  "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
}

// Source stage (Review) entryConditions — re-entry from rework:
{
  "id": "Condition_reentry",
  "displayName": "Re-enter from Coverage Check",
  "isInterrupting": true,
  "rules": [[{
    "rule": "selected-stage-exited",
    "id": "Rule_<6chars>",
    "selectedStageId": "Stage_coverageCheck"
  }]]
}
```

This pattern makes the round-trip explicit and allows different re-entry behavior via `finishedRunCount` variables.

## Multiple Exit Conditions (OR Logic)

A stage exits when any of its exit conditions fires:

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Approved path",
    "type": "exit-only",
    "exitToStageId": "Stage_approved",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.action === 'approved'"
    }]]
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Rejected path",
    "type": "exit-only",
    "exitToStageId": "Stage_rejected",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "required-tasks-completed",
      "id": "Rule_<6chars>",
      "conditionExpression": "=js:vars.action === 'rejected'"
    }]]
  }
]
```
