# Final Resolution

---

**Root Cause:** The workflow's `Write Range` activity received an
initialized `DataTable` (`dtOverdue`) with **0 rows** because the
preceding `Filter Data Table` step removed every row — today's batch
of 247 invoices contained no rows with `Status="Overdue"`. With
`Write Range`'s `ExcludeHeaders` property set to `False` (the
default), the activity treats a 0-row source as a configuration
error rather than a no-op and throws `UiPath.Excel.BusinessException:
The Excel Activity option 'Ignore empty source' is ineffective: the
source DataTable has 0 rows and 'Exclude headers' is False.` The
"Ignore empty source" property name in the error message is
misleading — that option only handles a `Nothing` DataTable (branch 1
of the playbook), not an initialized 0-row DataTable.

**What went wrong:** Failing job
`ee222222-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-25T08:00:01.300Z`. The source-side `Use Excel File` opened
`invoices-source.xlsx` and the `Read Range` returned 247 rows
(Status breakdown: Paid=189, Pending=58, Overdue=0 — already a
data signal, but the workflow author didn't surface this anywhere
the agent could see at runtime). The `Filter Data Table` activity
with predicate `Status = "Overdue"` produced 0 output rows from
247 input rows. The export-side `Use Excel File` opened
`invoice-report.xlsx` cleanly. The `Write Range: overdue report`
activity resolved its configuration (Sheet='Overdue',
StartingCell='A1', ExcludeHeaders=False, DataTable='dtOverdue'
with rows=0 cols=8), validated the source, and threw the
BusinessException.

**Why:** Write Range's source-table validation rejects an
initialized 0-row DataTable when `ExcludeHeaders=False` because
the activity is asked to write "the header row plus zero data rows"
— a degenerate case that the activity surface treats as a workflow
contract violation. The activity rejects rather than no-ops because
silent acceptance would mask the more common bug: a workflow that
expected data but produced none. The misleadingly named "Ignore
empty source" property handles ONLY the case where the variable
itself is `Nothing` (branch 1) — it has no effect on an
initialized-but-empty DataTable. This naming ambiguity is the
playbook's anti-pattern #3: setting `ExcludeHeaders=True` "to
silence the error" produces wrong-shape writes if the workflow
intends a header row.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelInvoiceProcess` (key `ee222222-...`) — Faulted
  at `2026-05-25T08:00:02.812Z`.
- Folder: `InvoiceOps` (key `f0066666-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The Excel Activity option
  'Ignore empty source' is ineffective: the source DataTable has 0
  rows and 'Exclude headers' is False.` with stack trace through
  `UiPath.Excel.Activities.Business.WriteRangeX.ValidateSourceTable(DataTable)`
  and `WriteRangeX.OnExecute(NativeActivityContext)`.
- Faulting activity: `WriteRange_1` (`Write Range: overdue report`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `Read Range: load invoices` → `dtInvoices` (source rows)
  - `Filter Data Table: Status = Overdue` → `dtOverdue` (filtered
    result, can be empty)
  - `Use Excel File: invoice-report.xlsx` (export scope, opens
    cleanly)
  - `<uix:ExcelWriteRange DataTable="[dtOverdue]" ExcludeHeaders="False" StartingCell="A1" SheetName="Overdue" ... />`
- `ExcludeHeaders="False"` is the default; the workflow author did
  not override it.
- There is no `If dtOverdue.Rows.Count > 0` guard around the Write
  Range — the activity runs unconditionally.

### Job logs (decisive)
- `Read Range: load invoices (Invoices!A1:Z10000) — returned 247 rows (Status values: Paid=189, Pending=58, Overdue=0)`
- `Filter Data Table: Status = Overdue — input 247 rows, output 0 rows (no matches)`
- `Write Range: overdue report — resolved config Sheet='Overdue' StartingCell='A1' ExcludeHeaders=False DataTable='dtOverdue' (rows=0 cols=8)`
- `Write Range: overdue report — UiPath.Excel.BusinessException: The Excel Activity option 'Ignore empty source' is ineffective: the source DataTable has 0 rows and 'Exclude headers' is False.`

The `rows=0 cols=8` Trace line + the explicit `ExcludeHeaders=False`
in the resolved config + the BusinessException's literal wording
together pin the failure to branch 3 unambiguously. The DataTable
is initialized (cols=8 ≠ 0) so it's NOT branch 1's `Nothing` case;
it's the 0-row case the "Ignore empty source" property does NOT
handle.

### Cross-check — what this is NOT
- Not branch 1 (uninitialized DataTable): `cols=8` proves the
  DataTable is initialized; the variable is not `Nothing`. The
  exception class is `BusinessException`, not `NullReferenceException`.
- Not branch 2 (workbook locked / read-only): both the source and
  export workbooks opened cleanly per the logs; no `IOException`,
  no "cannot access the file" COMException.
- Not branch 4 (hidden rows / columns): the BusinessException
  message references "empty source" and "Exclude headers", not
  "hidden rows" or "hidden columns". The activity validation
  rejected the source before any target-range inspection.
- Not branch 5 (out-of-memory / COMException): 0 rows is not a
  volume case, and the data has no formula-prefix characters
  because the data doesn't exist. The exception class is
  `BusinessException`, not `OutOfMemoryException` or `COMException`.

---

**Recommended Fix (Resolution):**

### Primary fix — guard the Write Range with an If on row count

The cleanest fix: wrap the Write Range in an `If` activity with
condition `dtOverdue.Rows.Count > 0`. In the Then-branch, perform
the write. In the Else-branch, log a message that today's batch
had no overdue invoices (or no-op).

1. Open `Main.xaml`.
2. Wrap `WriteRange_1` in an `If` activity.
3. Set the condition to `dtOverdue.Rows.Count > 0`.
4. In the Else-branch, add a `Log Message Level=Info` saying
   "No overdue invoices today — skipping report write."
5. Save and re-run.

This explicitly encodes the "nothing to write" semantics. Future
runs with 0 overdue invoices are no-ops instead of failures, and
the log message makes the empty-batch case observable in job logs.

### Alternative — keep the write but make it explicit

If the report SHOULD be written even when empty (so consumers can
see "today's report ran but was empty" rather than "no report
exists today"), set `ExcludeHeaders=True` AND restructure so the
header is written separately or pre-populated:

1. Pre-populate the report workbook with the header row at design
   time, OR write the header row in a separate Write Range
   activity inside an `If dtOverdue.Rows.Count = 0` Then-branch.
2. Set `ExcludeHeaders=True` on the data-row write.
3. With ExcludeHeaders=True, a 0-row write is a no-op.

This is more complex than the primary fix. Use it only if the
"empty report exists" semantics are load-bearing for downstream
consumers.

### Alternative — restructure the workflow to handle the empty case at source

If today's empty result was unexpected (the upstream invoices file
should always contain Overdue entries by the time this workflow
runs), the right fix is upstream: investigate why no invoices
have `Status="Overdue"` in the source workbook. This is a data /
schedule issue, not a Write Range bug.

### Anti-pattern (do NOT use)

Do NOT "fix" this by setting `ExcludeHeaders=True` without
restructuring the rest of the workflow. With `ExcludeHeaders=True`,
the data rows land at the same column positions as the header
would have — overwriting any existing header in the report
workbook. The Write Range succeeds, but the report's first data
row sits in the header position; downstream consumers reading the
report (or humans opening it) see misaligned data. This is the
playbook's anti-pattern #3 — silencing the error without fixing
the underlying intent.

### Prevention

- Guard every Write Range that operates on filtered / queried /
  scraped data with an `If rows.Count > 0` check. The "what if the
  result is empty?" question should be explicit in every workflow,
  not delegated to the activity.
- Log `DataTable.Rows.Count` and `DataTable.Columns.Count`
  immediately before every Write Range. The two-line log makes
  branches 1 and 3 self-diagnosing.
- Don't rely on the "Ignore empty source" property to handle
  empty cases — it only handles the `Nothing` variable case
  (branch 1), not the initialized 0-row case (branch 3). The
  property name is misleading; treat it as "ignore null source"
  if it helps remember the actual semantics.
- For workflows that filter or query upstream data, log the input
  vs. output row counts of the filter / query step. A 247→0 drop
  is meaningful signal — surfacing it in logs makes empty-result
  diagnostics one-step instead of multi-step.
- For workflows where the empty case is a known operational state
  (e.g., "no overdue invoices today is a good day, not an error"),
  document this explicitly in the workflow comments AND handle it
  with an explicit If-guard. Both are needed: the comment
  communicates intent, the guard enforces it.
