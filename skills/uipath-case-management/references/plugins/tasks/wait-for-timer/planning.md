# wait-for-timer task — Planning

A timer task inside a stage. Suspends the stage for a duration, until a specific time, or on a repeating cycle.

## When to Use

Pick this plugin when the sdd.md describes a task that **pauses or delays execution** within a stage. Typical patterns:

- "Wait 24 hours before reminding"
- "Delay until next business day at 9 AM"
- "Poll every hour for up to 5 iterations"

Distinguish from:

- **Case-level timer triggers** (start the case on a schedule) → [`plugins/triggers/timer/`](../../triggers/timer/planning.md)
- **Connector event wait** → [connector-trigger](../connector-trigger/planning.md)

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name | Written to `task.displayName` |
| Either `timeDuration` (`every`) OR `timeCycle` OR `timeDate` (`at`) | sdd.md timer semantics | At least one required. Written to `task.data.timerType` + corresponding field. |
| `repeat` | sdd.md (optional) | Number of repetitions — omit for infinite |
| `isRequired` | sdd.md (default `true`) | Written to `task.isRequired` |

## Registry Resolution

**No cache lookup required.** Timer is a built-in task type with no registry representation — no `taskTypeId`, no `enrich`, no `describe`.

## Duration Formats

Accepted `every` values:

| Format | Example | Meaning |
|--------|---------|---------|
| Seconds | `10s` | 10 seconds |
| Minutes | `5m` | 5 minutes |
| Hours | `1h` | 1 hour |
| Days | `2d` | 2 days |
| Weeks | `1w` | 1 week |
| Months | `3mo` | 3 months |
| ISO 8601 | `PT10S` | 10 seconds (raw ISO) |

Accepted `at` values: ISO 8601 datetime (e.g., `2026-04-26T10:00:00.000Z`).

Accepted `timeCycle` values: raw ISO 8601 repeating interval (e.g., `R/PT1H` = repeat every hour, infinite). Overrides `every`, `at`, `repeat` if set.

## Translation Guidance

- "Wait X hours" → `every: Xh`, no `at`, no `repeat`.
- "Every day at 9 AM" → `every: 1d`, `at: <ISO datetime with 09:00>`.
- "Every hour, up to N times" → `every: 1h`, `repeat: N`.
- "Run repeatedly forever every N" → `timeCycle: R/PT<N>`.

Ambiguous phrasing → **AskUserQuestion** with 2–3 candidate interpretations + "Something else".

## tasks.md Entry Format

```markdown
## T<n>: Add wait-for-timer task "<display-name>" to "<stage>"
- every: 1h
- at: 2026-04-26T09:00:00.000Z   # optional
- repeat: 5                       # optional
- time-cycle: R/PT1H              # optional (overrides above)
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
