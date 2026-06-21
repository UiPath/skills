# Timer Task — Planning

Timer tasks (`wait-for-timer`) pause stage execution for a fixed duration or until a specific time.

## When to Use

| Situation | Use timer task? |
|---|---|
| Wait a fixed amount of time before the next step | Yes |
| Wait until a specific date/time | Yes |
| Run on a recurring schedule | Yes (timeCycle) |
| Case triggered on a schedule | No — use a [timer trigger](../../triggers/timer/planning.md) instead |

## Timer Type Decision

| `timerType` | Use when | Format |
|---|---|---|
| `"timeDuration"` | Wait a fixed period from now | ISO 8601 duration: `PT30M`, `P1D`, `PT2H30M` |
| `"timeDate"` | Wait until a specific point in time | ISO 8601 datetime: `2024-12-01T09:00:00` |
| `"timeCycle"` | Repeat on a schedule (N times at interval) | ISO 8601 interval: `R3/2024-01-01T00:00:00/PT1H` |

## ISO 8601 Duration Cheat Sheet

| Duration | Meaning |
|---|---|
| `PT30M` | 30 minutes |
| `PT2H` | 2 hours |
| `P1D` | 1 day |
| `P7D` | 7 days |
| `PT2H30M` | 2 hours 30 minutes |

## ISO 8601 Repeating Interval Format

`R<count>/<startDateTime>/<duration>`

- `R3/2024-01-01T00:00:00/PT1H` — repeat 3 times, every 1 hour starting Jan 1 2024
- `R/2024-01-01T08:00:00/P1D` — repeat indefinitely, every day starting Jan 1 2024
