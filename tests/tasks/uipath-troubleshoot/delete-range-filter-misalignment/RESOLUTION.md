# Final Resolution

---

**Root Cause:** The workflow's `Delete Range` activity targeted
`Customers!A10:D20` with `ShiftCells=True ShiftOption=ShiftCellsUp`,
but the workbook had an active `AutoFilter` on column `Status`
hiding rows where `Status='Archived'`. Delete Range operates on cell
coordinates, not visible rows. The customer record `CUST-9001` sat
on a row inside `A10:D20` that was hidden by the filter — invisible
to the workflow author looking at the filtered view, but in scope
of the deletion. When the activity ran, `CUST-9001` was silently
removed along with the intentional test-data rows. The downstream
`Throw_1` activity fired because the post-delete `For Each Row`
scan could not find `CUST-9001` in `dtPostDelete`.

The visible runtime exception is the Throw — but the Throw is a
SYMPTOM, not the root. The root is Delete Range's coordinate-mode
behavior against a filtered sheet.

**What went wrong:** Failing job
`dd333333-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-23T08:00:01.300Z`. The `Use Excel File` scope opened the
workbook cleanly and immediately logged the active AutoFilter on
column `Status`. The pre-delete `Read Range` returned 47 rows total
with 22 visible + 25 hidden (rows 15-22 explicitly noted). The
`Delete Range` activity completed without an exception — Excel
accepted the shift, 44 cells across 11 rows were removed. The
post-delete `Read Range` returned 36 rows (11 fewer, as expected
by coordinate count). The `For Each Row` scan iterated all 36
rows looking for `CUST-9001` and never found it — `CUST-9001` had
been on row 17 of the original sheet, inside the deletion target,
hidden by the filter, and silently removed by ShiftCellsUp. The
final `Throw_1` activity fired because the boolean `found` was
still False at end-of-loop.

**Why:** Excel's `Range.Delete` operates on the physical row
coordinates, not the filtered display. The OpenXML provider's
read returns all rows (hidden + visible); the Modern `DeleteRangeX`
activity passes the coordinate range to Excel COM (or its OpenXML
equivalent) which deletes physical cells. The filter's row
visibility is a display-layer attribute that doesn't propagate to
range mutations. A workflow author looking at the workbook
interactively sees only filtered rows ("the test data is rows
10-14 and 19-20") and configures the deletion based on visible
geometry — but the activity operates on the underlying coordinate
geometry that includes the hidden rows in between.

This kind of mismatch is silent at the Delete Range layer: no
exception, no warning, no log entry hinting that hidden rows were
affected. Detection requires either: (1) a downstream
post-condition check (as this workflow has via Read → ForEach →
Throw), (2) a content-based row identifier compared against the
pre/post state, or (3) explicit filter-state inspection before
mutation.

---

**Evidence:**

### Orchestrator (Root cause — but only the symptom)
- Failing job: `ExcelCustomerProcess` (key `dd333333-...`) — Faulted
  at `2026-05-23T08:00:02.812Z`.
- Folder: `CustomerOps` (key `f0044444-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Exception: Customer CUST-9001 missing from post-delete data`
  with stack trace through
  `System.Activities.Statements.Throw.Execute(...)`.
- Faulting activity: `Throw_1` (`Throw: missing customer`) at
  `Main.xaml`. **This is the visible fault but not the originating
  fault.**

### Workflow source (decisive — the sequence that links symptom to root)
- `Main.xaml` `UseExcelFile` body:
  - `ExcelReadRange "Customers!A1:Z100" → dtPreDelete`
  - `ExcelDeleteRange "Customers!A10:D20" ShiftCells=True ShiftOption=ShiftCellsUp`
  - `ExcelReadRange "Customers!A1:Z100" → dtPostDelete`
  - `ForEachRow row in dtPostDelete → If row("CustomerId")="CUST-9001" Then found=True`
  - `If Not found Then Throw_1 "Customer CUST-9001 missing from post-delete data"`
- The Throw is a post-condition check the workflow author placed
  to detect exactly this silent-corruption pattern. It fires when
  the expected post-state doesn't hold.

### Job logs (decisive — filter state + Delete Range completion)
- `Use Excel File: customer-list.xlsx — workbook has active AutoFilter on sheet 'Customers' column 'Status' (hiding rows where Status='Archived')`
- `Read Range: pre-delete snapshot (Customers!A1:Z100) — returned 47 rows (filtered view: 22 visible, 25 hidden including rows 15-22)`
- `Delete Range: drop legacy customers (Customers!A10:D20 ShiftCells=True ShiftOption=ShiftCellsUp) — completed successfully (44 cells deleted across 11 rows, 0 errors)`
- `Read Range: post-delete snapshot (Customers!A1:Z100) — returned 36 rows`
- `For Each Row: scan for CUST-9001 — 36 iterations, CUST-9001 not encountered (found=False)`
- `Throw: missing customer — System.Exception: Customer CUST-9001 missing from post-delete data`

The AutoFilter Trace line plus the Delete Range "completed
successfully" line are the smoking gun. The activity that
appears in the exception (Throw_1) is not the activity that
caused the failure — Delete Range is. The agent must trace
backward through the log chain.

### Cross-check — what this is NOT
- Not branch 1 (activity outside a scope container): the
  `Use Excel File` scope is present and wraps Delete Range.
- Not branch 2 (invalid range syntax): `A10:D20` is a
  well-formed literal A1 rectangular range; no ArgumentException.
- Not branch 3 (ShiftCells / ShiftOption conflict): no
  COMException, no `0x800A03EC`. Excel accepted the shift; the
  deletion ran cleanly at the COM layer.
- Not branch 4 (workbook locked / read-only): no `IOException`,
  no "cannot access the file"; the workbook opened and the
  read/write cycle completed.

The decisive distinction from these other branches: there is no
Delete-Range-side exception in this scenario. The activity ran to
completion. The fault is silent-data-corruption surfaced by a
downstream post-condition check.

---

**Recommended Fix (Resolution):**

### Primary fix — remove the filter before Delete Range

Insert a `Remove Data Filter` activity (Modern) or `Filter Range`
with `Action: Remove` (Classic) before `DeleteRange_1`:

1. Open `Main.xaml`.
2. Inside the `Use Excel File` body, after the pre-delete
   `Read Range` and before the `Delete Range`, add:
   `Remove Data Filter` activity targeting `SheetName="Customers"`.
3. (Optional) After the workflow's final read, re-apply the filter
   if downstream consumers depend on it: `Filter Range` with the
   original column / criterion.
4. Save and re-run.

With the filter removed, Delete Range still operates on
coordinates — but the workflow author's mental model now matches
the activity's behavior because no rows are hidden.

### Alternative — refactor to DataTable operations

Avoid in-place Delete Range entirely. Read the data into memory,
filter / mutate the DataTable, then Write Range the result. This
eliminates the entire filter-state surface:

1. Replace `Delete Range` with: an `Assign` that uses
   `dtPreDelete.Select(...)` or LINQ to remove the legacy test
   customer rows by key (e.g., `CustomerId LIKE 'TEST-%'`).
2. After the mutation, use `Write Range` (with `Auto Save: True`
   on the scope) to overwrite the workbook with the new
   DataTable.
3. The intermediate `Read Range` post-delete and the verification
   loop become unnecessary — operate on the DataTable directly
   and assert against it before the Write.

### Alternative — delete by key, not by coordinate

Identify rows to delete by a content-based identifier (CustomerId,
status, age) rather than by row coordinate. Loop the DataTable
in memory, mark rows for deletion, then either:
- Use `Delete Row` against the workbook for each marked
  CustomerId (slower but correct).
- OR rebuild the DataTable without marked rows and Write Range
  the cleaned result (faster).

### Prevention

- Workflows that mutate filtered workbooks must explicitly manage
  filter state. Treat an active filter as a hidden config that
  changes the semantics of every coordinate-based mutation.
- Prefer DataTable-in-memory mutations followed by Write Range
  over in-place Delete Range when the source workbook has any
  filtering, hidden rows, or grouped rows.
- When in-place Delete Range is unavoidable: insert a `Remove Data
  Filter` immediately before, and assert on a content-based
  post-condition immediately after (the existing `Throw_1` pattern
  is correct — it caught this bug, just at the wrong layer of the
  workflow's understanding).
- Document the workbook's expected layout in the workflow comments:
  "this workflow assumes no active filter on the Customers sheet";
  pair with the `Remove Data Filter` activity as enforcement, not
  just documentation.
