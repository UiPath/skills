# Final Resolution

---

**Root Cause:** The workbook's defined name `MyDataRange` has a
`Refers to` of `#REF!` in Name Manager. It previously pointed at
`Sheet1!A1:E1000`, but `Sheet1` was deleted (or the cell range was
restructured) upstream, and the named range was not updated. When
the workflow's `Read Range` activity, configured with
`Range: "MyDataRange"`, walks the workbook's defined-names
collection to resolve the name, it gets a broken-reference target.
The activity's range-resolution code does not anticipate the
`#REF!` case and throws a generic `NullReferenceException` without
a cell pointer.

**What went wrong:** Failing job
`bb222222-bbbb-cccc-dddd-eeeeffffaaaa` opened the workbook
successfully and ran `Get Workbook Sheets`, which returned the
current sheets (Sheet1 is missing -- only `Data`, `Summary`, and
`Archive` remain; the deletion is upstream). The subsequent
`Read Range` activity, configured with `Range: "MyDataRange"`,
attempted to resolve the named range and surfaced the broken
reference as `NullReferenceException`.

**Why:** Excel's Name Manager stores named ranges as cell-address
references (e.g., `Sheet1!A1:E1000`). When a sheet or range that a
named range depends on is deleted, Excel replaces the reference
with the sentinel `#REF!` rather than deleting the named range
entry. Workflows that look up named ranges by name without
inspecting the `Refers to` field have no way to distinguish a
valid reference from a `#REF!` one, and surface the failure as a
generic null-reference exception when the activity's parser
encounters the broken target.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `bb222222-...`) -- Faulted at
  `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.NullReferenceException: Object reference not set to an
  instance of an object.` Stack inside
  `UiPath.Excel.Activities.ExcelReadRangeX.ExecuteAsync`. No cell
  address.
- Faulting activity: `ExcelReadRangeX_1` (`Read Range`) at
  `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`: `<uix:ExcelReadRangeX Range="MyDataRange" .../>` --
  the `Range` property is a named range, not an A1 address. This
  is the defining setup for the broken-named-range branch.

### Job logs (decisive)
- Earlier in the run: `Get Workbook Sheets` succeeded and logged
  `[ExcelDailyImport] Available sheets in workbook: ["Data", "Summary", "Archive"]`.
  Notice Sheet1 is NOT in the list -- the upstream deletion is
  reflected.
- The `Read Range` Trace entry includes the named-range lookup
  result:
  `Read Range: MyDataRange -- resolving named range
  'MyDataRange' (RefersTo: '#REF!'; resolved sheet: <null>;
  resolved address: <null>)`
- `RefersTo: '#REF!'` is the smoking gun.

### Cross-check -- what this is NOT
- Not branch 1 (sensitivity label): no label evidence in logs;
  workbook opened fine and Get Workbook Sheets succeeded (label
  failures usually surface earlier).
- Not branch 2 (structural corruption): Get Workbook Sheets
  succeeded; the file is structurally intact.
- Not branch 4 (unsupported OpenXML feature): the workbook was
  parseable enough to enumerate sheets; the issue is a specific
  data-content reference, not a feature parser cannot handle.
- Not branch 5 (heavy formatting): no scale clues; the file is
  presumably normal-sized; the NRE fires at a specific
  named-range lookup, not late in formatting parsing.

---

**Recommended Fix (Resolution):**

### Primary fix -- repair Name Manager

In Excel (on a workstation where you have access to the workbook):

1. Open `C:\Robot\Data\sales-2026-05.xlsx`.
2. Press `Ctrl+F3` (Formulas -> Name Manager).
3. Find the `MyDataRange` entry. Its `Refers to` column will show
   `#REF!`.
4. Two options:
   - **Option A (preserve named range):** Update the `Refers to`
     to the new location of the data (e.g., `Data!A1:E1000` if
     the data moved from the deleted Sheet1 to the Data sheet).
   - **Option B (replace with A1 address):** Delete the
     `MyDataRange` entry. Update the workflow's `Range` property
     from `"MyDataRange"` to the explicit A1 address (e.g.,
     `"A1:E1000"` with the correct `SheetName`).
5. Save the workbook (Ctrl+S).
6. Re-trigger the job to verify.

### Coordination with workbook publisher

The upstream owner who deleted Sheet1 should have updated Name
Manager at the same time. Open a coordination follow-up:

- Document the contract: named ranges referenced by automation
  workflows must remain valid (`Refers to` must not be `#REF!`).
- When deleting sheets or restructuring data, audit Name Manager
  first and update or remove dependent named ranges in the same
  edit.

### Validation at job start (prevention)

Add a pre-Read-Range smoke test that resolves the named range
and fails fast with a clear message naming the broken `Refers to`:

```vb
Dim namedRanges = ExcelWorkbookScope.NamedRanges
Dim target = namedRanges.FirstOrDefault(Function(n) n.Name = "MyDataRange")
If target Is Nothing OrElse target.RefersTo.Contains("#REF!") Then
    Throw New BusinessRuleException(
        $"Named range 'MyDataRange' is missing or broken (RefersTo: '{If(target?.RefersTo, "<not found>")}')")
End If
```

This converts a generic NRE deep in the activity into a one-line
diagnosis at job start.

### Prevention (cross-workflow)

- Workflow review should call out `Range` properties that
  reference named ranges -- they are a fragile abstraction
  when the workbook publisher is a different team.
- Prefer explicit A1 addresses when the workbook layout is
  stable. Use named ranges only when the publisher commits to
  maintaining them.
- If the workbook is regenerated from scratch by an upstream
  script, have the script also recreate the named ranges (not
  leave the previous file's broken references behind).
