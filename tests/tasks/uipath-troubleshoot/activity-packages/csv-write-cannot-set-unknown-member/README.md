# Write CSV Failure - "Cannot set unknown member" (Package Version Skew)

This scenario reproduces a `Write CSV` failure caused by **activity-package
version skew** between the build machine and the runtime robot. The project
targets `UiPath.System.Activities 25.10.5` and sets the Write CSV `Encoding`
property, but the robot runs an **older** version whose `WriteCsvFile` has no
`Encoding` member — so the workflow fails to initialize with `Cannot set unknown
member 'UiPath.Core.Activities.WriteCsvFile.Encoding'`.

## What this scenario uncovers

**Root Cause:** The runtime robot's `UiPath.System.Activities` is older than the
version the workflow was built with, so a property present in the build-time
activity is "unknown" to the runtime activity during XAML deserialization.

This maps to:
`references/activity-packages/csv-activities/playbooks/write-csv-cannot-set-unknown-member.md`

"Works in Studio, fails on the robot" is the signature. The fix is to align the
runtime's package versions with `project.json` (or rebuild against the runtime's
versions) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project pinning `UiPath.System.Activities 25.10.5`, with a `Write CSV` that sets `Encoding=UTF-8` |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the build-vs-runtime
  activity-package version skew (a property unknown to the robot's older
  activity) and recommends aligning the robot's package versions with
  `project.json` (or rebuilding against the runtime versions), without
  fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
