# Excel Delete Range — Shift Conflict with Merged Region

This scenario reproduces a Delete Range failure where `ShiftCells=True`
with `ShiftOption=ShiftUp` collides with a merged region anchored on
the bottom edge of the deletion target. The job ends with:

```
System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.
```

## What this scenario uncovers

**Root Cause:** The workflow's Delete Range activity targets
`Q1!A3:C5` with `ShiftCells=True ShiftOption=ShiftUp`. Sheet `Q1`
has a merged region `D5:D7` whose anchor sits on the bottom edge of
the deletion target. Excel's `Range.Delete xlShiftUp` cannot move
rows 6-7 into row 5 without breaking the merge, so Excel COM rejects
the call with the generic `0x800A03EC` Application-defined error.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/delete-range-failures.md`
(the "ShiftCells / ShiftOption conflict" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | `ExcelQuarterlyProcess` project — Classic `Excel Application Scope` → `Delete Range` with Range=A3:C5, ShiftCells=True, ShiftOption=ShiftUp |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (COMException 0x800A03EC
on Delete Range) → `jobs logs` (merged-region scan + ShiftCells
config + COM dispatch failure) → workflow source review (confirms
ShiftCells=True ShiftOption=ShiftUp on A3:C5) → conclude branch 3.

> **Note on fixtures.** Synthetic. The merged region's exact
> coordinates and HRESULT detail are placeholders. The test grades
> whether the agent connects the ShiftCells/ShiftOption configuration
> to the merged-region collision and recommends a viable fix (disable
> shift, switch to EntireRow, switch to Clear Range, or restructure
> the merge).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
