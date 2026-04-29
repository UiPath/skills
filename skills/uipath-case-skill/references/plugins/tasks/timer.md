# Timer Task

Timer tasks (`wait-for-timer`) pause stage execution for a fixed duration, until a specific time, or on a recurring schedule.

## Timer Type Decision

| `timerType` | Use when | Format |
|---|---|---|
| `timeDuration` | Wait a fixed period from now | ISO 8601: `PT30M`, `P1D`, `PT2H30M` |
| `timeDate` | Wait until a specific point in time | ISO 8601: `2024-12-01T09:00:00` |
| `timeCycle` | Repeat on a schedule | ISO 8601: `R3/2024-01-01T00:00:00/PT1H` |

For scheduling case start, use a [timer trigger](../triggers/timer.md) instead.

---

## Implementation

### timeDuration — Wait a Fixed Period

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Wait 30 Minutes",
  "type": "wait-for-timer",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "timerType": "timeDuration",
    "timeDuration": "PT30M"
  },
  "entryConditions": [
    {
      "id": "Condition_<6chars>",
      "displayName": "Stage entered",
      "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
    }
  ]
}
```

## timeDate — Wait Until a Specific Time

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Wait Until Deadline",
  "type": "wait-for-timer",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "timerType": "timeDate",
    "timeDate": "2024-12-01T09:00:00"
  },
  "entryConditions": [
    {
      "id": "Condition_<6chars>",
      "displayName": "Stage entered",
      "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
    }
  ]
}
```

## timeCycle — Recurring Schedule

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Check Every Hour",
  "type": "wait-for-timer",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {
    "timerType": "timeCycle",
    "timeCycle": "R3/2024-01-01T08:00:00/PT1H"
  },
  "entryConditions": [
    {
      "id": "Condition_<6chars>",
      "displayName": "Stage entered",
      "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
    }
  ]
}
```

## Duration Reference

| `timeDuration` | Meaning |
|---|---|
| `"PT30M"` | 30 minutes |
| `"PT2H"` | 2 hours |
| `"P1D"` | 1 day |
| `"P7D"` | 7 days |
| `"PT2H30M"` | 2 hours 30 minutes |
