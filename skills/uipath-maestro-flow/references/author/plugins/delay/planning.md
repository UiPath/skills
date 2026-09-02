# Delay Node — Planning

## Node Type

`core.logic.delay`

## When to Use

Use a Delay node to pause execution for a duration or until a specific date.

### Selection Heuristics

| Situation | Use Delay? |
| --- | --- |
| Fixed duration pause (wait 15 minutes, wait 1 day) | Yes |
| Wait until a specific date/time | Yes |
| Wait for external work to complete | No — use [Queue](../queue/planning.md) (`create-and-wait`) |
| Wait for human input | No — use [HITL](../hitl/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `timerType` | Yes | `timeDuration` or `timeDate` |
| `timerPreset` | Yes | Preset value or `custom` |
| `timerValue` | Conditional | Required when `timerPreset: "custom"` (ISO 8601 duration) |
| `timerDate` | Conditional | Required when `timerType: "timeDate"` (ISO 8601 datetime or `=js:` expression) |

## Duration Presets

| Preset Value | Duration |
| --- | --- |
| `PT5M` | 5 minutes |
| `PT15M` | 15 minutes |
| `PT30M` | 30 minutes |
| `PT1H` | 1 hour |
| `PT6H` | 6 hours |
| `PT12H` | 12 hours |
| `P1D` | 1 day |
| `P1W` | 1 week |
| `custom` | Use `timerValue` for custom ISO 8601 duration |

## ISO 8601 Duration Format

`P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S`

Examples: `PT30S` (30 seconds), `PT2H30M` (2.5 hours), `P3DT12H` (3 days 12 hours)
