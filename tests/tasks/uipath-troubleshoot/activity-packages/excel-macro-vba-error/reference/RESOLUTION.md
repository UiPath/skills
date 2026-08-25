# Final Resolution

---

**Root Cause:** The macro `Module1.ProcessData` was successfully
dispatched by Excel COM (`Application.Run` found the macro and
started executing) but threw `Run-time error '91': Object variable
or With block variable not set` from inside the VBA code. The
activity surfaces this via the standard Excel-COM wrapper:
HRESULT `0x80020009 (DISP_E_EXCEPTION)` indicating "the IDispatch
target raised an exception", with the inner VBA error captured
in the COMException message.

Run-time error 91 specifically means the macro dereferenced an
object variable (`Range`, `Worksheet`, `Workbook`, `Cells`, etc.)
that was never assigned with `Set`. The most common patterns:

- `Set rng = Cells.Find(what:="header")` followed by use of `rng`
  when `Find` returned `Nothing` because the search term wasn't
  present.
- `Set sht = ThisWorkbook.Worksheets(name)` where the sheet
  `name` doesn't exist in the workbook.
- `Dim wb As Workbook` declared and dereferenced without ever
  being `Set`.

**What went wrong:** Failing job
`bb222222-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope opened the
workbook; `Execute Macro` dispatched `Module1.ProcessData` via
`Application.Run`. The macro began executing and faulted inside
its own VBA code at a line that dereferenced a `Nothing` object
reference. Excel's COM layer caught the VBA Err and re-raised it
to the activity as `DISP_E_EXCEPTION` with the inner Err.Description
attached.

**Why:** The macro's logic does not defensively check whether a
lookup returned `Nothing` before dereferencing the result. The
user's "worked last week" clue strongly suggests something about
the input data or workbook structure changed: a header row was
deleted, a sheet was renamed, or a search term that previously
matched now doesn't. The macro's runtime behavior depends on
workbook state that the workflow's earlier activities (or upstream
data) determine.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelMacroProcess` (key `bb222222-...`) -- Faulted
  at `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException (0x80020009):
  Exception occurred.\r\n ---> Run-time error '91': Object
  variable or With block variable not set`
- Faulting activity: `ExecuteMacro_1` (`Execute Macro:
  Module1.ProcessData`) at `Main.xaml`.

### HRESULT (decisive)
- `0x80020009 DISP_E_EXCEPTION` -- the COM wrapper for "IDispatch
  target raised an exception". This SPECIFICALLY indicates the
  macro ran past the lookup / dispatch stage and faulted in its
  own code, NOT that the macro is missing (branch 1) or Trust
  Center disabled (branch 5).

### Inner VBA error (decisive)
- `Run-time error '91': Object variable or With block variable
  not set` -- specific VBA error code 91, meaning an object
  variable was dereferenced without first being `Set`. Different
  from:
  - Error 9 (Subscript out of range) -- array / collection
    indexing failure.
  - Error 13 (Type mismatch) -- assignment incompatibility.
  - Error 1004 (Application-defined or object-defined error) --
    generic Excel object error.
  - Error 424 (Object required) -- usually missing reference
    (branch 7).
  - Error 429 (ActiveX component can't create object) -- branch
    7 (missing ActiveX).

### Workflow source
- `Main.xaml`: `<uix:ExecuteMacro MacroName="Module1.ProcessData"
  .../>` -- the macro name is qualified (`Module.Sub`).
- The macro is in the workbook (the dispatch succeeded) -- rules
  out branch 1.
- Job logs show the macro started executing -- the COMException
  is from inside the macro, not from Excel rejecting the call.

### Cross-check -- what this is NOT
- Not branch 1 (macro not found): the macro dispatched
  successfully (Excel found `Module1.ProcessData`); the error
  comes from inside the macro's execution.
- Not branch 3 (Excel torn down): the error is on `Execute Macro`
  itself, not a later activity with `RPC_E_DISCONNECTED`.
- Not branch 4 (modal dialog): the job didn't hang; it surfaced
  a specific COMException.
- Not branch 5 (Trust Center disabled): the macro was allowed to
  run -- it just threw mid-execution. If Trust Center blocked
  macros, the COMException would say "Cannot run the macro..."
  not the DISP_E_EXCEPTION wrapper.
- Not branch 6 (concurrent COM): no `0x800AC472`; the failure is
  deterministic with this input data.
- Not branch 7 (missing add-in / ActiveX): inner error is 91, not
  424 (Object Required) or 429 (ActiveX cant create). If a
  reference were missing, the macro likely wouldn't compile, or
  would throw a different inner error.

---

**Recommended Fix (Resolution):**

### Step 1 -- Reproduce in the VBA editor

1. Open the workbook in Excel.
2. `Alt+F11` to open the VBA editor.
3. Find `Module1.ProcessData` and review the code.
4. Run the macro manually with the same input data (`F5` or
   `F8` for step-through). The VBE will break at the line
   throwing Run-time error 91.

### Step 2 -- Fix the unsafe dereference

The faulting line will be using an object variable. Wrap the
dereference with a null check OR ensure the lookup succeeds
before continuing. Examples:

```vba
' Before (unsafe):
Dim rng As Range
Set rng = ThisWorkbook.Worksheets("Data").UsedRange.Find("Header")
rng.Offset(1, 0).Select   ' Error 91 if Find returned Nothing

' After (defensive):
Dim rng As Range
Set rng = ThisWorkbook.Worksheets("Data").UsedRange.Find("Header")
If rng Is Nothing Then
    Err.Raise vbObjectError + 1001, "ProcessData", _
              "Could not find 'Header' in Data sheet's used range. " & _
              "Confirm the sheet's structure has not changed."
End If
rng.Offset(1, 0).Select
```

### Step 3 -- Identify why it worked last week

The user noted the macro worked previously. Likely changes
between then and now:

- **Workbook structure changed** -- a sheet was renamed, a
  header cell was edited, a row/column was deleted upstream.
  Coordinate with the workbook publisher.
- **Input data changed** -- the upstream process that writes
  the workbook now produces different content. The lookup
  previously matched but no longer does.
- **VBA references changed** -- less likely for Run-time error
  91 specifically, but possible if the macro `Set`s its
  variables from a configuration sheet that was modified.

Whichever applies, the lookup should not be silent: convert it
to fail-fast with a clear message that names what the macro
expected vs. what it found.

### Step 4 -- Structured error handling

Add `On Error GoTo` to the macro so future failures surface a
useful Err.Description instead of a generic Run-time error:

```vba
Sub ProcessData()
    On Error GoTo ErrHandler

    ' ... macro body ...

    Exit Sub
ErrHandler:
    Err.Raise Err.Number, "Module1.ProcessData", _
              "ProcessData failed at line " & Erl & ": " & Err.Description
End Sub
```

This makes the COMException's inner message much more diagnostic
for the next UiPath job to fault.

### Prevention

- Defensive object-variable usage: always check `If obj Is
  Nothing Then ...` after any lookup (`Find`, `Worksheets(name)`,
  collection indexers).
- Treat the macro as headless: it must not assume workbook state
  that the upstream process could change without coordinating
  with the workflow consumer.
- Add `On Error GoTo ErrHandler` + `Err.Raise` to every public
  Sub consumed by UiPath. Generic Run-time errors are much
  harder to diagnose than `Err.Raise` with a clear description.
- Unit-test macros against the same data shapes the workflow
  will produce. The "works on my data, fails on production
  data" pattern is what produces Run-time error 91 in the wild.
