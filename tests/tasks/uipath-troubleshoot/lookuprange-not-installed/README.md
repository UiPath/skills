# Lookup Range Failure - Excel Not Installed on the Robot Host

This scenario reproduces a classic `Lookup Range` failure caused by
**Microsoft Excel not being installed** on the execution machine. The
classic activity drives the Excel Interop API, so the surrounding
`Excel Application Scope` cannot create the `Excel.Application` COM
object and faults at startup with `REGDB_E_CLASSNOTREG` (0x80040154).

## What this scenario uncovers

**Root Cause:** The classic `Lookup Range` (`UiPath.Excel.Activities.LookUpRange`)
inside an `Excel Application Scope` needs a registered desktop Excel
install. The new unattended robot host has no Excel, so the COM class
factory for `Excel.Application` cannot be created and the scope faults
before any cell is read. The "worked on dev, broke after the move to the
new robot" detail points at a host-environment cause, not a workflow
defect.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md`

The user is framed as **off-host**, so the correct agent behavior is to
tie the HRESULT to a missing Excel install and recommend either
installing Excel or migrating to the Excel-free Workbook path - not to
attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a classic `Excel Application Scope` + `Lookup Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-excel-not-installed.md`
- Agent identified "Excel not installed on the robot host" as the cause
  and recommended either installing Excel or migrating to Workbook
  Read Range + Lookup Data Table (either fix path scores full marks)
