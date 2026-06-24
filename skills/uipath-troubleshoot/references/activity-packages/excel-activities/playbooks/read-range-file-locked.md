---
confidence: medium
---

# Read Range — File In Use By Another Process

## Context

A `UiPath.Excel.Activities` activity that opens a workbook (Read Range and the rest of the read/write family, plus the surrounding `Excel Application Scope` / `Use Excel File` scope) fails because another process is holding an exclusive lock on the workbook file. The activity cannot acquire the file and faults before any sheet or range parsing happens.

What this looks like:
- Activity fails with `System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` The error wording is the .NET IO message — the activity passes it through with minimal wrapping.
- Under Excel COM (Excel Application Scope or `Use Excel File` falling back to COM), the surface may also be `System.Runtime.InteropServices.COMException` with HRESULT `0x800A03EC` and Excel's own message about the file being locked for editing. Same root cause, different wrapper.
- The path in the error is the workbook the activity was configured to open.
- May be intermittent (the locker releases the file between job attempts and retries succeed) or persistent (a stuck process holds the lock indefinitely).
- No sheet name, range address, or cell value appears in the error — failure happens at file acquisition, before parsing.

What can cause it (cause-branches — pick the right one from evidence):

1. **User opened the workbook in Excel UI** — A human is editing the workbook in Microsoft Excel on the same host (or, for a network share, on any host that has the file open). Excel takes an exclusive write lock by default. Common on developer workstations and shared automation hosts.
2. **Orphan `EXCEL.EXE` from a prior job** — A previous job left an `EXCEL.EXE` process running (typically because an `Excel Application Scope` was bypassed with `Continue On Error`, the workflow threw inside the scope without proper cleanup, or the executor was killed mid-run). The orphan still owns the file lock under the Robot's session. Symptom: file is locked but no human is using it; `EXCEL.EXE` appears in `tasklist` with no visible UI.
3. **Network-share lock from a different host** — Workbook lives on a UNC path or mapped network drive, and another machine (a developer's workstation, a different Robot host, a SharePoint sync agent, an indexer) is holding the lock. Local host shows no `EXCEL.EXE`; lock is held elsewhere.
4. **Concurrent Robot jobs racing on the same workbook** — Two or more jobs scheduled against the same workbook ran simultaneously; the first one's `Excel Application Scope` / `Use Excel File` is still open when the second one tries to acquire. Common pattern: triggers fire on overlapping schedules, or a queue dispatcher started multiple performers without per-workbook serialization.
5. **Antivirus / EDR / indexer holding the file** — Defender, a third-party AV, Windows Search Indexer, OneDrive / SharePoint sync client, or a backup agent transiently opens the workbook for scanning. Lock is brief (seconds) but races with the activity's open call. Intermittent failures without any visible Excel instance are the fingerprint.
6. **Hidden Excel instance owned by a different user session** — Excel was launched under a different Windows session (e.g., an admin RDP'd in earlier and left Excel running; a service account left an instance open under fast user switching). Task Manager shows `EXCEL.EXE` under "Users" → another session, not the current one.

What to look for:
- **The exact path in the error** — confirms the workbook the activity tried to open. Don't assume it matches the configured property — variable expressions may have resolved differently.
- **`EXCEL.EXE` presence on the host at failure time** — strongest single signal. If present under the Robot user → branch 2 or 4. If present under a human user → branch 1. If absent locally but the file is on a UNC → branch 3 or 5.
- **Lock owner across all sessions** — `handle.exe -a <path>` (Sysinternals) names the exact process and PID holding the file. Authoritative when available.
- **Pattern across recent runs** — every run fails immediately → branch 2 or 4 (persistent holder). Intermittent, no pattern → branch 5 (transient scanner). Fails only during business hours → branch 1 (human editor).
- **Workflow source** — look for `Continue On Error: True` on the surrounding `Excel Application Scope`, or a `Try Catch` that swallows scope exceptions. Either makes branch 2 (orphans) likely.
- **Trigger / schedule configuration** — overlapping schedules or unbounded queue performers point at branch 4.

## Investigation

Go in this order — cheaper checks first.

1. **Confirm the activity and the path.** From the workflow source (and from `uip or jobs get <job-key> --output json` → `Info`), capture: the activity class (Read Range / Write Range / etc.), the scope it runs inside (`Excel Application Scope` vs. `Use Excel File`), the configured workbook path expression, and the resolved path from the error string. Mismatch between expected and resolved path is itself a finding (different scope cause, not this playbook).

2. **Get the failing job and host.** `uip or jobs get <job-key> --output json` to capture `HostMachineName`, `RobotName`, `StartTime`, `EndTime`. The host is where the lock check has to run.

3. **Check recent jobs on the same host / workbook.** `uip or jobs list --folder-path '<folder>' --process-name '<process>' --limit 20 --output json`:
   - All recent runs on this host fail with the same IO exception → persistent holder (branches 2, 3, or a stuck branch 1). Skip to step 5.
   - Mixed pass/fail with no pattern → likely branch 5 (transient scanner). Continue to step 4 but expect a clean snapshot.
   - Failures clustered in business hours, passes outside → branch 1.
   - Two or more jobs against the same workbook with overlapping `StartTime` / `EndTime` windows → branch 4.

4. **Pattern: jobs that ran or scheduled around the failure window.** `uip or jobs list --folder-path '<folder>' --created-after <EndTime-10min> --created-before <EndTime+1min> --output json`. Look for sibling jobs that touch the same workbook — those are branch-4 candidates.

5. **Host-side process snapshot.** On the host (or have the user run it the next time the failure occurs):
   ```powershell
   Get-Process EXCEL -ErrorAction SilentlyContinue |
     Select-Object Id, SessionId, UserName, StartTime, MainWindowTitle
   ```
   - No `EXCEL.EXE` rows → branch 3 (lock is remote) or branch 5 (transient, already gone). Go to step 6.
   - One or more `EXCEL.EXE` under the Robot user (same `SessionId` as the failing job's session, no `MainWindowTitle`) → **branch 2** (orphan).
   - One or more `EXCEL.EXE` under a human user / different `SessionId` → **branch 1** (user editing) or **branch 6** (other session).
   - Multiple `EXCEL.EXE` under the Robot user across overlapping `StartTime`s → branch 4 (concurrent jobs).

6. **Exact lock owner (most authoritative).** If Sysinternals `handle.exe` is available on the host:
   ```powershell
   handle.exe -a '<workbook-path>'
   ```
   Names the exact PID and process holding the lock — including non-Excel processes (AV scanner, backup agent, OneDrive). Cross-reference the PID against `Get-Process` from step 5.
   - Holder is `EXCEL.EXE` → confirmed branch 1, 2, or 6 per step 5.
   - Holder is a scanner / sync / backup process → **branch 5**.
   - Holder is on a different machine (network share) → handle.exe will not name it; go to step 7.

7. **Network-share lock investigation (branch 3).** If the workbook is on a UNC path and the local host shows no holder:
   - On the file server (if accessible): `Get-SmbOpenFile | Where-Object { $_.Path -like '*<workbook>*' }` (Windows file server) names the client machine and user holding the file.
   - On a Linux/Samba server: `smbstatus --locks` or check the share's lock file.
   - If the share is SharePoint via OneDrive sync: the local host's OneDrive client may be syncing the file; check `tasklist | findstr OneDrive` and the OneDrive activity log.

8. **Cross-check workflow source for orphan-prone patterns (branch 2 confirmation).** Open the source:
   - Is the failing scope `Excel Application Scope` with `Continue On Error: True`? That swallows scope-internal exceptions and may leave `EXCEL.EXE` running.
   - Is there a `Try Catch` wrapping the scope where the `Catch` does not re-throw or close the scope?
   - Is `Visible: True` set on the scope? Visible Excel instances are more likely to be left stranded after an executor crash.
   - These together raise branch-2 confidence even after a one-off kill — the next run will produce a new orphan unless the workflow is fixed.

The root cause is **which process holds the lock and why**. A confirmed finding names the holder (process name, PID, owning user / session / host) and one of the cause-branches.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — User has the workbook open in Excel UI:**
  - On the host, close Excel (the human user closes the document, or coordinate a maintenance window).
  - Prevention: do not edit production workbooks on automation hosts; move source-of-truth data files off shared automation hosts; for shared workbooks, use SharePoint / OneDrive with the `o365-activities` cloud surface instead of the desktop file.

- **Branch 2 — Orphan `EXCEL.EXE` under the Robot user:**
  - One-off kill (host, as the Robot user or admin):
    ```powershell
    Get-Process EXCEL | Where-Object { $_.SessionId -eq <robot-session-id> } | Stop-Process -Force
    ```
    Confirm the file is no longer locked (`handle.exe -a <path>` returns no holder) before re-running.
  - Permanent fix: address the workflow pattern that produced the orphan:
    - Remove `Continue On Error: True` from `Excel Application Scope`. Let the exception propagate so cleanup runs.
    - In any `Try Catch` wrapping the scope, the `Catch` must dispose the scope or re-throw; do not silently suppress.
    - Prefer `Use Excel File` over `Excel Application Scope` when the workbook does not require Excel-COM-only features — its disposal semantics are more robust.
    - Set `Visible: False` on `Excel Application Scope` unless you are debugging interactively. Visible instances are harder to clean up after an abrupt executor exit.
  - For chronic orphans on a host, add a startup task or a pre-job activity that kills stale `EXCEL.EXE` owned by the Robot user before the workflow begins.

- **Branch 3 — Network-share lock from a different host:**
  - Identify the locking host / user via `Get-SmbOpenFile` (Windows file server) or `smbstatus` (Samba). Coordinate with that user to close the file.
  - As a tactical unlock on Windows file server: `Close-SmbOpenFile -FileId <id>` (administrator on the file server). Note this terminates the remote handle without giving the user a chance to save — confirm intent first.
  - Prevention: move the workbook off a shared network path, or fence access to it with a check-out workflow (queue item per workbook, lock asset, or sentinel file). For SharePoint document libraries, switch to the `o365-activities` surface so file acquisition goes through Graph instead of an SMB lock.

- **Branch 4 — Concurrent Robot jobs on the same workbook:**
  - Serialize the jobs. Options:
    - Switch the process to single-instance via a per-workbook lock asset (`uip or assets create lock-<workbook> ...`) acquired at job start and released at end. Workflow checks the asset and waits or fails fast.
    - Use a queue with a single performer (concurrency 1) so two jobs cannot run together.
    - Stagger triggers so schedules do not overlap.
  - Verify by inspecting the triggers / schedule: `uip or triggers list --folder-path '<folder>' --output json` and confirm no two triggers fire the same process within the workbook's expected runtime window.

- **Branch 5 — Antivirus / EDR / indexer / sync client:**
  - Identify the holder via `handle.exe -a <path>` at failure time (the holder is transient — must capture during the lock window).
  - Allowlist the workbook's directory in the AV/EDR product (Defender: add an exclusion for the folder; vendor-specific elsewhere).
  - Stop Windows Search from indexing the automation data folder: Indexing Options → Modify → uncheck the folder.
  - For OneDrive / SharePoint sync clients on automation hosts: either un-sync the folder (preferred — automation hosts should not run sync clients) or use Files-On-Demand and ensure files are downloaded before the job runs.
  - Add a retry-on-`IOException` wrapper as a defensive measure (Retry Scope with 3 attempts, 5-second back-off) — masks transient scanner races without papering over a real holder.

- **Branch 6 — Hidden Excel instance under a different user session:**
  - Identify the session: `quser` on the host shows all active and disconnected sessions; the `Get-Process EXCEL` output from investigation step 5 names the session ID.
  - If the session is a disconnected RDP from an admin: log it off (`logoff <session-id>`) after confirming with the session owner. The disconnected session's Excel goes with it.
  - Prevention: dedicate automation hosts to the Robot; humans should not RDP in for ad-hoc work, and when they must, they should sign out (not disconnect) when done.

## Prevention (cross-branch)

- Do not store production workbooks on hosts where humans actively edit Excel. Either move the workbook off the automation host, or move the editing workflow off it.
- Prefer `Use Excel File` over `Excel Application Scope` for new workflows. Disposal is more robust; OpenXML provider sidesteps Excel COM entirely when the workbook does not require COM-only features.
- Never set `Continue On Error: True` on an Excel scope. If the scope fails, fail the workflow — orphan `EXCEL.EXE` is worse than a single failed run.
- Set `Visible: False` on `Excel Application Scope` in production. Reserve `Visible: True` for interactive debugging.
- For workbooks that multiple processes legitimately need to touch, serialize via a per-workbook lock asset, single-performer queue, or sentinel file. Do not rely on Excel's own lock to coordinate — its error surface is too noisy.
- Allowlist the automation data folder in AV/EDR; exclude it from Windows Search indexing; do not run OneDrive / SharePoint sync clients on automation hosts.
- For long-running automation hosts, add a pre-job cleanup step that terminates stale `EXCEL.EXE` owned by the Robot user before the workflow begins. Cheap, idempotent, and prevents branch-2 chains from cascading across runs.

## Related

- Other Excel Read Range failure fingerprints (sheet not found, file not found, null-reference on formatted files) are separate playbooks — see [`../summary.md`](../summary.md).
- If the executor was killed mid-Excel-scope (and the orphan is the consequence rather than the cause), inspect the surrounding job's exit code via `uip or jobs get <key> --output json` — an executor-termination exit code on the parent job points at job-level investigation, not Excel.
- For shared / cloud Excel workbooks accessed via Microsoft Graph rather than the local filesystem, see [`o365-activities/overview.md`](../../o365-activities/overview.md).
