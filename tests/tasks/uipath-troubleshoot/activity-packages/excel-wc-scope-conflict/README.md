# Excel Write Cell — Classic/Modern Scope Conflict

This scenario reproduces a Write Cell failure with the canonical
"file in use by another process" `IOException` — the same wording
as the Read Range file-locked playbook — but here the locker is
NOT external. The workflow's own surrounding Modern `Use Excel File`
scope holds the file while a nested Classic Workbook `Write Cell`
activity tries to write to the same file. The job ends with:

```
System.IO.IOException: The process cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by another process.
```

## What this scenario uncovers

**Root Cause:** The workflow contains a Modern `Use Excel File`
scope on `C:\Robot\Data\sales-2026-05.xlsx`, and INSIDE its body
a Classic Workbook `Write Cell` activity with its own
`WorkbookPath` property pointing at the same file. The Classic
Workbook surface accesses the file's raw bytes directly and
refuses to write while another process — including UiPath's own
Modern scope — has the file open.

The error wording is identical to an external-locker failure
(orphan `EXCEL.EXE`, user editing, network share, etc.) but the
user has explicitly ruled those out. The workflow source is what
makes the diagnosis: two scopes / surfaces on the same file
inside the same job.

This maps to the **scope-conflict variant of branch 1** in:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-cell-failures.md`

The agent must distinguish this from the **external-locker variant**
covered by `workbook-file-locked.md`. The decisive signal is the
workflow source — both scopes visible in `Main.xaml` — combined
with the user's explicit exclusion of external lockers.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelWriteCellProcess` project — `Use Excel File` scope opens `sales-2026-05.xlsx`; inside the scope's body, a Classic Workbook `Write Cell` targets the same file |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field is the IOException; `or jobs logs` shows the scope opening succeeded, then the Classic Workbook Write Cell faulted |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (IOException) →
`jobs logs` (Modern scope opened the file successfully; Classic
Workbook activity faulted next) → **workflow source review** (the
dual-scope pattern is the smoking gun) → conclude branch 1
scope-conflict variant.

> **Note on fixtures.** Synthetic. The workbook path and job key
> are placeholders. The test grades whether the agent reads the
> workflow source, spots the dual-scope pattern, and recommends
> either nesting Modern Write Cell or unnesting the Classic
> activity — rather than reflexively pivoting to the read-range
> file-locked investigation chain (orphan check, network share,
> AV scanner) which the user has explicitly ruled out.
