# Excel Append Range — Hidden Rows in Target Append Region (v2.8.5+)

This scenario reproduces an Append Range failure where the target
sheet has an active AutoFilter hiding rows in the computed append
region. Package v2.8.5+ throws an explicit BusinessException to
prevent the silent data loss that pre-2.8.5 versions caused. The
job ends with:

```
UiPath.Excel.BusinessException: Cannot append to a range that contains hidden rows or columns. The target sheet 'Transactions' has hidden rows in the computed append region (rows 4012-4089).
```

## What this scenario uncovers

**Root Cause:** The target sheet `Transactions` has an active
AutoFilter on the `Status` column hiding rows 4012-4089
(`Status='Reconciled'`). The Append Range activity's target-region
validator (v2.8.5+) detected the hidden rows in or near the
computed append target and refused to proceed. The workflow has no
filter-normalization step before the append.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/append-range-failures.md`
(the "Hidden rows in target append region" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelLedgerProcess` project — `Use Excel File` → `Append Range` against a sheet with an active AutoFilter, no filter-normalization step |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture (a) the AutoFilter detection on column 'Status', (b) the v2.8.5+ package-version note, (c) the target-region validation that explicitly identifies the hidden row range, and (d) the BusinessException |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException naming
hidden rows in the append region) → `jobs logs` (AutoFilter
detection + v2.8.5+ guard activation + hidden row range
identification — all on consecutive Trace lines) → workflow source
review (confirms no Remove Data Filter before Append Range) →
conclude branch 6.

> **Note on the anti-pattern trap.** The natural temptation is to
> downgrade the package to pre-2.8.5 to "silence the error." The
> playbook explicitly rejects this — pre-2.8.5 versions silently
> append over hidden rows, causing the data loss the explicit
> error was added to catch. The test penalizes agents that
> recommend a package downgrade and rewards those that recommend
> a filter-normalization step (Remove Data Filter or equivalent).

> **Note on fixtures.** Synthetic. The transactions sub-workflow,
> exact hidden row range, and target-region computation are
> placeholders. The test grades whether the agent identifies the
> AutoFilter + v2.8.5+ guard combination as the root AND
> recommends a viable fix (remove the filter, route to a
> different sheet, or unhide explicitly).
