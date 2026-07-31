# Excel Append Range — Column Schema Mismatch (By-Position Trap)

This scenario reproduces an Append Range failure where the source
`DataTable`'s 4 columns and the target sheet's 4-column header row
have the same NAMES but in different ORDERS. Append Range writes
by position (not by header name), so a numeric column lands in a
text column and Excel COM rejects the cell. The job ends with:

```
System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.
```

## What this scenario uncovers

**Root Cause:** The source DataTable's column order is
`[EmployeeId, HireDate, FullName, Department]` but the target
sheet's existing header is `[FullName, EmployeeId, Department, HireDate]`.
Append Range writes the source's column 0 (numeric `EmployeeId`)
into the target's column A (text `FullName`) — Excel COM rejects
the cell with `0x800A03EC`. The workflow author likely assumed
Append Range would map columns by header name; it doesn't.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/append-range-failures.md`
(the "Column schema mismatch" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelHRProcess` project — `Invoke FetchNewHires.xaml` → `Use Excel File` → `Append Range` with no intermediate column-reorder transformation |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture BOTH column orders side-by-side AND the cell-level COM rejection naming the type mismatch |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (COMException 0x800A03EC
on AppendRange_1, stack through `Range.set_Value`) → `jobs logs`
(the source vs. target column-order Trace + the cell-rejection
explanation are the smoking gun) → workflow source review (confirms
no column-reorder step between the sub-workflow output and the
Append Range) → conclude branch 5.

> **Note on the by-position semantics.** This is the playbook's
> counterintuitive trap: visual presence of column names in both
> ends creates a false expectation of by-name mapping. The test
> grades agents that recognize Append Range's by-position semantics
> as the cause AND recommend an explicit column-reorder step
> (DataTable.DefaultView.ToTable with the target's column-name
> list).

> **Note on fixtures.** Synthetic. The HR sub-workflow, column
> name choices, and exact COMException stack frame are
> placeholders. The test grades whether the agent identifies the
> position-vs-name mapping trap AND recommends a viable structural
> fix (reorder source, restructure target, or migrate to Write
> Range with explicit mapping).
