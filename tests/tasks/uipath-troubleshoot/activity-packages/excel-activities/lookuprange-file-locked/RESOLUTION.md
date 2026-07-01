# Final Resolution

---

**Root Cause:** The classic `Lookup Range` activity in `Main.xaml` runs
inside an `Excel Application Scope`, which must open the workbook
`Invoices.xlsx` before it can search it. On MOCK-HOST the file is held
open by another process, so the scope cannot acquire the read/write
handle and faults at open with
`System.IO.IOException: The process cannot access the file
'C:\ProgramData\Automation\Invoices.xlsx' because it is being used by
another process` - before any cell is read. The most likely holder on an
unattended robot is an **orphaned `EXCEL.EXE`** left behind by a prior run
that did not dispose its Excel instance.

**What went wrong:** The `InvoiceLookup` job (started
2026-05-27T07:45:11Z) faulted ~3 seconds in, while the
`Excel Application Scope` was opening the workbook. The runtime error was
the IOException above. The failure is intermittent - runs succeed when no
stale handle is present and fault when one is - which is the signature of
file-handle contention rather than a defect in the lookup logic.

**Why:** A classic `Excel Application Scope` opens the workbook through
Excel Interop and needs an exclusive (or at least non-conflicting) file
handle. If a previous unattended run crashed or exited without disposing
its `Excel.Application`, a windowless `EXCEL.EXE` keeps the handle open;
the file then appears closed to a human but is still locked. A user with
it open interactively, a concurrent job touching the same path, or a
sync/backup/AV client transiently holding the file produce the same
IOException.

This is **not** the modern-surface COM dispatcher fault
(`0x80010100 RPC_E_SYS_CALL_FAILED`), which is a blocked/hung Excel call.
The error here names the **file** as in use, so it routes to the
file-locked playbook, not the COM-interop one.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceLookup -- Faulted at 2026-05-27T07:45:14.530Z (ran for ~3.3 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: RPA Production (key `b2c9d4e7-3a8f-4b1d-9e5c-7f0a2b3c4d5e`)
- Final error: `System.IO.IOException: The process cannot access the file 'C:\ProgramData\Automation\Invoices.xlsx' because it is being used by another process` -> `Main.xaml` -> `ExcelApplicationScope "Excel Application Scope"` -> `Sequence "Main Sequence"`
- Log ordering: "Opening workbook ..." then the IOException - the fault is at scope open, before the `Lookup Range` body runs.

### Excel Activities (Root Cause)
- Activity surface: classic `UiPath.Excel.Activities.ExcelLookUpRange` inside `UiPath.Excel.Activities.ExcelApplicationScope` (Interop / COM)
- The exception is a file-handle conflict (`IOException` / "being used by another process"), not a COM HRESULT - the workbook cannot be opened because something else holds it.
- Intermittent success/failure across runs corroborates a stale/contended handle (most likely an orphaned `EXCEL.EXE` on the unattended host) rather than a bad sheet/range or lookup value.

---

**Immediate fix:**

The agent could not enumerate host processes from Orchestrator alone.
Hand the user a host check plus the developer fix.

### Host check (RPA Production / MOCK-HOST, as the robot's Windows user)
1. Check whether `Invoices.xlsx` is open interactively on the host.
2. Look for orphaned `EXCEL.EXE` processes with no visible window:
   Task Manager, or `Get-Process EXCEL` in PowerShell. Expect one or more
   stray instances - that confirms the cause.
3. Check whether another job/schedule touches the same workbook path in an
   overlapping window, and whether a sync client (OneDrive/SharePoint) or a
   backup/AV agent holds the path.

### Fix path A -- force a clean release (most common: orphaned EXCEL.EXE)
1. Wrap the lookup in an `Excel Application Scope` (already present) and
   ensure no `Try/Catch` swallows the scope exit, so its dispose always
   releases the handle.
2. Add a **Kill Process** activity targeting `EXCEL` at the **start** of
   the workflow to force-close stray background instances before opening
   the file. (On the modern surface, `Excel Process Scope`'s
   `KillExcelProcessesEachIteration` does this automatically.)
- **Who:** RPA developer
- **Source:** `excel-activities/playbooks/lookup-range-file-locked.md`

### Fix path B -- serialize or relocate access
- If a user or another job legitimately holds the file: schedule the run
  when the file is not open, dedicate the host to unattended runs, or
  stagger conflicting jobs so they do not touch the workbook concurrently.
- If a sync/backup/AV client holds the path: move the workbook out of the
  synced/scanned folder, or exclude it from the sync/scan.
- If the file must stay open elsewhere: open it read-only where the
  activity supports it, or copy it to a private working path at the start
  of the run and look up against the copy.
- **Source:** same playbook.

---

**Preventive fix:**

1. **Studio** -- every Excel automation must close cleanly: keep the
   `Excel Application Scope` dispose on the success and failure paths, and
   add a startup `Kill Process` (EXCEL) so a prior run's stray instance
   cannot lock the next run.
   - **Why:** orphaned `EXCEL.EXE` from a crashed/aborted unattended run is
     the most common cause of "file in use" on robot hosts.
   - **Who:** RPA developer.

2. **Platform / robot host** -- keep automation workbooks out of
   user-synced or AV-scanned folders, and avoid scheduling two jobs against
   the same workbook in overlapping windows.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The workbook is held open by another process on MOCK-HOST (most likely an orphaned EXCEL.EXE from a prior undisposed run); the Excel Application Scope cannot acquire the file handle and faults at open | High | Confirmed | Yes | `IOException` "being used by another process" naming `Invoices.xlsx` at scope open + intermittent success/failure across runs | Kill stray EXCEL.EXE at workflow start + clean scope dispose; or serialize/relocate access |

---

Would you like help editing `Main.xaml` to add a `Kill Process` (EXCEL)
step at the start and verify the scope disposes cleanly, or cleaning up the
`.local/investigations/` folder?
