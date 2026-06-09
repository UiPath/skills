# Final Resolution

---

**Root Cause:** The workflow's `Delete Range` activity is configured
with `Range="A3:C5"`, `ShiftCells=True`, `ShiftOption=ShiftUp`. The
target sheet `Q1` has a merged region `D5:D7` that anchors at row 5
on the right side of the deletion target. Excel COM's `Range.Delete
xlShiftUp` would have to move rows 6-7 into row 5 — but doing so
breaks the merge anchor at `D5`, and Excel refuses to perform a shift
that requires splitting or relocating an existing merge. The activity
surfaces this as `System.Runtime.InteropServices.COMException
(0x800A03EC): Application-defined or object-defined error.` — Excel's
generic "I can't do that" HRESULT.

**What went wrong:** Failing job
`dd222222-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-22T08:00:01.300Z`. The `Excel Application Scope` opened the
workbook cleanly. The `Delete Range` activity resolved its config
(Range=A3:C5, ShiftCells=True, ShiftOption=ShiftUp), scanned merged
regions on the sheet and logged the adjacent merge at `D5:D7`,
dispatched the COM `Range.Delete(xlShiftUp)` call, and received the
`0x800A03EC` rejection from Excel COM.

**Why:** Excel's shift semantics require that the destination cells
of a shift operation be free of merge anchors that would have to be
broken. A merged region whose top-left anchor sits on the deletion
target's bottom edge (row 5 for an A3:C5 target) cannot be relocated
by ShiftUp because the merge would need to migrate into row 4 — and
Excel's COM API refuses partial merge relocations. The same operation
performed interactively in Excel (select A3:C5, `Home → Delete →
Delete Cells… → Shift cells up`) produces the same rejection with a
dialog stating "This operation requires the merged cells to be
identically sized."

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelQuarterlyProcess` (key `dd222222-...`) — Faulted
  at `2026-05-22T08:00:02.812Z`.
- Folder: `Quarterly` (key `f0033333-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException (0x800A03EC):
  Application-defined or object-defined error.` with stack trace
  through `Microsoft.Office.Interop.Excel.Range.Delete(Object Shift)`
  and `UiPath.Excel.Activities.DeleteRange.OnExecute(...)`.
- Faulting activity: `DeleteRange_1` (`Delete Range: drop stale block`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  `<uix:DeleteRange SheetName="Q1" Range="A3:C5" ShiftCells="True" ShiftOption="ShiftUp" ... />`
  — all four configuration properties are literals.
- Scope: Classic `ExcelApplicationScope` with
  `WorkbookPath="C:\Robot\Data\quarterly-report.xlsx"`,
  `Visible="False"`, `AutoSave="True"`.

### Job logs (decisive)
- `Delete Range: drop stale block — resolved config Sheet='Q1' Range='A3:C5' ShiftCells=True ShiftOption=ShiftUp`
- `Delete Range: drop stale block — sheet 'Q1' merged regions adjacent to target: ['D5:D7'] (bottom edge of A3:C5 abuts merge anchor at D5)`
- `Delete Range: drop stale block — dispatching Excel COM Range.Delete(xlShiftUp) on Q1!A3:C5`
- `Delete Range: drop stale block — System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.`

The merged-region scan log is the smoking gun: `D5:D7` is anchored
at row 5, the bottom of the deletion target. A ShiftUp cannot run
without violating Excel's merge-relocation rule, and the activity
sees Excel's standard `0x800A03EC` rejection.

### Cross-check — what this is NOT
- Not branch 1 (activity outside a scope container): the
  `Excel Application Scope` wraps the Delete Range in `Main.xaml`.
  If the scope were missing, the failure would be a
  `BusinessException` referencing the missing scope rather than a
  COMException.
- Not branch 2 (invalid range syntax): `A3:C5` is a well-formed
  literal A1 rectangular range; the validator accepted it and the
  activity proceeded to dispatch.
- Not branch 4 (workbook locked / read-only): the workbook opened
  cleanly per the logs; no `IOException`, no "cannot access the
  file" COMException.
- Not branch 5 (filter misalignment): no AutoFilter on the sheet;
  the failure is a hard rejection at the COM dispatch, not a
  silent data corruption with a downstream exception.

---

**Recommended Fix (Resolution):**

### Primary fix — disable the shift

The simplest, lowest-risk change: if the workflow's intent is to
clear cells (not restructure the sheet), set `ShiftCells` to `False`.
Delete Range with `ShiftCells: False` removes cell values and
formatting in place without shifting surrounding rows, and does not
interact with adjacent merged regions.

1. Open `Main.xaml` and update `DeleteRange_1`:
   - `ShiftCells="False"`
   - Remove or ignore `ShiftOption` (unused when ShiftCells is False).
2. Save and re-run.

### Alternative — switch to EntireRow

If the workflow's intent IS to remove the rows and reflow remaining
data: change the deletion target to whole rows and use `EntireRow`.
Excel handles whole-row deletes more robustly than partial-row
shifts because the merge moves with the row rather than crossing
into adjacent cells.

1. Adjust the workflow's logic to operate on whole rows (e.g.,
   `Range="A3:A5"` covering only the rows you want gone — the
   sheet width parameter is irrelevant when `ShiftOption=EntireRow`).
2. Update `ShiftOption` to `EntireRow`.
3. Re-run.

### Alternative — replace with Clear Range

If the goal is to wipe values while preserving cell structure /
formatting / merged regions, `Clear Range` is the purpose-built
activity. It does not require a shift direction and does not
interact with surrounding merges.

1. Replace `DeleteRange_1` with `Clear Range` on the same
   `SheetName="Q1"`, `Range="A3:C5"`.
2. Re-run.

### Alternative — restructure the merge

If the merged region `D5:D7` is incidental (e.g., a legacy header
spacer), the workbook author can remove or relocate it so future
deletions are not constrained. This is a workbook-side fix, not
a workflow-side fix, and should be coordinated with the workbook
owner.

### Prevention

- Avoid `ShiftCells: True` on workbooks with merged regions or
  structured Tables adjacent to deletion targets. The default-True
  is a frequent source of these failures.
- Prefer `EntireRow` deletes when the workflow's intent is row
  removal; the activity is more predictable than partial-row shifts.
- Use `Clear Range` when only values need to be wiped — it sidesteps
  the entire shift / merge / Table interaction surface.
- Reproduce the operation manually in Excel before automating it:
  if Excel itself rejects the action interactively, the activity
  will too.
- Document workbook layout constraints (merged regions, Excel
  Tables, freeze panes) as part of the workflow contract — a
  workbook author who later adds a merge can silently break a
  previously-working Delete Range.
