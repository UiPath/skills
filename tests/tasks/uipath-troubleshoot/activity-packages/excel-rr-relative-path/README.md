# Excel Read Range — Relative WorkbookPath Resolved Against Wrong CWD

This scenario reproduces a Read Range failure where the workflow uses
a relative `WorkbookPath` that resolves to the per-package
`%LocalAppData%` directory at unattended runtime, instead of the user's
intended data folder. The job ends with:

```
System.IO.DirectoryNotFoundException: Could not find a part of the path 'C:\Users\automation1\AppData\Local\UiPath\Packages\ExcelDailyImport\1.0.0\Data\sales-2026-05.xlsx'.
```

## What this scenario uncovers

**Root Cause:** The workflow's `WorkbookPath` is the relative literal
`"Data\sales-2026-05.xlsx"`. The .NET runtime resolves relative paths
against `Environment.CurrentDirectory`. Studio's CurrentDirectory is
the project folder (so the workflow "works on my machine"). The
Robot's unattended runtime CWD is
`%LocalAppData%\UiPath\Packages\<process>\<version>\`, which has no
`Data\sales-2026-05.xlsx`. The resolved path's prefix is the smoking
gun.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-file-not-found.md`
(the "Relative path resolved against wrong CWD" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` with **relative** `WorkbookPath: "Data\sales-2026-05.xlsx"`, then `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field echoes the resolved path with the `%LocalAppData%\UiPath\Packages\...` prefix |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (resolved path shows
per-package prefix) → `jobs logs` → workflow source review (relative
literal `WorkbookPath`) → conclude branch 3.

> **Note on fixtures.** Synthetic. The job key, folder key, and
> resolved-path prefix are placeholders representative of a real
> Robot host layout. The test grades whether the agent surfaces the
> CWD divergence using both the workflow-source evidence AND the
> resolved-path prefix.
