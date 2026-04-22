# Timer Trigger — sdd fragment

Minimal sdd fragment exercising only the `triggers/timer` plugin. No stages, edges, tasks, or conditions — the fixture validates the trigger-emission recipe in isolation.

## Case

**Name:** TimerProbe
**Description:** Probe case exercising the timer trigger migration.

## Triggers

**TIMER (schedule)**
- **displayName:** `10-min Poll`
- **Schedule:** Every 10 minutes, starting `2026-04-21T22:00:00.000-07:00`, repeat 12 times.
- **Canonical `timeCycle`:** `R12/2026-04-21T22:00:00.000-07:00/PT10M`

## Expected tasks.md excerpt

```markdown
## T01: Create case file "TimerProbe"
- file: "<SolutionDir>/TimerProbe/caseplan.json"
- case-identifier: "TimerProbe"
- identifier-type: constant
- case-app-enabled: false
- description: "Probe case exercising the timer trigger migration."
- order: first
- verify: Confirm Result: Success, capture file path and initial Trigger node ID

## T02: Configure timer trigger "10-min Poll"
- timeCycle: R12/2026-04-21T22:00:00.000-07:00/PT10M
- displayName: "10-min Poll"
- sdd-intent: "Every 10 minutes, starting 2026-04-21 22:00 PDT, 12 times"
- order: after T01
- verify: node added to schema.nodes with data.uipath.serviceType == Intsvc.TimerTrigger; entry-points.json has matching entry; timeCycle matches
```

## Notes for the fixture

- T01 stays CLI (`case` plugin is still CLI per the matrix). T02 is the only thing the JSON recipe produces.
- Starting state for T02: `trigger_1` (manual, minimal) already exists in `caseplan.json` and `entry-points.json` courtesy of T01.
- Therefore T02 takes the **secondary-trigger path** (Case B in [`impl-json.md`](../../../skills/uipath-case-management/references/plugins/triggers/timer/impl-json.md)) — the first-trigger path (Case A) is not reachable via CLI today, so the golden fixture doesn't exercise it.
