# Excel Delete Range — Filter Misalignment (Silent Corruption)

This scenario reproduces a Delete Range failure where the activity
itself succeeds but silently deletes hidden rows because of an
active AutoFilter, causing a downstream `Throw` to fire when an
expected customer record is missing from the post-delete data. The
job ends with:

```
System.Exception: Customer CUST-9001 missing from post-delete data
```

The visible runtime fault is the Throw — but that's the symptom.
The root is Delete Range's coordinate-mode behavior against a
filtered sheet.

## What this scenario uncovers

**Root Cause:** The workflow's Delete Range targets
`Customers!A10:D20` with `ShiftCells=True ShiftOption=ShiftCellsUp`,
but the workbook has an active AutoFilter on column `Status` hiding
rows where `Status='Archived'`. `CUST-9001` sits on a hidden row
inside the deletion target. Delete Range operates on cell
coordinates, not visible rows, so `CUST-9001` is silently removed
along with the intentional test-data rows. The downstream
`For Each Row` + `Throw` post-condition check fires because
`CUST-9001` is not in the post-delete DataTable.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/delete-range-failures.md`
(the "Range misalignment over filtered data" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelCustomerProcess` project — `Use Excel File` → `Read Range` → `Delete Range A10:D20 ShiftCells=True` → `Read Range` → `For Each Row` → conditional `Throw` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture the active AutoFilter, the successful Delete Range completion, and the For Each Row "CUST-9001 not encountered" result that triggers the Throw |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (the visible fault is the
Throw — NOT a Delete Range exception) → `jobs logs` (decisive: the
AutoFilter Trace line + Delete Range "completed successfully" Trace
line are the smoking gun) → workflow source review (confirms the
Read → Delete → Read → ForEach → Throw sequence and that Delete
Range targeted a coordinate range, not a content-based selection) →
conclude branch 5.

> **Note on the agent's challenge.** The exception text says
> "Customer CUST-9001 missing." A naive agent might match a customer
> data-quality playbook or blame the source data. The correct
> conclusion requires connecting the AutoFilter state from the logs
> to the silent Delete Range corruption — reasoning backward from
> the Throw through the workflow sequence and the log timeline.

> **Note on fixtures.** Synthetic. The customer ID, sheet name,
> and visible/hidden row counts are placeholders. The test grades
> whether the agent traces the failure back to Delete Range +
> AutoFilter (not just observes the Throw) and recommends a viable
> fix (remove the filter, refactor to DataTable, or delete by key).
