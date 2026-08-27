# Final Resolution

---

**Root Cause:** The workflow's `Delete Range` activity is configured
with `Range` as an expression `"A1:B" + lastRow.ToString()`. At runtime
on this empty (header-only) workbook the preceding `Read Range`
returned 0 rows, so `lastRow = dtCleanup.Rows.Count = 0`. The expression
evaluated to `"A1:B0"` — an invalid A1 address because row 0 does not
exist. The Modern `DeleteRangeX` activity's range validator rejected
the string with `System.ArgumentException: The range is invalid`
before any Excel COM / OpenXML call was made.

**What went wrong:** Failing job
`dd111111-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-21T08:00:01.300Z`. The `Use Excel File` scope opened the
workbook (no IOException, no FileNotFoundException). `Read Range`
on `Sales!A1:Z1000` returned 0 rows (the workbook had only a
header row). The Assign computed `lastRow = 0`. The next activity,
`Delete Range: clear stale block`, resolved its `Range` property
expression to `"A1:B0"` and immediately threw the
`ArgumentException` — the validator detected the zero-row part
of the address.

**Why:** A1 notation requires both column letters and a row number
≥ 1. Row index 0 is not a legal address in Excel; `B0` parses as
neither a cell reference nor a full-column reference. The Modern
Delete Range activity validates its `Range` property against the
A1 grammar before dispatching to the provider, so the failure
surfaces as a managed `ArgumentException` rather than a COM
exception. The same expression with `lastRow >= 1` would have
produced a syntactically valid range (`"A1:B1"`, `"A1:B7"`, etc.)
and the activity would have proceeded normally.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelCleanupProcess` (key `dd111111-...`) — Faulted
  at `2026-05-21T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0022222-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.ArgumentException: The range is invalid` with stack
  trace through
  `UiPath.Excel.Activities.Business.DeleteRangeX.ValidateRange(String range)`
  and `DeleteRangeX.OnExecute(NativeActivityContext context)`.
- Faulting activity: `DeleteRange_1` (`Delete Range: clear stale block`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  `<uix:ExcelDeleteRange Range="[&quot;A1:B&quot; + lastRow.ToString()]" ... />`
  — `Range` is an expression depending on the `lastRow` variable,
  which is set earlier by `Assign: lastRow = dtCleanup.Rows.Count`.
- Preceding sequence:
  `ExcelReadRange (Sales!A1:Z1000) → dtCleanup`,
  `Assign lastRow = dtCleanup.Rows.Count`,
  `ExcelDeleteRange (Range = "A1:B" + lastRow.ToString())`.

### Job logs (decisive)
- `Read Range: scan used data (Sales!A1:Z1000) — returned 0 rows (header-only workbook)`
- `Assign: lastRow = dtCleanup.Rows.Count → 0`
- `Delete Range: clear stale block — resolved Range expression "A1:B" + lastRow.ToString() to "A1:B0"`
- `Delete Range: clear stale block — System.ArgumentException: The range is invalid`

The resolved-Range Trace line is the smoking gun: the configured
expression evaluated to the literal string `"A1:B0"`, and that string
fails A1 validation because row 0 is not a valid row index.

### Cross-check — what this is NOT
- Not branch 1 (activity outside a scope container): the
  `Use Excel File` scope is present and wraps the Delete Range
  activity in `Main.xaml`. If the scope were missing, the failure
  would be a `BusinessException` referencing the missing scope
  rather than an `ArgumentException` on the range string.
- Not branch 3 (ShiftCells / ShiftOption conflict): `ShiftCells` is
  False. No shift was attempted; the activity threw before any
  cell operation.
- Not branch 4 (workbook locked / read-only): no `IOException`,
  no `COMException` referencing file access, the workbook opened
  cleanly per the logs.
- Not branch 5 (filter misalignment): the workbook had no active
  AutoFilter (and even if it had, branch 5 produces silent
  corruption — not an ArgumentException).

---

**Recommended Fix (Resolution):**

### Primary fix — guard the expression

The expression has a defined failure mode when `lastRow = 0`. Add an
`If` activity before Delete Range that skips the activity when the
range would be invalid:

1. Open `Main.xaml`.
2. Wrap `DeleteRange_1` in an `If` activity with condition
   `lastRow > 0`.
3. In the `Then` branch: keep the Delete Range activity.
4. In the `Else` branch: a `Log Message` noting "Nothing to clean —
   workbook has no data rows" (or leave empty).
5. Save and re-run.

### Alternative — fix the expression

If the workflow genuinely needs to clear cells even when there are
zero data rows, the intent was likely to wipe values without
restructuring. Use `Clear Range` instead:

1. Replace `Delete Range: clear stale block` with `Clear Range` on
   the literal range you want to wipe (e.g., `"A2:Z1000"` — header
   preserved, body wiped).
2. `Clear Range` does not depend on a row count and tolerates
   empty target regions.

### Alternative — use a literal range

If the deletion target is known at design time (e.g., always rows
2 through some maximum), replace the expression with a literal:

1. Update `Range` from `"A1:B" + lastRow.ToString()` to `"A2:B1000"`
   (or whatever fixed bound matches the data shape).
2. Literal ranges remove the runtime dependency entirely.

### Prevention

- Prefer literal A1 ranges when the deletion target is known at
  design time. Expression-based ranges are a runtime hazard.
- For expression-based ranges, always validate the resolved value
  before the activity. A `Log Message Level=Info Message=$"Range: '{range}'"`
  immediately before Delete Range gives you the exact string in
  the job logs — invaluable when this kind of bug recurs.
- Guard against zero-row / empty cases explicitly. The Excel
  activity contract treats "nothing to delete" as a configuration
  error, not a no-op.
- When refactoring expressions, consider all boundary inputs:
  `dtCleanup.Rows.Count = 0` for empty sheets, very large counts
  for full sheets (`"A1:B1048576"` is valid but enormous), and
  negative / null values from upstream activity failures.
