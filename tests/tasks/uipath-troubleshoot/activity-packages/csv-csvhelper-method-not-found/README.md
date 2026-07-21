# Append To CSV Failure - CsvHelper Version Conflict (Method not found)

This scenario reproduces an `Append To CSV` failure caused by a **CsvHelper
version conflict**. `CsvHelper.dll` is bundled in **both**
`UiPath.System.Activities` (which provides the CSV activities) and
`UiPath.Excel.Activities`. The project pins **mismatched versions** of the two,
so the CSV activity binds an incompatible `CsvHelper` and faults with
`Method not found: 'Void CsvHelper.CsvWriter..ctor(...)'`.

## What this scenario uncovers

**Root Cause:** `project.json` pins `UiPath.System.Activities [23.4.0]` and
`UiPath.Excel.Activities [2.24.4]` — versions that bundle incompatible
`CsvHelper` builds. `Append To CSV` is compiled against one `CsvHelper` API but
binds the other at runtime, raising `MissingMethodException`.

This maps to:
`references/activity-packages/csv-activities/playbooks/csv-helper-method-not-found.md`

The fix is a Studio/project dependency change (align both packages), so the
correct agent behavior is to identify the System↔Excel CsvHelper conflict and
recommend upgrading both — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project that Reads Range (Excel) then Append To CSV, with `project.json` pinning mismatched `UiPath.System.Activities` / `UiPath.Excel.Activities` versions |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `csv-helper-method-not-found.md`
- Agent identified the CsvHelper conflict between `UiPath.System.Activities` and
  `UiPath.Excel.Activities` (mismatched versions bundling incompatible CsvHelper)
  and recommended aligning/upgrading both packages, without fabricating host
  actions
