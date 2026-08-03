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
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project pinning `UiPath.System.Activities 25.10.5`, with a `Write CSV` that sets `Encoding=UTF-8` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the job faults at workflow init with the deserialization error |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

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
