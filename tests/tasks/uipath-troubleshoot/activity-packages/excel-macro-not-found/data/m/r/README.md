# Excel Execute Macro — Macro Name Not Found

This scenario reproduces an Execute Macro failure where the configured
`MacroName` does not exist in the workbook's VBA project. The job
ends with:

```
System.Runtime.InteropServices.COMException: Cannot run the macro 'RunImport'. The macro may not be available in this workbook or all macros may be disabled.
```

## What this scenario uncovers

**Root Cause:** The workflow's Execute Macro activity is configured
with `MacroName: "RunImport"`. The workbook's VBA project contains
macros `Module1.ProcessData` and `Module2.UpdateReport` — NOT
`RunImport`. The error string is the canonical Excel-COM "macro not
in workbook OR macros disabled" message; the distinguishing evidence
is the activity's VBA-module enumeration in the logs, which shows the
absence of `RunImport`.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/execute-macro-failures.md`
(the "Macro name not found in the workbook" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelMacroProcess` project — `Use Excel File` → `Execute Macro` with `MacroName: "RunImport"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entry from `Execute Macro` enumerates the workbook's VBA modules ("VBA modules: ['Module1.ProcessData', 'Module2.UpdateReport']") |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (canonical "Cannot run the
macro" COMException) → `jobs logs` (VBA-module enumeration is the
smoking gun) → workflow source review (confirms configured
`MacroName: "RunImport"`) → conclude branch 1.

> **Note on fixtures.** Synthetic. The macro names and module
> names are placeholders. The test grades whether the agent
> distinguishes branch 1 (macro absent) from branch 5 (macro
> present but Trust Center disabled) — the absence-from-enumeration
> evidence is decisive.
