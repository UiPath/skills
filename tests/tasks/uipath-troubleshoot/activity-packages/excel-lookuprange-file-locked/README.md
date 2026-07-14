# Lookup Range Failure - Workbook Locked / File In Use

This scenario reproduces a classic `Lookup Range` failure caused by the
**workbook being held open by another process** on the robot host. The
surrounding `Excel Application Scope` cannot acquire the file handle and
faults at open with `System.IO.IOException: The process cannot access the
file '<path>' because it is being used by another process` - before any
cell is read.

## What this scenario uncovers

**Root Cause:** The workbook is locked by another process on MOCK-HOST -
most often an **orphaned `EXCEL.EXE`** left behind by a prior unattended
run that did not dispose its Excel instance. The file looks closed to a
human but the handle is still held by a windowless process, so the next
run's `Excel Application Scope` cannot open it. The intermittent pattern
("some runs succeed, others fault") is the signature of handle contention,
not a workflow defect.

This maps to:
`references/activity-packages/excel-activities/playbooks/lookup-range-file-locked.md`

It is **distinct** from the modern-surface COM dispatcher fault
(`0x80010100 RPC_E_SYS_CALL_FAILED`): that one is a *blocked/hung* Excel
call; this one is *file-handle* contention. The error names the **file**
as in use, which routes here rather than to the COM-interop playbook.

The user is framed as **off-host**, so the correct agent behavior is to
tie the IOException to a held file handle and hand over a host check list
(look for orphaned `EXCEL.EXE`, who/what holds the path) plus the fix - not
to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a classic `Excel Application Scope` + `Lookup Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `lookup-range-file-locked.md` (not the COM-interop playbook)
- Agent identified the workbook being held by another process (orphaned
  `EXCEL.EXE` the most likely unattended cause) and recommended forcing a
  clean release - e.g. a `Kill Process` (EXCEL) at workflow start plus a
  cleanly-disposed scope, or serializing access - without fabricating host
  actions
