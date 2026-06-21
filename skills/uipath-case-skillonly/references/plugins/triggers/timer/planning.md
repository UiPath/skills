# Timer Trigger — Planning

A timer trigger starts a new case automatically on a schedule, without human initiation.

## When to Use

| Situation | Use timer trigger? |
|---|---|
| Case should start on a recurring schedule | Yes |
| Case should start at a specific date/time | Yes |
| Case is started by a human (portal, API) | No — use [manual trigger](../manual/impl.md) |
| Case is started by an external event (webhook, connector) | No — use event trigger (connector enrichment required) |

## Timer Type Decision

| `timerType` | Use when |
|---|---|
| `"timeCycle"` | Recurring schedule (daily, weekly, every N hours) |
| `"timeDate"` | One-time trigger at a specific datetime |
| `"timeDuration"` | Trigger after a delay from case creation — rare for triggers |

## timeCycle Format

ISO 8601 repeating interval: `R<count>/<startDateTime>/<duration>`

| Example | Meaning |
|---|---|
| `R/2024-01-01T08:00:00/P1D` | Every day at 08:00 (indefinitely) |
| `R/2024-01-01T00:00:00/P7D` | Every week |
| `R3/2024-06-01T09:00:00/PT1H` | 3 times, every hour starting June 1 |
