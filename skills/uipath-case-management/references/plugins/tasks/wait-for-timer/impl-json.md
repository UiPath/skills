# wait-for-timer task — Implementation (Direct JSON Write)

Write the timer task directly to `caseplan.json`. No CLI command needed.

## Task JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tWm4Vx9Tp",
  "type": "wait-for-timer",
  "displayName": "Approval Escalation Timer",
  "elementId": "Stage_aB3kL9-tWm4Vx9Tp",
  "isRequired": false,
  "shouldRunOnlyOnce": true,
  "data": {
    "timerType": "timeDuration",
    "timeDuration": "PT3M"
  }
}
```

## Procedure

**Step 1 — Create task with empty data:**

1. Generate task ID: `t` + 8 alphanumeric chars (unique across all tasks)
2. Generate elementId: `<stageId>-<taskId>`
3. Write the task with `"data": {}` to the target stage's `tasks[]` array (in its own task set)

```json
{
  "id": "tWm4Vx9Tp",
  "type": "wait-for-timer",
  "displayName": "Approval Escalation Timer",
  "elementId": "Stage_aB3kL9-tWm4Vx9Tp",
  "isRequired": false,
  "shouldRunOnlyOnce": true,
  "data": {}
}
```

**Step 2 — Populate timer details:**

4. Read the timer type from tasks.md (`every`, `at`, or `time-cycle`)
5. Set `data.timerType` and the corresponding duration field (see below)

**Step 3 (separate):** Entry conditions are added in Step 10

## Timer Types

### timeDuration — fixed delay

```json
"data": { "timerType": "timeDuration", "timeDuration": "PT3M" }
```

ISO 8601 duration format (e.g., `PT3M`, `PT1H30M`, `P2D`). Time units use `PT` prefix, date units use `P` (no `T`). Weeks → `P7D` (Luxon doesn't output `W`).

### timeDate — specific datetime

```json
"data": { "timerType": "timeDate", "timeDate": "2026-04-26T09:00:00.000+00:00" }
```

ISO 8601 datetime with timezone offset. Always include milliseconds and offset.

### timeCycle — repeating interval

```json
"data": { "timerType": "timeCycle", "timeCycle": "R5/2026-03-03T12:00:00.000+00:00/PT1H" }
```

Composite format: `R{repeatCount}/{startDatetime}/{duration}`

| Example | Meaning |
|---|---|
| `R/PT15S` | Every 15 seconds, infinite |
| `R5/PT1H` | Every hour, 5 times |
| `R/2026-03-03T12:00:00.000+00:00/P1D` | Daily starting March 3, infinite |

Omit repeatCount segment for infinite (`R/...`). Omit datetime segment if no start time (`R/PT1H`).

## Post-Write Verification

Confirm task exists in the correct stage with `type: "wait-for-timer"` and `data.timerType` + duration field set.
