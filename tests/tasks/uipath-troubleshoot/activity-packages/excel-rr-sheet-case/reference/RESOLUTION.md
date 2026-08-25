# Final Resolution

---

**Root Cause:** Workflow configured `SheetName: "data"` (lowercase)
on the `ExcelReadRangeX` activity. The workbook's actual sheets are
`["Sheet1", "Data", "Summary"]` — the sheet exists as `Data` with a
capital D. The workflow uses `Use Excel File` (modern scope) with
no `ReadFormatting`, `EditPassword`, or macro-related properties
set, so the runtime selects the OpenXML provider. OpenXML is
**case-sensitive** in sheet name lookups; `"data"` does not match
`"Data"`, and the activity throws `BusinessException`.

**What went wrong:** Failing job
`bb222222-7777-8888-9999-000011112222` opened the workbook
`C:\Robot\Data\sales-2026-05.xlsx` successfully on `MOCK-HOST`. The
workflow's `Get Workbook Sheets` activity enumerated the actual
sheets and logged the list. The subsequent `Read Range` activity,
configured with lowercase `"data"`, attempted to resolve that name
against the workbook's actual titles. The OpenXML provider's
case-sensitive comparison rejected the lookup and the activity
faulted with `BusinessException`.

**The "worked on dev" clue:** The dev machine where the workflow
was authored has Microsoft Excel installed. When the workflow ran
there, `Use Excel File` selected the Excel COM provider (the
runtime falls back to COM when Excel is available). Excel COM is
case-insensitive in sheet name lookups, so `"data"` matched `Data`
silently. On the Robot host (`MOCK-HOST`), Excel is not installed
(or the project's properties do not force COM), so the runtime
selected OpenXML — case-sensitive — and the same workflow now
fails.

**Why:** Modern `Use Excel File` was designed to be cross-platform.
Its default provider (OpenXML) does not normalize case in sheet
name lookups because the underlying file format does not require
it. Excel COM is case-insensitive because Excel itself was designed
around Windows-style case-insensitive APIs. Workflows that depend
on case-insensitive sheet lookups silently couple themselves to the
COM provider; when the runtime falls through to OpenXML on a
headless host, the coupling breaks.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `bb222222-...`) — Faulted at
  `2026-05-19T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`. **Excel is not
  installed** (the host is a headless Robot — no `EXCEL.EXE`).
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The sheet with the name 'data' does not exist.`
- Faulting activity: `ExcelReadRangeX_1` (`Read Range`) at
  `Main.xaml`.

### Workflow logs
- `Get Workbook Sheets` succeeded and logged:
  `[ExcelDailyImport] Available sheets in workbook:
  ["Sheet1", "Data", "Summary"]`.
- Note the configured `SheetName: "data"` is lowercase; the actual
  sheet is `Data` (capital D).

### Workflow source
- `Main.xaml`: `<uix:UseExcelFile WorkbookPath="..."
  ReferenceName="ExcelWorkbookScope" ...>` — modern scope. No
  `ReadFormatting`, `EditPassword`, or macro-related properties set.
  Defaults to OpenXML provider on a host without Excel installed.
- `Main.xaml`: `<uix:ExcelReadRangeX SheetName="data" .../>` — the
  configured name is a literal lowercase string.

### Cross-check — what this is NOT
- Not a typo: the configured `"data"` differs from `"Data"` only
  in case, not in any character.
- Not whitespace: lengths match (both 4 chars).
- Not look-alike Unicode: `d` is ASCII lowercase, `D` is ASCII
  uppercase — same code points except case.
- Not sheet renamed: `Data` is present and matches the configured
  name in spelling.
- Not dynamic-expression-wrong: the configured `SheetName` is a
  literal in workflow source.

---

**Recommended Fix (Resolution):**

### Primary fix — match casing in the workflow

In `Main.xaml`, update `ExcelReadRangeX_1`'s `SheetName` property
from `"data"` to `"Data"`. Cheapest fix, fully portable across
provider runtimes (COM and OpenXML both accept the case-correct
form).

### Alternative — force the COM provider

If matching casing is not feasible (e.g., the workflow consumes
sheet names from an external source and you cannot normalize), set
`ReadFormatting: True` (or another COM-forcing property) on the
`Use Excel File` scope to force the runtime to use Excel COM. This
restores the case-insensitive lookup but requires Excel installed
on every Robot host that runs the workflow.

### Validation at job start (prevention)

The workflow already enumerates sheets via `Get Workbook Sheets`.
Add a case-insensitive validation that maps the configured name to
the actual case before reading:

```vb
Dim configured = "data"
Dim actual = availableSheets.FirstOrDefault(
    Function(s) s.Equals(configured, StringComparison.OrdinalIgnoreCase))
If String.IsNullOrEmpty(actual) Then
    Throw New BusinessRuleException(
        $"Sheet '{configured}' not in workbook. Available: {String.Join(", ", availableSheets)}")
End If
' Then use `actual` for the Read Range
```

This makes the workflow portable across providers and fails fast
with a clear message when the name is truly missing.

### Prevention (cross-workflow)

- Default to case-sensitive matching in your workflows even when
  the current provider is case-insensitive. Cheaper than discovering
  the bug after migrating to a headless host.
- If `Use Excel File` MUST behave like Excel COM (case-insensitive),
  document the COM-forcing property in the project's README so
  future authors do not strip it.
- Treat the workbook's sheet casing as canonical. Workflows
  consume the case the workbook publishes.
