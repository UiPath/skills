# Excel Application Scope — Workbook Locked by an Orphan EXCEL.EXE

This scenario reproduces a Classic `Excel Application Scope` failure
where the target workbook is locked by an **orphan `EXCEL.EXE`** that a
prior crashed job left running. The job ends with:

```
UiPath.Excel.BusinessException: Failed opening the Excel file. Possible reasons: file is corrupt, already used by another process or password protected.
```

(with inner `COMException 0x800A03EC` — "Microsoft Excel cannot access the file … in use by another program")

## What this scenario uncovers

**Root Cause:** A prior `ExcelOrderImport` job (`gg5550000-...`) faulted
mid-scope on 2026-05-29 when its Robot session was force-terminated,
leaving an `EXCEL.EXE` (PID 7312, session 0, no window) still holding
the workbook handle. The current job's Classic scope can't open the
file exclusively, so it throws "Failed opening the Excel file."

The fix is to clear the orphan (`Stop-Process` / Task Manager; or a
guarded `Kill Process EXCEL` at workflow start on a dedicated
unattended host) AND stop creating orphans (clean scope close, no
force-kill mid-scope, `Excel Process Scope` for multi-scope flows) —
**not** to treat the file as corrupt or password protected.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`
(branch 2 — workbook held by another EXCEL.EXE).

## The trap

The exception message lists THREE possible reasons — "file is corrupt,
already used by another process or password protected." Only the
middle one applies. The agent must use the log evidence (which
explicitly rules out corruption and password protection and names the
orphan process) rather than chasing the corrupt/password red herrings.

It must also scope its `Kill Process EXCEL` recommendation correctly:
valid recovery on a dedicated unattended host, dangerous on a
shared/attended one.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelOrderImport` — single Classic `<uix:ExcelApplicationScope>` wrapping a `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `jobs list` includes the prior force-terminated run, and `jobs logs` names the orphan `EXCEL.EXE` lock holder + its origin and rules out corruption/password |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

Expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` (sees this run + the prior crashed run) →
`jobs get` (Failed opening / inner `0x800A03EC` in-use) → `jobs logs`
(orphan `EXCEL.EXE` PID 7312 + originating crashed job; corruption and
password ruled out) → workflow source (single Classic scope) →
conclude branch 2.

> **Note on fixtures.** Synthetic. The PID, session id, and
> orphan-detection wording are placeholders. The test grades whether
> the agent identifies the orphan-process lock (NOT corruption /
> password), recommends clearing it + fixing the orphan source, and
> scopes the `Kill Process EXCEL` advice to dedicated unattended hosts.
