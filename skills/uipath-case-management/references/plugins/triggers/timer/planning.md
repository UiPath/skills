# timer trigger — Planning

A case-level trigger that fires on a schedule — once at a specific time, on a repeating interval, with an optional repeat count.

## When to Use

Pick this plugin when the sdd.md describes the case as running on a schedule:

- "Every hour"
- "Daily at 9 AM"
- "Every Monday for 5 weeks"
- Cron-like phrasing

For user-initiated starts, use [manual](../manual/planning.md). For external events, use [event](../event/planning.md).

## Required Fields from sdd.md

At least one of:

| Field | Source | Notes |
|-------|--------|-------|
| `every` | sdd.md interval phrasing | `10s`, `5m`, `1h`, `2d`, `1w`, `3mo`, or raw ISO 8601 like `PT10S` |
| `at` | sdd.md start time | ISO 8601 datetime |
| `time-cycle` | sdd.md repeating expression | Raw ISO 8601 (e.g., `R/PT1H`); overrides `every`/`at`/`repeat` |

Plus optional:

| Field | Source | Notes |
|-------|--------|-------|
| `repeat` | sdd.md (optional) | Integer. Omit for infinite. |
| `display-name` | sdd.md (optional) | Defaults to `Trigger N` |

## Registry Resolution

**None.** Timer triggers have no registry representation.

## Translation Guidance

| sdd.md phrase | CLI flags |
|---------------|-----------|
| "Every hour" | `--every 1h` |
| "Every 30 minutes" | `--every 30m` |
| "Daily at 9 AM UTC" | `--every 1d --at 2026-04-26T09:00:00.000Z` |
| "Every hour, 10 times" | `--every 1h --repeat 10` |
| "Infinite, every hour (raw ISO)" | `--time-cycle R/PT1H` |

When the sdd.md phrasing is ambiguous, **AskUserQuestion** with 2–3 candidate interpretations + "Something else".

## tasks.md Entry Format

```markdown
## T02: Configure timer trigger "<display-name>"
- every: 1h
- at: 2026-04-26T09:00:00.000Z   # optional
- repeat: 5                        # optional
- time-cycle: R/PT1H               # optional, overrides above
- order: after T01
- verify: Confirm Result: Success, capture TriggerId
```
