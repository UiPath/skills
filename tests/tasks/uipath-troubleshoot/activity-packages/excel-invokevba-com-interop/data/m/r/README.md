# Invoke VBA Failure - COM Interop HRESULT 0x80010100

This scenario reproduces a runtime `Invoke VBA` failure caused by a COM
interop instability: a hidden modal dialog on Excel (Protected View
bar from Mark-of-the-Web) blocks the COM call into the workbook, while
the surrounding Excel Process Scope ran with `ShowExcel=False`. The
COM layer surfaces the wedge as
`The system call failed. (Exception from HRESULT: 0x80010100
(RPC_E_SYS_CALL_FAILED))`.

## What this scenario uncovers

**Root Cause:** The Excel Process Scope in `Main.xaml` runs with
`ShowExcel="False"`. When the workbook opens, a hidden Protected View
bar (from a Mark-of-the-Web on the downloaded `.xlsx`) blocks every
COM call into the workbook. The Invoke VBA activity's call into the
workbook's VBProject times out and the COM layer raises
`0x80010100 RPC_E_SYS_CALL_FAILED`. The same workbook + macro pair
runs cleanly once the Protected View bar is dismissed and the file is
unblocked.

This maps to:
`references/activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md`
(specifically the "modal dialog was blocking" branch).

The user is framed as **off-host**, so the correct agent behavior is
to recommend the host-side check list (Visible=True, dialog
inspection, orphaned EXCEL.EXE, Office install) rather than try
commands itself.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with `ShowExcel="False"` on the Excel Process Scope |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-vba-com-interop-failure.md`
- Agent recommended setting `ShowExcel`/`Visible` to True on the Excel
  Process Scope to surface the hidden dialog, and listed the other
  host-side checks (Protected View / Mark-of-the-Web, orphaned
  EXCEL.EXE, multi-Office hosts) without fabricating host commands it
  could not run
