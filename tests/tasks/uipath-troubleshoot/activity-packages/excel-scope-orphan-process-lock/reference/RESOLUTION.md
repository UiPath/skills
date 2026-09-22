# Final Resolution

---

**Root Cause:** The Classic `Excel Application Scope` could not open
`orders-inbound.xlsx` because the workbook is **locked by an orphan
`EXCEL.EXE`** (PID 7312) left running on the host. That orphan was
created by a PRIOR job, `gg5550000-...` (also `ExcelOrderImport`),
which faulted mid-scope at `2026-05-29T22:04:11` when its Robot session
was force-terminated; the `EXCEL.EXE` it had spun up was never closed
and still holds an exclusive handle on the workbook. The current job's
scope therefore fails at file acquisition with
`UiPath.Excel.BusinessException: Failed opening the Excel file.
Possible reasons: file is corrupt, already used by another process or
password protected.` (inner `COMException 0x800A03EC` — "Microsoft
Excel cannot access the file … in use by another program").

> **Of the three reasons the message lists, only one applies.** The
> file is NOT corrupt (it opens read-only from a copy) and NOT password
> protected — the decisive log line says so explicitly. The cause is
> "already used by another process," and that process is a Robot-owned
> orphan `EXCEL.EXE`, not a logged-in user's Excel.

**What went wrong:** Failing job
`aa555555-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T06:00:02.300Z`. The `Excel Application Scope:
orders-inbound.xlsx` activity tried to acquire the workbook via Excel
COM, found it locked by `EXCEL.EXE` PID 7312 (session 0, no main
window — an orphan owned by the Robot's session), and surfaced the
"Failed opening the Excel file" BusinessException.

**Why:** When a Classic `Excel Application Scope` doesn't close
cleanly — here because the prior job's session was force-terminated
mid-scope — the underlying `EXCEL.EXE` can be orphaned with the
workbook still open. The orphan holds an exclusive lock, so the next
job that targets the same file can't open it. The failure is a
downstream symptom of the prior crash, not of anything wrong with the
workbook or the current workflow's logic.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelOrderImport` (key `aa555555-...`) — Faulted at
  `2026-05-30T06:00:09.870Z`.
- Folder: `OrderImports` (key `f00fffff-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: Failed opening the Excel file.
  Possible reasons: file is corrupt, already used by another process
  or password protected.` with inner
  `System.Runtime.InteropServices.COMException (0x800A03EC): Microsoft
  Excel cannot access the file 'C:\Robot\Data\orders-inbound.xlsx'.
  … the file is being used by another program …`.
- Faulting activity: `ExcelApplicationScope_1`
  (`Excel Application Scope: orders-inbound.xlsx`) at `Main.xaml`.
- The `or jobs list --state Faulted` response also shows the PRIOR
  faulted run `gg5550000-...` at `2026-05-29T22:04` with a
  `COMException: The RPC server is unavailable. (Robot session
  force-terminated mid-scope.)` — the origin of the orphan.

### Job logs (decisive)
- `Excel Application Scope: orders-inbound.xlsx — surface: Classic ExcelApplicationScope (COM-only). Acquiring workbook via Excel COM.`
- `Excel Application Scope: orders-inbound.xlsx — workbook open failed: target file is locked. ... Lock holder: EXCEL.EXE PID 7312, session 0 (Robot session UIPATH\AUTOMATION1), NO main window — orphan instance (not a logged-in user's Excel). Orphan originated from job gg5550000-... (Faulted 2026-05-29T22:04:11 mid-scope; the Robot session was force-terminated and EXCEL.EXE was left running, still holding the workbook handle). The file itself is well-formed (opens read-only from a copy) and is not password protected.`
- `Excel Application Scope: orders-inbound.xlsx — UiPath.Excel.BusinessException: Failed opening the Excel file. ... Inner: COMException 0x800A03EC (Microsoft Excel cannot access the file; in use by another process).`

The decisive log line names the exact lock holder (orphan `EXCEL.EXE`
PID 7312, Robot session, no window) and its origin (the prior
force-terminated job), and explicitly rules out corruption and
password protection.

### Workflow source
- `Main.xaml` uses a SINGLE Classic `<uix:ExcelApplicationScope>`
  wrapping a `Read Range`. Nothing in the current workflow is wrong —
  the lock predates this run.
- `project.json`: `UiPath.Excel.Activities` `[2.24.7]`.

### Cross-check — what this is NOT
- NOT file corruption: the log states the file opens read-only from a
  copy; it is well-formed.
- NOT password protection: the log states it is not password
  protected.
- NOT "Excel not installed" / registration corruption: the scope got
  far enough to attempt the file open via COM, and the error is a file
  lock, not a COM acquisition fault.
- NOT a within-this-workflow multi-scope race: only one scope; the
  lock holder is a SEPARATE prior job's orphan.

---

**Recommended Fix (Resolution):**

This maps to branch 2 (workbook held by another EXCEL.EXE) of
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`.

### Immediate recovery — clear the orphan
1. On the host, confirm the orphan: `Get-Process EXCEL | Select-Object Id, SI, MainWindowTitle` — PID 7312, session 0, empty `MainWindowTitle`.
2. Terminate the orphan: `Stop-Process -Id 7312 -Force` (or end `EXCEL.EXE` PID 7312 in Task Manager). The lock releases and the next run can open the workbook.

### Durable fix — stop creating orphans, and guard the open
- **Guard against pre-existing orphans on a DEDICATED unattended host:**
  add a `Kill Process` activity (`ProcessName = "EXCEL"`) at the START
  of the workflow to clear any stray instances before the scope opens.
  **Only on a dedicated unattended Robot host** — never on a shared /
  attended machine, where it would kill a user's open workbooks.
- **Fix the root cause of the orphan:** orphans come from scopes that
  don't close cleanly. Avoid force-terminating jobs mid-scope; wrap
  multi-scope workflows in an `Excel Process Scope` so the EXCEL.EXE
  lifecycle is governed; ensure no child macro calls `Application.Quit`
  / `Workbooks.Close`.
- **If the workflow only reads:** set `ReadOnly = True` on the scope so
  a concurrently-open instance doesn't block acquisition as hard
  (defense in depth, not a substitute for clearing the orphan).

### Anti-patterns (do NOT use)
- Do NOT conclude the workbook is corrupt or password protected — the
  message lists those as POSSIBLE reasons, but the evidence rules them
  out. Acting on them (e.g., asking for the password, restoring from
  backup) wastes time.
- Do NOT add a bare `Try Catch` that swallows the error and continues —
  the import would silently process stale/empty data.
- Do NOT bake an unconditional `Kill Process EXCEL` into a workflow
  that runs on a SHARED / attended host — it destroys interactive
  users' open workbooks.
- Do NOT just add a `Delay` and hope the lock clears — an orphan does
  not exit on its own.

### Prevention
- Govern EXCEL.EXE lifecycle: `Excel Process Scope` for multi-scope
  flows, no macro-driven `Application.Quit`, and avoid force-killing
  jobs mid-scope.
- Add orphan-cleanup to the unattended host's job-startup routine (or
  a scheduled sweep) on dedicated hosts.
