# wait-for-timer task — Implementation (Direct JSON Write)

> **Phase split.** Write in Phase 2 only. The timer task has no variable inputs to bind—`timerType` and duration come from the SDD's timing. Phase 3 does not revisit this plugin. See [`../../../phased-execution.md`](../../../phased-execution.md).

Write the timer task directly to `caseplan.case`; no CLI command is needed.

## Task JSON Shape

> **ID and elementId format.** `id` is `t` + 8 random chars; `elementId` is `${stageId}-${taskId}`.

```json
{
  "id": "tWm4Vx9Tp",
  "type": "wait-for-timer",
  "displayName": "Approval Escalation Timer",
  "elementId": "Stage_aB3kL9-tWm4Vx9Tp",
  "isRequired": false,
  "shouldRunOnlyOnce": false,
  "description": "Holds the stage open for three minutes so the approver can respond before escalation.",
  "skipCondition": "=js:vars.skipReview === true",
  "data": { "timerType": "timeDuration", "timeDuration": "PT3M" }
}
```

> **`description` is a copy.** The task's `**Description:**` line from sdd.md, word for word. Do not shorten or reword it. `**Design Rationale:**` is a different line and goes to `tasks/build-issues.md`; use it here only when the block writes no `**Description:**`.
>
> **Envelope and data.** Take `isRequired` and `shouldRunOnlyOnce` from the SDD task envelope; default `shouldRunOnlyOnce` to `false` when omitted and never infer run-once from timer type. `data` contains ONLY `timerType` and its duration field; `skipCondition` and all other envelope fields are top-level siblings, never nested in `data` (misplacement passes `validate` silently but is never applied). The `repeat` exception is below. See [case-schema.md](../../../case-schema.md) §7 Tasks — BaseTask shape.

## Procedure

**Step 1 — Create task with empty data:**

1. Generate a unique task ID: `t` + 8 alphanumeric chars.
2. Generate `elementId`: `<stageId>-<taskId>`.
3. Write the task with `"data": {}` to the target stage's `data.tasks` using the common placement contract: strict sequential timers get their own single-task inner array; `parallel-after-predecessor` timers share the planned same next inner array even though their entry rule is `runs-sequentially`; adhoc/event-driven/fan-in/conditional-gate/standalone timers get their own single-task inner array; only explicitly parallel or parallel-after-predecessor timers may share an inner array.

**Step 2 — Populate timer details:**

4. Read the timer type from the SDD (`every`, `at`, or `time-cycle`).
5. Set `data.timerType` and its corresponding duration field below.

**Step 3 (separate):** Add entry conditions in Step 10.

## Timer Types

### timeDuration — fixed delay

```json
"data": { "timerType": "timeDuration", "timeDuration": "PT3M" }
```

Use ISO 8601 duration format (`PT3M`, `PT1H30M`, `P2D`): time units use `PT`, date units use `P` without `T`; convert weeks to `P7D` because Luxon does not output `W`. For an SDD-specified repeat count, add `data.repeat` as a string alongside `timeDuration`; omit it for a single fire. `repeat` pairs with `timeDuration` only. For bounded repetition with a start datetime, use `timeCycle`.

```json
"data": { "timerType": "timeDuration", "timeDuration": "PT1H", "repeat": "5" }
```

### timeDate — specific datetime

```json
"data": { "timerType": "timeDate", "timeDate": "2026-04-26T09:00:00.000+00:00" }
```

Use an ISO 8601 datetime with timezone offset, always including milliseconds and offset.

### timeCycle — repeating interval

```json
"data": { "timerType": "timeCycle", "timeCycle": "R5/2026-03-03T12:00:00.000+00:00/PT1H" }
```

Format: `R{repeatCount}/{startDatetime}/{duration}`. Omit `repeatCount` for infinite repetition (`R/...`) and omit the datetime when there is no start time (`R/PT1H`). `R/PT15S` means every 15 seconds, infinite; `R5/PT1H` means every hour, 5 times; `R/2026-03-03T12:00:00.000+00:00/P1D` means daily starting March 3, infinite.

## Post-Write Verification

Confirm the task exists in the correct stage with `type: "wait-for-timer"` and `data.timerType` plus its duration field set.

<!-- END: impl-json.md -->