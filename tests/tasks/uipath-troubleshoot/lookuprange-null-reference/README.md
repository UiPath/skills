# Lookup Range Failure - Object Reference Not Set (No Excel Scope)

This scenario reproduces a classic `Lookup Range` failure caused by the
activity being placed **outside any Excel scope**. The classic
`Lookup Range` needs an `Excel Application Scope` to provide its workbook
context; dropped directly into the Main `Sequence` with no scope, it
dereferences a null workbook handle and faults with
`System.NullReferenceException: Object reference not set to an instance of
an object`.

## What this scenario uncovers

**Root Cause:** In `Main.xaml`, the `Lookup Range` activity sits directly
in the Main `Sequence` with **no surrounding `Excel Application Scope`**
(or `Use Excel File`). There is no workbook context object, so the activity
dereferences null and throws a `NullReferenceException` the instant it runs.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-null-reference.md`
(the **no surrounding scope** cause).

It is **not** a missing Excel install (no `REGDB_E_CLASSNOTREG` -> that
routes to `lookup-range-excel-not-installed.md`) and **not** a file-in-use
fault (no IOException -> `lookup-range-file-locked.md`). The fault stack
goes `ExcelLookUpRange` -> `Sequence "Main Sequence"` -> `Main` with **no scope
in between**, which is the tell that the activity has no workbook context.

The misconfiguration is discoverable in `Main.xaml`: the `ExcelLookUpRange` is
not wrapped in any Excel scope.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Lookup Range` placed outside any Excel scope |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-null-reference.md`
- Agent identified that the `Lookup Range` is outside any Excel scope (no
  workbook context), found in `Main.xaml`, as the cause of the
  `NullReferenceException`, and recommended wrapping it in an
  `Excel Application Scope` (or `Use Excel File`)
