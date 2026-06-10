# Final Resolution

---

**Root Cause:** The target sheet `Transactions` in `ledger.xlsx` has
an active AutoFilter on the `Status` column hiding rows where
`Status='Reconciled'` — specifically rows 4012-4089 are hidden in
the workbook at the time the workflow ran. The `Append Range`
activity computed an append region starting at row 4101 (just after
the last-data row 4100), but the activity's target-region validator
(introduced in `UiPath.Excel.Activities` v2.8.5+) detected that
hidden rows exist in or near the append target and refused to
proceed. Pre-2.8.5 versions would have silently appended over the
hidden region — the explicit error is a deliberate guard against
that silent data loss.

The workbook was likely left in its filtered state by a human user
reviewing reconciled transactions; the workflow assumed the sheet
would be in its "fully visible" state and didn't normalize the
filter before appending.

**What went wrong:** Failing job
`ff333333-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-29T08:00:01.300Z`. The transactions sub-workflow returned
a 78-row, 6-column DataTable. The `Use Excel File: ledger.xlsx`
scope opened the workbook through the OpenXML provider and noted
the package version (2.24.7, ≥ 2.8.5). The Append Range activity
inspected the target sheet and detected the active AutoFilter on
column `Status`. It computed the append region (rows 4101-4178)
and validated the surrounding range for hidden state. The
validator found the hidden block rows 4012-4089 within the
activity's lookback / overlap zone and threw the BusinessException
that explicitly names the hidden range.

**Why:** Append Range's "where to start appending" logic relies on
locating the last row containing data on the target sheet. With
hidden rows in the picture, the computed start-row and the
visually-evident "next empty row" can diverge — and the activity
may compute a target that overlaps hidden cells (especially when
the package's used-range scan inspects rows for content
regardless of visibility). To prevent silent overwrites of hidden
data, v2.8.5+ refuses to append into ANY region that intersects a
hidden row. The fix is to normalize the sheet's visibility state
before the append: remove the filter, or unhide explicitly, or
route to a different sheet.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelLedgerProcess` (key `ff333333-...`) — Faulted
  at `2026-05-29T08:00:03.212Z`.
- Folder: `LedgerOps` (key `f00aaaaa-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: Cannot append to a range that
  contains hidden rows or columns. The target sheet 'Transactions'
  has hidden rows in the computed append region (rows 4012-4089).`
  with stack trace through
  `UiPath.Excel.Activities.Business.AppendRangeX.ValidateTargetRegion(Worksheet, Int32, Int32)`
  and `AppendRangeX.OnExecute(NativeActivityContext)`.
- Faulting activity: `AppendRange_1` (`Append Range: today's transactions`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `Invoke FetchTransactions.xaml` → `dtTransactions`.
  - `Use Excel File: ledger.xlsx` (Modern scope, OpenXML provider).
  - `<uix:ExcelAppendRange SheetName="Transactions" DataTable="[dtTransactions]" AddHeaders="False" />`
  - There is NO `Remove Data Filter` / equivalent step before the
    Append Range — the workflow doesn't normalize the target
    sheet's filter state.

### Package version (decisive)
- `project.json`: `"UiPath.Excel.Activities": "[2.24.7]"` — well
  above the 2.8.5 threshold where the hidden-rows-in-append-target
  guard was introduced. The error is version-correct behavior.

### Job logs (decisive)
- `Use Excel File: ledger.xlsx — workbook opened (OpenXML provider); UiPath.Excel.Activities version 2.24.7 (>= 2.8.5)`
- `Append Range: today's transactions — target sheet 'Transactions' inspection: AutoFilter active on column 'Status' (hiding rows where Status='Reconciled')`
- `Append Range: today's transactions — last data row on sheet 'Transactions': row 4100. Computed append region: rows 4101-4178 (78 rows for the dtTransactions payload).`
- `Append Range: today's transactions — target region validation (v2.8.5+): hidden rows detected in append target — sheet rows 4012-4089 are hidden by the AutoFilter and overlap with the computed append region's lookback. Pre-2.8.5 versions would have silently appended over the hidden region; v2.8.5+ throws to prevent data loss.`
- `Append Range: today's transactions — UiPath.Excel.BusinessException: Cannot append to a range that contains hidden rows or columns.`

The AutoFilter detection log + the v2.8.5+ guard log + the explicit
BusinessException naming the hidden row range together pin the
failure to branch 6.

### Cross-check — what this is NOT
- Not branch 1 (activity variant mismatch): the activity is
  correctly nested inside `Use Excel File`.
- Not branch 2 (sheet name mismatch / extension): the target
  sheet `Transactions` was located and inspected successfully.
- Not branch 3 (workbook locked / read-only): the workbook
  opened cleanly per the logs.
- Not branch 4 (uninitialized DataTable): `dtTransactions` is
  populated (78 rows, 6 columns).
- Not branch 5 (column schema mismatch): the failure surfaces in
  target-region validation, BEFORE column-by-column write
  validation. The exception is a BusinessException about hidden
  rows, not a COMException from `Range.set_Value`.

---

**Recommended Fix (Resolution):**

### Primary fix — remove the filter before Append Range

The cleanest fix: normalize the target sheet's visibility state
immediately before the append. Insert a `Remove Data Filter`
(Modern) or `Filter Range` with `Action: Remove` (Classic) activity
inside the `Use Excel File` scope, before the Append Range.

1. Open `Main.xaml`.
2. Inside the `Use Excel File` body, immediately before
   `AppendRange_1`, add a `Remove Data Filter` activity targeting
   `SheetName="Transactions"`.
3. (Optional) After the append, re-apply the filter if downstream
   consumers depend on it.
4. Save and re-run.

With the filter removed before the append, no rows are hidden, the
v2.8.5+ validator passes, and the activity proceeds.

### Alternative — unhide the rows explicitly

If the workflow's contract is to not touch the filter (e.g., the
filter state is meaningful for human reviewers), unhide ONLY the
rows in the computed append region's lookback window before the
append. This requires reading the activity's computed start-row
in advance — more complex than removing the filter, but preserves
the filter state.

### Alternative — route to a different sheet

If the target sheet's filter state must remain untouched AND the
data being appended is structurally separable from the filtered
data, route the append to a new or different sheet whose layout
the workflow controls. A downstream consolidation step (separate
workflow) merges the two sheets later. This is the safest pattern
when humans and robots both edit the same workbook.

### Anti-pattern (do NOT use)

Do NOT downgrade `UiPath.Excel.Activities` to a pre-2.8.5 version
to silence the error. The explicit guard was added BECAUSE
pre-2.8.5 versions silently appended over the hidden region,
producing exactly the silent-data-loss bug the explicit error was
designed to catch. Workflow authors only discovered the bug weeks
later when human users unhid rows and found their archived data
overwritten by robot appends. Downgrading reintroduces that bug —
the cost of the explicit error is far smaller than the cost of
silent data loss.

### Prevention

- For workflows on workbooks that humans also edit: ALWAYS insert
  a `Remove Data Filter` (or equivalent) immediately before any
  range-mutation activity (Append Range, Write Range, Delete
  Range). AutoFilter state is invisible to workflow authors at
  design time but very visible to v2.8.5+ activities at runtime.
- Document the workflow's expected sheet state in the activity
  comments: "this workflow assumes no active AutoFilter on the
  Transactions sheet" — pair the comment with the actual
  enforcement step (Remove Data Filter).
- Schedule the human-edited workbook for a clean state (e.g., the
  human reviewer clears filters before EOB; the robot runs
  overnight) — but don't rely on this alone; enforcement at the
  workflow level is more reliable than process discipline.
- For high-frequency appends to a shared workbook, consider
  routing each robot run's data to its own daily sheet, then
  consolidating in a periodic batch. The append surface remains
  filter-state-immune because each daily sheet is robot-only.
