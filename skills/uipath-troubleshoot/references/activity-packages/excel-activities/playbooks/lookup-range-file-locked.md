---
confidence: medium
---

# Lookup Range — Workbook Locked / File In Use

## Context

What this looks like:
- Activity `Lookup Range` (`UiPath.Excel.Activities.ExcelLookUpRange` / `LookUpRangeX`) — or the surrounding `Excel Application Scope` / `Use Excel File` — faults when it tries to open or read the workbook
- Error message contains one of: `The process cannot access the file '<path>' because it is being used by another process`, `The file '<name>' is locked for editing by '<user>'`, `IOException`, or a COM `0x800A03EC`/`RPC` error that resolves to a busy/locked workbook
- The failure is often intermittent — the workflow succeeds when no one has the file open and fails when the file is held

What can cause it:
- The workbook is **held open by another process**: a user has it open interactively on the host, a previous job or a crashed debug run left an `EXCEL.EXE` instance holding the handle, another concurrent job is reading/writing the same file, or an antivirus/indexer/sync client (OneDrive, backup agent) has a transient lock.
- Excel cannot acquire the read/write handle it needs, so the open faults before the lookup runs.

Notes:
- This is distinct from the modern-surface COM dispatcher failure (`0x80010100 RPC_E_SYS_CALL_FAILED`) documented in [invoke-vba-com-interop-failure.md](./invoke-vba-com-interop-failure.md): that one is a *blocked/hung* Excel call, this one is a *file handle* contention. If the message names the **file** being in use, apply this playbook; if it names a COM system-call HRESULT during a macro, apply the COM-interop one.
- An orphaned `EXCEL.EXE` from a prior run is the most common unattended cause — the file looks closed to a human but the handle is still held by a windowless process.

## Investigation

1. Read the workflow `.xaml`: capture the workbook path the `Excel Application Scope` / `Use Excel File` opens, and confirm the faulted activity is the `Lookup Range` (or the scope wrapping it).
2. Confirm the error names the **file** as being used by another process (vs. a COM/HRESULT signature — that routes to the COM-interop playbook).
3. Ask the user (or someone with host access, as the robot's Windows user) to check:
   - Whether the workbook is open interactively on the robot host.
   - Whether orphaned `EXCEL.EXE` processes exist (Task Manager, or `Get-Process EXCEL` in PowerShell) with no visible window.
   - Whether another job/schedule touches the same workbook path in an overlapping window.
   - Whether a sync client (OneDrive/SharePoint) or backup/AV agent holds the path.

## Resolution

- **If an orphaned `EXCEL.EXE` is holding the file** — make every Excel automation close cleanly and kill strays:
  1. Wrap the lookup in an `Excel Application Scope` (classic) or `Use Excel File` / `Excel Process Scope` (modern) so the scope's dispose always releases the handle. Ensure no `Try/Catch` swallows the scope exit.
  2. Add a **Kill Process** activity targeting `EXCEL` at the **start** of the workflow to force-close stray background instances before opening the file. (On the modern surface, the `Excel Process Scope`'s `KillExcelProcessesEachIteration` does this for you.)
  - **Who:** RPA developer
- **If a user or another job holds the file** — serialize access: schedule the workflow when the file is not open interactively, dedicate the host to unattended runs, or stagger the conflicting jobs so they do not touch the same workbook concurrently.
- **If a sync/backup/AV client holds the path** — move the workbook out of the synced/scanned folder, or exclude it from the sync/scan, so the handle is not transiently locked during the run.
- **If the file is genuinely shared and must stay open** — open it read-only where the activity supports it, or copy the workbook to a private working path at the start of the run and look up against the copy.
