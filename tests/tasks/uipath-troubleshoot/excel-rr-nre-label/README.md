# Excel Read Range — Sensitivity Label Blocks Robot Access

This scenario reproduces a Read Range failure where the workbook is
protected by a Microsoft Purview / Azure Information Protection
sensitivity label that the Robot user lacks permission for. The job
ends with:

```
System.NullReferenceException: Object reference not set to an instance of an object.
```

(no cell pointer, no sheet name).

## What this scenario uncovers

**Root Cause:** The workbook `C:\Robot\Data\sales-2026-05.xlsx` is
labeled `Confidential\Limited Access`. The interactive workbook
owner has the label permission and can read the file from Explorer.
The Robot user (`UIPATH\AUTOMATION1`) is not in the label's policy,
so when the `Use Excel File` activity opens the file under the
Robot's identity, the label's encryption / policy engine refuses
programmatic access. The activity's parser receives a null where it
expected workbook content and throws `NullReferenceException`.

The user's "Confidential banner at the top" clue + the job-log
Trace entry naming the label together pinpoint branch 1 of the
playbook.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-null-reference.md`
(the "Sensitivity label" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` with absolute literal `WorkbookPath`, then `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entry from `Use Excel File` includes the label name (`Confidential\Limited Access`) |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (bare NRE) → `jobs logs`
(Trace entry surfaces the label name) → workflow source → conclude
branch 1.

> **Note on fixtures.** Synthetic. The label name `Confidential\Limited
> Access` and Robot user are placeholders representative of a real
> Purview deployment. The test grades whether the agent surfaces
> the Purview / AIP branch using the banner clue + the log evidence.
