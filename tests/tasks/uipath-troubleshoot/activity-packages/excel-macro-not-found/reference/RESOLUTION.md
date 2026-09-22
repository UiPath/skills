# Final Resolution

---

**Root Cause:** The workflow's Execute Macro activity is configured
with `MacroName: "RunImport"`, but the workbook's VBA project
contains macros `Module1.ProcessData` and `Module2.UpdateReport` --
NOT `RunImport`. When Excel COM dispatches the macro call by name,
the VBA project's macro-name lookup returns nothing, and Excel
surfaces the canonical `Cannot run the macro 'RunImport'. The macro
may not be available in this workbook or all macros may be
disabled.` COMException.

**What went wrong:** Failing job
`aa111111-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope opened the
workbook (no IOException, no FileNotFoundException). The `Execute
Macro` activity enumerated the workbook's VBA modules (the activity
exposes this in its Trace logs as a sanity check), found two
public Subs (`Module1.ProcessData`, `Module2.UpdateReport`), then
attempted to dispatch the configured name `RunImport` via COM. The
COM dispatch failed with the standard "macro not available" error
because no public Sub by that name exists.

**Why:** Excel's COM `Application.Run` looks up the macro by its
qualified name in the active workbook's VBA project. If the name
matches no Sub / Function, Excel returns an error -- there is no
fallback to other open workbooks (unless the macro is in a loaded
add-in or `Personal.xlsb`, neither of which a default Robot
session loads). The same error wording also fires when macros are
globally disabled by Trust Center (branch 5), so distinguishing
branch 1 vs. branch 5 requires comparing the configured name
against the workbook's actual VBA module enumeration.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelMacroProcess` (key `aa111111-...`) -- Faulted
  at `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException: Cannot run the
  macro 'RunImport'. The macro may not be available in this
  workbook or all macros may be disabled.`
- Faulting activity: `ExecuteMacro_1` (`Execute Macro`) at
  `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`: `<uix:ExecuteMacro MacroName="RunImport" .../>` --
  the configured macro name is a literal string.

### Job logs (decisive)
- `Execute Macro: RunImport -- enumerating VBA modules in workbook`
- `Execute Macro: RunImport -- VBA modules: ['Module1.ProcessData', 'Module2.UpdateReport']`
- `Execute Macro: RunImport -- dispatching macro via COM`
- `Execute Macro: RunImport -- COMException: Cannot run the macro
  'RunImport'. The macro may not be available in this workbook or
  all macros may be disabled.`

The enumeration log line is the smoking gun: the configured name
`RunImport` is absent from the enumerated list. The workbook has
two macros, neither of which is `RunImport`.

### Cross-check -- what this is NOT
- Not branch 5 (Trust Center disabled): the VBA-module enumeration
  succeeded, which means the COM client CAN read the workbook's
  VBA project. If macros were globally disabled by Trust Center,
  the enumeration would either be empty or the COM call would
  fail earlier with a different error. The error fires
  specifically at dispatch, after enumeration.
- Not branch 2 (VBA error in macro): no `DISP_E_EXCEPTION`
  (0x80020009) and no inner Run-time error text -- the macro never
  ran.
- Not branch 3 (Excel torn down): no `RPC_E_DISCONNECTED` on a
  later activity; the failure is on Execute Macro itself.
- Not branch 4 (modal dialog): the job didn't hang; it surfaced an
  exception immediately.
- Not branch 6 (concurrent COM): no `0x800AC472`; the failure is
  the standard macro-lookup error, not a threading violation.
- Not branch 7 (missing add-in / ActiveX): no compile error / 424
  Object Required / 429 ActiveX-cant-create; the macro never
  started executing.

---

**Recommended Fix (Resolution):**

### Primary fix -- correct the macro name

The workbook contains `Module1.ProcessData` and
`Module2.UpdateReport`. The workflow author needs to confirm which
of these (or some other macro) was intended:

1. Open `Main.xaml` and update `ExecuteMacro_1`'s `MacroName`
   property from `"RunImport"` to the correct qualified name
   (e.g., `"Module1.ProcessData"`).
2. Re-run the job to verify.

### Alternative -- add the missing macro to the workbook

If `RunImport` is genuinely supposed to exist (the workflow was
ported from a different project where this macro lives in the
workbook):

1. Open the workbook in Excel -> `Alt+F11` (VBA editor).
2. Add a new Module (`Insert -> Module`).
3. Implement the `RunImport` Sub.
4. Save the workbook with `.xlsm` extension (macro-enabled
   workbook) and re-trigger.

### Alternative -- open the source workbook instead

If `RunImport` lives in a DIFFERENT workbook (e.g.,
`MacroLibrary.xlsm`):

1. Update the workflow to open that workbook's path in the
   `Use Excel File` scope.
2. Or use Excel's `Workbook.Open` to bring the macro source into
   scope before invocation.

### Prevention

- Use **explicit qualified names** for `MacroName`:
  `"Module1.RunImport"` rather than `"RunImport"`. Unqualified
  names are ambiguous and harder to maintain.
- Document the workbook's macro contract: macros consumed by
  UiPath workflows must remain present and named consistently.
  Renaming a public Sub is a breaking change for downstream
  workflows.
- Avoid relying on `Personal.xlsb` -- Robot unattended sessions
  do not load it by default.
- Avoid relying on add-ins -- they require host-side registration
  under the Robot user (see branch 7 of the playbook).
- Consider a pre-invocation smoke test that enumerates the
  workbook's macros and fails fast with a clear message if the
  configured `MacroName` is absent (similar pattern to
  `Get Workbook Sheets` for sheet names).
