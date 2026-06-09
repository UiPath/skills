# Excel Read Range — File Locked by Concurrent Robot Jobs

This scenario reproduces an `ExcelReadRange` failure caused by **two
Orchestrator jobs racing against the same workbook on the same host**.
The job ends with:

```
System.IO.IOException: The process cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by another process.
```

## What this scenario uncovers

**Root Cause:** Job `ExcelDailyImport` (key `aa111111-...`) and a sibling
job (key `bb222222-...`) ran the same process against the same workbook
on overlapping schedules. The first job to start acquired the file lock
on `sales-2026-05.xlsx`; the second job's Read Range hit `IOException`
because the OS refused the concurrent open. Two triggers (`HourlySalesA`
and `HourlySalesB`) fire the same process every 30 minutes, offset by
0 minutes — their Running windows always overlap.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-file-locked.md`
(the "Concurrent Robot jobs racing on the same workbook" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | minimal `ExcelDailyImport` project — `Use Excel File` → `Read Range` on `sales-2026-05.xlsx` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The fixture set models the agent's expected investigation chain:
`folders list-current-user` → `jobs list --state Faulted` → `jobs get`
→ `jobs logs` → `jobs list` (broader, shows the sibling job) → `jobs
get <sibling-key>` → `triggers list` (shows overlap). The sibling job
key, its Running window, and the two-trigger overlap pattern together
identify the concurrent-jobs branch.

> **Note on fixtures.** Fixtures are synthetic, authored from the
> documented playbook signature rather than captured from a real
> `.investigation/` session. The job keys, folder key, workbook path,
> and trigger names are placeholders — the test grades whether the
> agent surfaces the concurrent-jobs branch with evidence (sibling job
> key + trigger overlap), not the specific names.
