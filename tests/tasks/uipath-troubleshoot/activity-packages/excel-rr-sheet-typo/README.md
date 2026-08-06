# Excel Read Range — Sheet Name Typo

This scenario reproduces a Read Range failure where the configured
`SheetName` is a one-character typo of an actual sheet in the
workbook. The job ends with:

```
UiPath.Excel.BusinessException: The sheet with the name 'Datab' does not exist.
```

## What this scenario uncovers

**Root Cause:** Workflow configured `SheetName: "Datab"` on the
`ExcelReadRange` activity. The workbook's actual sheets are
`["Sheet1", "Data", "Summary"]`. The configured name is a typo of
`Data` (extra trailing `b`).

The workflow's `Get Workbook Sheets` activity runs first, succeeds,
and logs the actual sheet titles via `LogMessage`. The agent reads
the job logs, finds the enumerated list, compares against the
configured name, and identifies the typo.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md`
(the "Typo in the configured sheet name" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | minimal `ExcelDailyImport` project — `Use Excel File` → `Get Workbook Sheets` (logs result) → `Read Range "Datab"` (fails) |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (current) → `jobs logs`
(reveals the enumerated sheet list from the prior `Get Workbook
Sheets` activity) → workflow source inspection → conclude typo.

> **Note on fixtures.** Synthetic. Job keys, folder key, workbook
> path are placeholders — the test grades whether the agent surfaces
> the typo branch with the actual-sheets evidence, not the specific
> names.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
