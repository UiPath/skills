# Timer Trigger — Implementation

## timeCycle (Recurring)

```json
{
  "id": "trigger_<6chars>",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": {
    "label": "Daily Trigger",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeCycle",
      "timeCycle": "R/2024-01-01T08:00:00/P1D"
    }
  }
}
```

## timeDate (One-Time)

```json
{
  "id": "trigger_<6chars>",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": {
    "label": "Scheduled Trigger",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeDate",
      "timeDate": "2024-12-01T09:00:00"
    }
  }
}
```

Connect to the first stage the same way as a manual trigger — with a `TriggerEdge`.

## timeCycle Examples

| `timeCycle` value | Schedule |
|---|---|
| `R/2024-01-01T08:00:00/P1D` | Every day at 08:00 |
| `R/2024-01-01T00:00:00/P7D` | Every 7 days |
| `R/2024-01-01T06:00:00/PT12H` | Every 12 hours |
| `R3/2024-06-01T09:00:00/PT1H` | 3 times, every 1 hour |
