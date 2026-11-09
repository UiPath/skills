# wait-for-timer task — Planning

A stage task that suspends execution for a duration, until a time, or on a repeating cycle.

## When to Use

Use this plugin when sdd.md describes pausing or delaying execution within a stage (for example, waiting 24 hours, delaying until a time, or polling cyclically). Distinguish:

- **Case-level timer triggers** (start the case on a schedule) → [`plugins/triggers/timer/`](../../triggers/timer/planning.md)
- **Connector event wait** → [connector-trigger](../connector-trigger/planning.md)

## Required Fields from sdd.md

- `display-name`: sdd.md task name
- At least one of `timeDuration` (`--every`), `timeCycle`, or `timeDate` (`--at`)
- `repeat`: optional repetition count; omit for infinite
- `isRequired`: sdd.md, default `true`
- `runOnlyOnce`: sdd.md, default `false`; re-entry behavior comes from the SDD, not the task type

## Registry Resolution

**No cache lookup required.** Timer is built-in and has no registry representation: do not use `taskTypeId`, `enrich`, or `describe`.

## Duration Formats

Accepted `--every` values:

| Format | Example | Meaning |
|--------|---------|---------|
| Seconds | `10s` | 10 seconds |
| Minutes | `5m` | 5 minutes |
| Hours | `1h` | 1 hour |
| Days | `2d` | 2 days |
| Weeks | `1w` | 1 week |
| Months | `3mo` | 3 months |
| ISO 8601 | `PT10S` | 10 seconds (raw ISO) |

Accepted `--at` values: ISO 8601 datetime (e.g., `2026-04-26T10:00:00.000Z`).

Accepted `--time-cycle` values: raw ISO 8601 repeating interval (e.g., `R/PT1H` = repeat every hour, infinite). Overrides `--every`, `--at`, `--repeat` if set.

## Translation Guidance

- "Wait X hours" → `--every Xh`, no `--at`, no `--repeat`.
- "Every day at 9 AM" → `--every 1d --at <ISO datetime with 09:00>`.
- "Every hour, up to N times" → `--every 1h --repeat N`.
- "Run repeatedly forever every N" → `--time-cycle R/PT<N>`.

Ambiguous phrasing → **AskUserQuestion** with 2–3 candidate interpretations + "Something else".

## Fields to Resolve

Timers are built-in and have no registry dependency, so a wait-for-timer task produces **no `tasks/registry-resolved.json` entry**. These are reasoning fields only; Phase 2 reads them from sdd.md ([planning.md § Step 4](../../../planning.md)).

```text
wait-for-timer task "<display-name>" in stage "<stage>"
- every: 1h
- at: 2026-04-26T09:00:00.000Z   # optional
- repeat: 5                       # optional
- time-cycle: R/PT1H              # optional (overrides above)
- isRequired: true
- runOnlyOnce: false
- activation-mode: <sequential|parallel|event-triggered|adhoc|fan-in|conditional-gate>   # required
- entry-rule: <runs-sequentially|current-stage-entered|wait-for-connector|adhoc|selected-tasks-completed>   # required; must pair with activation-mode — see ../../conditions/task-entry-conditions/planning.md
- lane: <n>  # structural/layout position only; sequencing is the task entry rule plus data.tasks order.
- verify: Confirm Result: Success, capture TaskId
```

<!-- END: planning.md -->
