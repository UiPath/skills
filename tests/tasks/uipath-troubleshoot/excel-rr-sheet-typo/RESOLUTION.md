# Final Resolution

---

**Root Cause:** Workflow configured `SheetName: "Datab"` on the
`ExcelReadRange` activity. The workbook's actual sheets are
`["Sheet1", "Data", "Summary"]`. The configured name `Datab` does
not match any sheet — but is a one-character typo of `Data` (extra
trailing `b`).

**What went wrong:** Failing job
`aa111111-7777-8888-9999-000011112222` opened workbook
`C:\Robot\Data\sales-2026-05.xlsx` successfully (no `IOException`,
no `FileNotFoundException`). The workflow's first activity,
`Get Workbook Sheets`, ran successfully and logged the available
sheet titles. The subsequent `Read Range` activity, configured with
`SheetName: "Datab"`, attempted to resolve that name against the
workbook's actual titles and failed with `BusinessException` because
no sheet matches.

**Evidence chain (CLI):**

- `or jobs get`: returns `State: Faulted` with `Info` containing
  `UiPath.Excel.BusinessException: The sheet with the name 'Datab'
  does not exist.` and `ActivityName: ExcelReadRange_1`.
- `or jobs logs`: contains a LogMessage entry from the prior
  `Get Workbook Sheets` activity:
  `[ExcelDailyImport] Available sheets in workbook: ["Sheet1", "Data", "Summary"]`.
- Workflow source: `Main.xaml` has `<uix:ExcelReadRangeX
  SheetName="Datab" ...>`. The configured value is a hard-coded
  literal, not a dynamic expression.

**Why:** The configured `SheetName` literal `"Datab"` was typed
with an extra trailing `b`. The workflow was authored by hand and
the typo was not caught at design time (Studio does not validate
sheet names against an actual workbook). At runtime, the Excel
activity passed `"Datab"` to the OpenXML / COM provider, which
checked the workbook's sheet collection and returned no match.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `aa111111-...`) — Faulted at
  `2026-05-19T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The sheet with the name 'Datab' does not exist.`
- Faulting activity: `ExcelReadRange_1` (`Read Range`) at
  `Main.xaml`.

### Workflow logs
- `Get Workbook Sheets` succeeded at `2026-05-19T08:00:01.512Z`
  and logged: `[ExcelDailyImport] Available sheets in workbook:
  ["Sheet1", "Data", "Summary"]`.
- The actual sheet list is the authoritative ground truth from the
  Robot host at the moment of the failure.

### Workflow source
- `Main.xaml`: `<uix:ExcelReadRangeX SheetName="Datab" .../>` — the
  configured value is a literal, not a dynamic expression. No
  upstream variable to trace.

### Cross-check — what this is NOT
- Not case-mismatch: `"Datab"` vs `"Data"` differs in length, not
  just case.
- Not whitespace: lengths differ by one trailing character `b`,
  not a space.
- Not look-alike Unicode: the differing character is ASCII `b`,
  not a similar code point.
- Not sheet renamed: workbook still has `Data`; no recent rename
  was reported.
- Not deleted: `Data` is present in the enumerated list.
- Not dynamic-expression-wrong: the configured `SheetName` is a
  literal in workflow source.

---

**Recommended Fix (Resolution):**

1. **Immediate:** Update the `SheetName` property on
   `ExcelReadRange_1` in `Main.xaml` from `"Datab"` to `"Data"`.

2. **Validation at job start (prevention):** The workflow already
   enumerates sheets via `Get Workbook Sheets`. Add a validation
   step immediately after the enumeration: check that every
   configured sheet name appears in the returned list, and fail
   fast with a clear message naming the configured-but-missing
   name(s) AND the actual list. This converts a generic
   `BusinessException` deep in the workflow into a one-glance
   diagnosis at job start.

3. **Prevention (cross-workflow):** When the workbook is authored
   by a different team, do not hard-code sheet names. Either treat
   the layout as a contract (publish a sheet-name list in a
   metadata sheet or named range that the workflow reads), or
   always validate at job start.
