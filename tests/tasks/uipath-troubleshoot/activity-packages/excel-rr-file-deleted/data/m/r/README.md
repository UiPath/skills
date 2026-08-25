# Excel Read Range — Workbook File Deleted Upstream

This scenario reproduces a Read Range failure where the configured
`WorkbookPath` is a stable absolute literal that has worked for weeks,
but the file has now been deleted or moved by an upstream process. The
job ends with:

```
System.IO.FileNotFoundException: Could not find file 'C:\Robot\Data\sales-2026-05.xlsx'.
```

## What this scenario uncovers

**Root Cause:** The workbook
`C:\Robot\Data\sales-2026-05.xlsx` was deleted from the Robot host
between the prior (successful) run and the current (failed) run. The
configured `WorkbookPath` is an absolute literal that has not changed;
the file simply went missing. The recent-jobs list shows a clear
pattern — multiple successful runs followed by a single failed run on
the same path — that rules out a stable configuration problem and
points directly at branch 1 of the playbook.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-file-not-found.md`
(the "File moved or deleted upstream" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` with absolute literal `WorkbookPath: "C:\Robot\Data\sales-2026-05.xlsx"`, then `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (current, FileNotFoundException)
→ `jobs logs` (last activity log shows the open attempt) → `jobs list`
(broader; surfaces multiple prior **Successful** runs against the same
process / same path) → workflow source review (absolute literal path,
no relative / drive-letter / UNC concerns).

> **Note on fixtures.** Synthetic. The job keys, folder key, and
> workbook path are placeholders — the test grades whether the agent
> surfaces the file-deleted-upstream branch using the prior-success
> pattern as evidence.
