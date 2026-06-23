# Excel Write Range — Empty Source DataTable

This scenario reproduces a Write Range failure where the source
`DataTable` has 0 rows (a Filter DataTable removed everything) and
`ExcludeHeaders=False`. The job ends with:

```
UiPath.Excel.BusinessException: The Excel Activity option 'Ignore empty source' is ineffective: the source DataTable has 0 rows and 'Exclude headers' is False.
```

## What this scenario uncovers

**Root Cause:** The workflow's Write Range received an initialized
DataTable (`dtOverdue`) with 0 rows because the preceding Filter
DataTable activity removed every row — today's batch of 247 invoices
contained no rows with `Status="Overdue"`. With `ExcludeHeaders=False`
(the default), Write Range treats a 0-row source as a configuration
error rather than a no-op and throws. The "Ignore empty source"
property in the error message is misleading — it only handles
`Nothing` DataTables (playbook branch 1), not initialized 0-row
DataTables.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-range-failures.md`
(the "Empty source + ExcludeHeaders=False" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelInvoiceProcess` project — `Read Range` → `Filter DataTable: Status = Overdue` → `Write Range` with `ExcludeHeaders=False` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture the 247→0 filter drop and the WriteRange resolved-config showing `rows=0 cols=8 ExcludeHeaders=False` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException
referencing "Ignore empty source is ineffective" on WriteRange_1) →
`jobs logs` (the Filter DataTable 247→0 Trace + the WriteRange
`rows=0 cols=8 ExcludeHeaders=False` config Trace are the smoking
gun) → workflow source review (confirms no `If rows.Count > 0`
guard around the Write Range) → conclude branch 3.

> **Note on the anti-pattern trap.** The error message names
> "Exclude headers" as the relevant property, which can mislead
> the agent into recommending `ExcludeHeaders=True` as the fix.
> That's wrong — it would silence the error but produce wrong-shape
> writes (data row in header position). The correct fix is an
> `If dtOverdue.Rows.Count > 0` guard. The test rewards agents
> that recommend the guard and penalizes the ExcludeHeaders silencer.

> **Note on fixtures.** Synthetic. The status breakdown (247 / 189 /
> 58 / 0), filter predicate, and timing values are placeholders.
> The test grades whether the agent correctly diagnoses the 0-row
> case + ExcludeHeaders=False combination AND recommends the
> If-guard fix (not the ExcludeHeaders silencer).
