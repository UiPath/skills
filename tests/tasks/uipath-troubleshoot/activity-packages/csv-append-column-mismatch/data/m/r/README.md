# Append To CSV Failure - DataTable Column Structure Mismatch

This scenario reproduces an `Append To CSV` failure caused by a **DataTable
column-structure mismatch**. The workflow builds a 2-column `DataTable`
(`OrderId`, `Customer`) and appends it to `orders.csv`, which has 3 columns
(`OrderId`, `Customer`, `Total`) — so the rows cannot be aligned and the append
faults.

## What this scenario uncovers

**Root Cause:** The input `DataTable` (built via the two `Add Data Column` steps)
has 2 columns; the existing `orders.csv` has 3. `Append To CSV` cannot line the
rows up with the file's columns, so it faults with a column-count mismatch.

This maps to:
`references/activity-packages/csv-activities/playbooks/csv-datatable-structure-mismatch.md`

The discriminator vs the other CSV playbooks: this is a **data-shape** problem,
not a `CsvHelper` `Method not found` and not a file lock. The fix is a
workflow/DataTable change (align columns), so the correct agent behavior is to
recommend matching the DataTable's structure to the file — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project that initializes a `DataTable`, adds only `OrderId` + `Customer` columns, then `Append To CSV` to `data\orders.csv` (3-column file) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `csv-datatable-structure-mismatch.md`
- Agent identified the column count/header mismatch between the input DataTable
  (2 columns) and the existing CSV (3 columns) and recommended aligning the
  DataTable's columns to the file (add the missing column / Build Data Table with
  identical headers), without fabricating host actions
