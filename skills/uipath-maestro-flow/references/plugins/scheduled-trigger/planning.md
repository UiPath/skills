# Scheduled Trigger — Planning

## Node Type

`core.trigger.scheduled`

## When to Use

Use a Scheduled Trigger to start the flow on a recurring schedule instead of manual invocation.

### Selection Heuristics

| Situation | Use Scheduled Trigger? |
| --- | --- |
| Flow runs on a recurring schedule (hourly, daily, weekly) | Yes |
| Flow is started on demand by a user or API call | No — use `core.trigger.manual` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| — (none) | `output` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `timerType` | Yes | Always `timeCycle` for scheduled triggers |
| `timerPreset` | Yes | Preset value or `custom` |
| `timerValue` | Conditional | Required when `timerPreset: "custom"` (ISO 8601 repeating interval) |

## Frequency Presets

| Preset Value | Frequency |
| --- | --- |
| `R/PT5M` | Every 5 minutes |
| `R/PT15M` | Every 15 minutes |
| `R/PT30M` | Every 30 minutes |
| `R/PT1H` | Every hour |
| `R/PT6H` | Every 6 hours |
| `R/PT12H` | Every 12 hours |
| `R/P1D` | Daily |
| `R/P1W` | Weekly |
| `custom` | Use `timerValue` for custom ISO 8601 repeating interval |

## ISO 8601 Repeating Interval Format

`R/P[duration]` — `R` means repeat indefinitely, followed by duration.

Examples: `R/PT10M` (every 10 min), `R/P2D` (every 2 days), `R/PT2H30M` (every 2.5 hours)

## Key Rules

- Every flow must have exactly one trigger node
- Replaces `core.trigger.manual` — do not have both
- The trigger is always the first node in the topology
