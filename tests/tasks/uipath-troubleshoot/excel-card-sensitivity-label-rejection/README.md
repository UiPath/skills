# Use Excel File — Microsoft Purview Sensitivity Label Rejection

This scenario reproduces a Modern `Use Excel File` card failure
where the target workbook has a Microsoft Purview sensitivity label
applied (`Confidential - Client Data`) but the card's
`SensitivityLabel` / `SensitivityOperation` properties (available
in `UiPath.Excel.Activities` v2.23.4+) are not configured. The card
detects the label, validates against the unset properties, and
refuses the write. The job ends with:

```
UiPath.Excel.BusinessException: The workbook is protected by a Microsoft Purview sensitivity label ('Confidential - Client Data') that requires explicit handling. The SensitivityLabel and SensitivityOperation properties on the Use Excel File activity are not configured.
```

## What this scenario uncovers

**Root Cause:** The workbook has a Microsoft Purview label applied
(`Confidential - Client Data`, label ID
`8c2f3a4d-1234-5678-abcd-aip00client01`). Package version 2.24.7
supports the SensitivityLabel / SensitivityOperation card properties
(introduced in v2.23.4), but the workflow doesn't configure either.
Under v2.23.4+ semantics, write operations against labeled workbooks
require explicit acknowledgement (Keep / Apply / Remove). The card
throws BEFORE the inner Write Range runs.

The canonical fix is `SensitivityLabel="Confidential - Client Data"`
+ `SensitivityOperation=Keep` on the card (preserves the existing
label while writing data).

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-card-failures.md`
(the "Sensitivity label rejection" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelClientReportProcess` project — `<uix:UseExcelFile>` with no `SensitivityLabel` / `SensitivityOperation` properties, wrapping a `<uix:ExcelWriteRange>` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture (a) the package version (≥2.23.4: properties available), (b) the workbook's Purview label detection naming the label ID, (c) the card-property inspection showing both label props `<unset>`, and (d) the BusinessException |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException naming
the Purview label) → `jobs logs` (the four-line chain pinning
package version + label detection + unset card props + exception)
→ workflow source review (confirms no label properties on the
card) → conclude branch 5.

> **Note on the anti-pattern trap.** The natural temptation is to
> downgrade `UiPath.Excel.Activities` to a pre-v2.23.4 version to
> silence the error. The playbook explicitly rejects this —
> pre-v2.23.4 packages handle labeled workbooks INCORRECTLY
> (silent label-stripping = compliance violation). The test
> penalizes the package-downgrade recommendation and rewards
> the configure-the-properties fix.

> **Note on fixtures.** Synthetic. The label name, label ID, and
> Purview-detection log format are placeholders. The test grades
> whether the agent identifies the label-on-workbook +
> unset-properties combination as the root cause AND recommends
> the SensitivityLabel + SensitivityOperation configuration fix
> (NOT package downgrade, NOT bare Try-Catch).
