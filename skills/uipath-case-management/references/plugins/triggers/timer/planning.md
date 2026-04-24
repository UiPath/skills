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

Compose a single canonical `timeCycle` string (ISO 8601 repeating interval) from the sdd.md phrasing.

| Field | Source | Notes |
|-------|--------|-------|
| `timeCycle` | sdd.md schedule phrasing → ISO 8601 repeating interval | Canonical format: `R[<count>]/[<start-iso>/]<duration>` |
| `displayName` | sdd.md (optional) | Defaults to `Trigger N` where N = existing-trigger-count + 1 |

## Registry Resolution

**None.** Timer triggers have no registry representation.

## timeCycle Composition

The `timeCycle` field is a single ISO 8601 repeating-interval expression:

```
R[<count>]/[<start-iso>/]<duration>
```

- `R` alone — infinite repetitions
- `R<n>` — exactly `n` repetitions
- `<start-iso>` — optional start moment, ISO 8601 datetime (include explicit offset or `Z`)
- `<duration>` — ISO 8601 duration (`PT<time>` for sub-day units, `P<date>` for day-or-larger units)

### Duration reference

| Friendly phrase | ISO 8601 duration |
|-----------------|-------------------|
| 10 seconds | `PT10S` |
| 5 minutes | `PT5M` |
| 1 hour | `PT1H` |
| 2 days | `P2D` |
| 1 week | `P1W` |
| 3 months | `P3M` |

### sdd.md phrasing → `timeCycle`

| sdd.md phrasing | `timeCycle` |
|-----------------|-------------|
| Every hour | `R/PT1H` |
| Every 30 minutes | `R/PT30M` |
| Daily at 9 AM UTC | `R/2026-04-26T09:00:00.000Z/P1D` |
| Every hour, 10 times | `R10/PT1H` |
| Every 10 min, 12 times starting 2026-04-21 22:00 PDT | `R12/2026-04-21T22:00:00.000-07:00/PT10M` |
| Every day at 9 AM UTC, 30 times | `R30/2026-04-26T09:00:00.000Z/P1D` |

When the sdd.md phrasing is ambiguous (missing start time, timezone, repeat count), **AskUserQuestion** with 2–3 candidate interpretations + "Something else". Do not silently default timezone or count.

## tasks.md Entry Format

```markdown
## T02: Configure timer trigger "<display-name>"
- timeCycle: R12/2026-04-21T22:00:00.000-07:00/PT10M
- displayName: "<optional — defaults to Trigger N>"
- sdd-intent: "<prose restatement for reviewer — e.g. Every 10 min, starting 2026-04-21 22:00 PDT, 12 times>"
- order: after T01
- verify: node added to schema.nodes with data.uipath.serviceType == Intsvc.TimerTrigger; entry-points.json has matching entry; timeCycle exact match
```

`sdd-intent` is reviewer-only prose — the execution phase ignores it. `timeCycle` is the canonical executable field, consumed identically by both [`impl-cli.md`](impl-cli.md) (passed as `--time-cycle`) and [`impl-json.md`](impl-json.md) (written directly into `node.data.uipath.timeCycle`).
