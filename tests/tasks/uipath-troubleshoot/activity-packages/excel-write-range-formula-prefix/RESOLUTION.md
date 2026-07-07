# Final Resolution

---

**Root Cause:** The workflow's `Write Range` activity marshalled a
312-row `DataTable` (`dtEmployees`) scraped from the HR system into
the `Directory` sheet of `directory.xlsx`. Row 43 of that DataTable
contained the value `=Smith, John` in the `FullName` column — the
leading `=` was interpreted by Excel COM as the start of a formula,
not a literal name. `=Smith, John` is not a valid Excel formula
(comma in the wrong context, unknown name token), so Excel COM's
`Range.set_Value` rejected the cell with
`System.Runtime.InteropServices.COMException (0x800A03EC):
Application-defined or object-defined error.` This is the
formula-prefix sub-cause of branch 5 in the playbook — the volume
sub-cause is ruled out by the modest size (312 rows × 5 columns).

The most likely origin of the `=` prefix is a data-entry error in
the HR source system (someone typed the equals sign by mistake when
entering the employee's name), but the workflow has no sanitization
step between the HR scrape and the Excel write, so the bad data
passes through verbatim.

**What went wrong:** Failing job
`ee333333-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-26T08:00:01.300Z`. The HR scrape sub-workflow returned a
312-row, 5-column DataTable. The `Use Excel File: directory.xlsx`
scope opened the workbook via the COM provider (the workflow's
cell-format requirements declined the OpenXML fallback). The
`Write Range: employee directory` activity resolved its config
(Sheet='Directory', StartingCell='A1', ExcludeHeaders=False,
DataTable='dtEmployees' rows=312 cols=5), began marshalling the
data into the A1:E313 range, and was rejected by Excel COM at
cell B44 because the source value started with `=`. The activity
surfaced the rejection as the standard 0x800A03EC COMException.

**Why:** Excel's COM `Range.set_Value` interprets any string
starting with `=` as a formula and routes it through the formula
parser. `=Smith, John` parses as an attempted formula call with
two arguments (`Smith` and `John`), but `Smith` is not a defined
name, not a function, and not a valid cell reference, so the
parser raises the generic "application-defined error" HRESULT.
The same value written as a literal text cell (no formula
interpretation) would succeed — Excel's text cells accept
arbitrary content including leading equals signs. The activity
has no opt-in to literal-text mode; the workflow must escape or
sanitize the value before the write.

`+`, `-`, and `@` at the start of a string trigger the same
behavior (formula prefix or "old-style" function reference). Any
field that can contain user-supplied or scraped content is at
risk.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDirectoryProcess` (key `ee333333-...`) —
  Faulted at `2026-05-26T08:00:04.812Z`.
- Folder: `DirectoryOps` (key `f0077777-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException (0x800A03EC):
  Application-defined or object-defined error.` with stack trace
  through
  `Microsoft.Office.Interop.Excel.Range.set_Value(Object, Object)`,
  `UiPath.Excel.Activities.Business.WriteRangeX.WriteCellBlock(Range, DataTable)`,
  and `WriteRangeX.OnExecute(NativeActivityContext)`.
- Faulting activity: `WriteRange_1` (`Write Range: employee directory`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `Invoke: ScrapeHRDirectory.xaml` → `dtEmployees` (out-arg).
    The sub-workflow returns names verbatim from the HR system
    with no sanitization.
  - `Use Excel File: directory.xlsx` — COM provider.
  - `<uix:ExcelWriteRange DataTable="[dtEmployees]" ExcludeHeaders="False" StartingCell="A1" SheetName="Directory" ... />`
- No intermediate `Filter Data Table`, `For Each Row` + escape
  step, or any other sanitization between scrape and write.

### Job logs (decisive)
- `Invoke: ScrapeHRDirectory.xaml — returned dtEmployees with 312 rows, 5 columns (Id, FullName, Department, Email, Title)`
- `Use Excel File: directory.xlsx — workbook opened (COM provider; OpenXML fallback declined due to cell-format requirements)`
- `Write Range: employee directory — resolved config Sheet='Directory' StartingCell='A1' ExcludeHeaders=False DataTable='dtEmployees' (rows=312 cols=5)`
- `Write Range: employee directory — marshalling DataTable to Excel COM range A1:E313 (header row + 312 data rows)`
- `Write Range: employee directory — COM Range.set_Value rejected cell B44: source row 43 (0-indexed 42) column 'FullName' has value '=Smith, John' (leading '=' interpreted as malformed formula by Excel)`
- `Write Range: employee directory — System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.`

The decisive log line is the cell-rejection Trace that names the
exact offending value (`=Smith, John`) and the cell (B44 → source
row 43 → column `FullName`). This is the smoking gun: the value's
leading `=` is interpreted by Excel COM as a formula prefix, the
parser rejects the resulting "formula", and the activity surfaces
the COM HRESULT as-is.

### Cross-check — what this is NOT
- Not branch 1 (uninitialized DataTable): `dtEmployees` is
  populated with 312 rows / 5 columns; clearly initialized.
- Not branch 2 (workbook locked / read-only): the workbook
  opened cleanly per the logs; no `IOException`, no
  "cannot access the file" COMException.
- Not branch 3 (empty source + ExcludeHeaders=False): the source
  has 312 rows — the empty-source branch requires rows=0.
- Not branch 4 (hidden rows / columns): the BusinessException
  signature for branch 4 would mention "hidden rows" or "hidden
  columns" explicitly. The exception here is a generic 0x800A03EC
  COMException from the formula-parsing path.
- Not branch 5 volume sub-cause: 312 rows × 5 columns is well
  under the threshold where OOM / batch-overflow becomes likely.
  The cell-level rejection log line pins the cause to a single
  problematic cell value, not bulk memory pressure.

---

**Recommended Fix (Resolution):**

### Primary fix — sanitize formula-prefix characters before the write

Pre-clean the DataTable to neutralize cells starting with `=`, `+`,
`-`, or `@`. Two acceptable approaches:

**Approach 1: prefix with apostrophe (literal-text escape)**

Insert a `For Each Row` activity between the HR scrape and the
Write Range. For each row, check the `FullName` (and any other
free-text column) for the leading-formula characters and prefix
an apostrophe (`'`) when found:

```
For Each Row row in dtEmployees
  For Each Col col in {"FullName", "Email", "Title"}
    val = Convert.ToString(row(col))
    If val.Length > 0 AndAlso "=+-@".Contains(val(0)) Then
      row(col) = "'" & val
    End If
```

Excel renders apostrophe-prefixed cells as literal text without
showing the apostrophe. The apostrophe is stored in the file but
invisible in the rendered cell.

**Approach 2: strip the prefix (data correction)**

If the leading character is unambiguously a data-entry error (an
HR record's `FullName` should never start with `=` or `+`), strip
it:

```
For Each Row row in dtEmployees
  val = Convert.ToString(row("FullName"))
  row("FullName") = val.TrimStart("="c, "+"c, "-"c, "@"c)
```

This is appropriate when the value should not have the prefix at
all — but mistakenly accepting `=Smith, John` as `Smith, John`
may hide an upstream data-quality issue. Combine with a `Log
Message Level=Warn` that flags the correction so it doesn't go
unnoticed.

### Alternative — fix at the source

If the workflow has any influence over the HR system's data
entry, fix the bad record there: open the employee's profile in
HR, remove the leading `=` from the `FullName` field, save. This
solves THIS instance but does not prevent recurrence — the next
data-entry mistake produces the same failure.

### Alternative — switch to OpenXML provider

The OpenXML provider does not interpret leading `=` as a formula
on writes (it stores values as inline strings). Switch the `Use
Excel File` scope's provider settings to prefer OpenXML, OR remove
the cell-format requirements that forced COM in this workflow.
This is a structural change with broader implications (cell
formatting, formulas in other cells, performance) — evaluate
before applying.

### Anti-pattern (do NOT use)

Do NOT "fix" this by adding a `Try Catch` around the Write Range
that catches `COMException` and continues. The catch turns the
write into a silent partial — Excel COM rejected at cell B44, so
rows 1-42 were written but rows 43-312 were NOT. Downstream
consumers reading the directory see 42 employees instead of 312,
with no error and no log entry indicating the truncation. This is
the playbook's anti-pattern #2 (bare Try-Catch suppression).

### Prevention

- For workflows that aggregate or transform user-supplied content
  (HR scrapes, form input, queue payloads, document extraction):
  always apply a formula-prefix sanitization step before any
  Excel write. Treat any user-supplied string as potentially
  formula-shaped.
- Log a sample of suspicious values when sanitization fires, so
  upstream data quality issues are observable rather than
  silently corrected.
- Prefer OpenXML provider for workflows that write user-supplied
  strings — its write semantics don't interpret leading `=` as a
  formula. Use COM only when the workflow genuinely needs
  COM-specific features (formatting, formulas in other cells,
  macros).
- For high-confidence text-only columns (names, IDs, emails),
  consider enforcing a type check on the DataTable column as
  early as possible in the workflow — a `String` column whose
  values must not start with `[=+\-@]` can be validated cheaply
  at the source step.
