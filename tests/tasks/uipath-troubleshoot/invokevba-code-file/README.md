# Invoke VBA Failure - Code File Missing Sub/Function Wrapper

This scenario reproduces a runtime `Invoke VBA` failure caused by the
external code file at `CodeFilePath` containing **bare VBA statements at
the top level** (no `Sub` or `Function` wrapper). The VBA compiler
rejects the injected module before any macro logic runs.

## What this scenario uncovers

**Root Cause:** `macro.txt` in the project contains bare executable
statements (`ActiveWorkbook.RefreshAll`, `Application.Calculate`) at the
module level, with no `Sub RefreshSheets()` / `End Sub` block around
them. `Invoke VBA` injects the file as a module body; the VBA compiler
expects only procedure declarations at the module level, so the
injection compile-fails with `Expected: Sub, Function, Property, or
Type`.

This maps to:
`references/activity-packages/excel-activities/playbooks/invoke-vba-code-file-path.md`
(specifically the "Code not wrapped in a Sub/Function" branch).

The user is framed as **on the project source**, so the agent has both
`Main.xaml` (the workflow + `CodeFilePath` reference) and `macro.txt`
(the broken source) directly Read-able.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/Main.xaml` + `process/macro.txt` | hand-authored UiPath project with an Excel Process Scope + Invoke VBA referencing a `CodeFilePath` whose contents are deliberately missing the `Sub` wrapper |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-vba-code-file-path.md`
- Agent named the missing `Sub`/`Function` wrapper in `macro.txt` and
  recommended wrapping the contents in a `Sub RefreshSheets()` block
  matching the activity's `EntryMethodName`
