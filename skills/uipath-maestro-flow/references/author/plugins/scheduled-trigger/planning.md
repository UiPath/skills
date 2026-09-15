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
| `timerValue` | Yes | The cycle expression — ISO 8601 repeating interval or Quartz cron |
| `timerType` | Yes | Always `timeCycle` for scheduled triggers |

Set both. The definition's `required` array names only `timerValue`, so a flow
without `timerType` passes `validate`, but `model.values` maps
`timerType -> inputs.timerType` to build the BPMN timer event. Omitting it
leaves the event without its cycle type.

The definition the registry serves (1.2) has no `timerPreset` input. Every
frequency, common or not, goes in `timerValue`.

## Cycle Expression Formats

### ISO 8601 Repeating Interval

`R/P[duration]` — `R` means repeat indefinitely, followed by duration.

| Value | Frequency |
| --- | --- |
| `R/PT5M` | Every 5 minutes |
| `R/PT15M` | Every 15 minutes |
| `R/PT30M` | Every 30 minutes |
| `R/PT1H` | Every hour |
| `R/PT6H` | Every 6 hours |
| `R/PT12H` | Every 12 hours |
| `R/P1D` | Daily |
| `R/P1W` | Weekly |

Any other interval uses the same form: `R/PT10M` (every 10 min), `R/P2D` (every 2 days).

Exactly one duration unit, non-zero, and in range: `Y` 1-9999, `M` 1-12, `W` 1-52, `D` 1-31, `H` 1-23, `T…M` 1-59, `S` 1-59.

| Rejected | Why | Instead |
| --- | --- | --- |
| `R/PT24H` | out of range | `R/P1D` |
| `R/PT0H` | zero, never fires | any non-zero interval |
| `R/PT2H30M` | two units | not expressible as an interval — see below |

An interval may be anchored to a start instant: `R/2026-05-14T09:00:00Z/P1W`.

### Quartz Cron

Six or seven whitespace-separated fields. Use it for a clock-aligned schedule
an interval cannot express: a fixed time of day, a set of weekdays, a day of
the month.

Examples: `0 0 9 ? * MON-FRI` (weekdays at 09:00), `0 0 2 1 * ? *` (02:00 on the 1st)

Put `?` in day-of-month or day-of-week, never a value in both.

`validate` checks cron field shape only, never semantics: `0 0 12 * * *` (no
`?`) and even `ABC ABC ABC ABC ABC ABC` pass it. Read the expression back field
by field before shipping.

Cron does not extend the set of *periods* available. An arbitrary period is
expressible in neither form: the interval takes one in-range unit and no single
cron expression carries a sub-hour period across the hour boundary. Every 2.5
hours and every 90 minutes have no representation here — pick a period one of
the two forms accepts (`R/PT2H`, `R/PT3H`) and say so, rather than shipping a
cron that silently fires on a different cadence.

## Key Rules

- Every flow must have exactly one trigger node
- Replaces `core.trigger.manual` — do not have both
- The trigger is always the first node in the topology
