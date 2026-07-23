# Invoke VBA Failure - Parameter Arity Mismatch

This scenario reproduces a runtime `Invoke VBA` failure caused by a
mismatch between the macro's signature in `macro.txt` and the
`EntryMethodParameters` array passed by `Main.xaml`. The Sub requires
two arguments but the workflow passes only one.

## What this scenario uncovers

**Root Cause:** `macro.txt` declares
`Sub PostRow(amount As Double, vendor As String)` with two required
parameters. The Invoke VBA activity in `Main.xaml` passes
`new Object[] { 125.50 }` - a one-element array. `Application.Run`
rejects the arity mismatch with `Wrong number of arguments or invalid
property assignment`.

This maps to:
`references/activity-packages/excel-activities/playbooks/invoke-vba-parameter-formatting.md`
(specifically the "arity mismatch" branch).

The user is framed as **on the project source**, so the agent has both
`Main.xaml` (the parameter expression) and `macro.txt` (the Sub
signature) directly Read-able.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/Main.xaml` + `process/macro.txt` | hand-authored UiPath project with a 1-arg parameter array against a 2-arg Sub signature |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-vba-parameter-formatting.md`
- Agent named the arity mismatch (2 required parameters in the Sub vs
  1-element array in the XAML) and recommended passing a 2-element
  array
