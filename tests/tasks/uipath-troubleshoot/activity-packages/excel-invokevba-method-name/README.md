# Invoke VBA Failure - Entry Method Name Typo

This scenario reproduces a runtime `Invoke VBA` failure caused by an
`EntryMethodName` typo in the workflow XAML. `Application.Run` cannot
resolve the typo'd name against the correctly-spelled `Sub` in the
external code file.

## What this scenario uncovers

**Root Cause:** The `Invoke VBA` activity in `Main.xaml` sets
`EntryMethodName="ProcessInvoces"` (missing an "i"). The external code
file `macro.txt` declares `Sub ProcessInvoices()` (correctly spelled).
`Application.Run` looks up the name verbatim against the injected
module and finds no match, so the activity faults with `Cannot run the
macro 'ProcessInvoces'. The macro may not be available in this
workbook`.

This maps to:
`references/activity-packages/excel-activities/playbooks/invoke-vba-entry-method-name.md`
(specifically the "typo or whitespace mismatch" branch).

The user is framed as **on the project source**, so the agent has both
`Main.xaml` (with the typo'd `EntryMethodName`) and `macro.txt` (with
the correctly-spelled Sub) directly Read-able. This mirrors the existing
`getasset-name-mismatch` scenario's typo-near-miss pattern.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/Main.xaml` + `process/macro.txt` | hand-authored UiPath project with a typo'd `EntryMethodName` and a correctly-spelled Sub |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-vba-entry-method-name.md`
- Agent named the typo explicitly (`ProcessInvoces` vs
  `ProcessInvoices`), not just "macro name doesn't match"
