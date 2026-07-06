# Final Resolution

---

**Outcome:** The `uip` CLI evidence is **insufficient** to identify
which cause-branch of the
`activity-packages/excel-activities/playbooks/read-range-file-locked.md`
playbook applies. The agent's correct action is to surface a host-
side investigation recommendation to the user, NOT to guess a branch.

**What the CLI evidence does establish:**

- Failing job `ee555555-6666-7777-8888-99990000aaaa` faulted at
  `2026-05-19T08:00:01.812Z` with the verbatim file-acquisition
  signature: `System.IO.IOException: The process cannot access the
  file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used
  by another process.`
- The fingerprint matches the read-range-file-locked playbook
  exactly.

**What the CLI evidence RULES OUT:**

- **Branch 4 (concurrent Robot jobs):** `or jobs list --folder-key
  ... --process-name ExcelDailyImport` returns only this single
  faulted job in the surrounding window. No overlapping siblings.
  `or triggers list` shows a single trigger (`HourlySalesA`) on a
  non-overlapping cron.
- **Branch 2 (orphan from prior job):** No prior faulted run of the
  same process in the recent window. Workflow source
  (`process/Main.xaml`) is clean — `Use Excel File` scope (not the
  legacy COM-based Excel Application Scope), no `ContinueOnError`
  set anywhere, no swallowing TryCatch wrapper. The workflow itself
  is not orphan-prone.

**What the CLI evidence CANNOT determine:**

- Whether a human has the workbook open in Excel UI on the host
  (branch 1).
- Whether a disconnected RDP session under a different Windows user
  holds an Excel instance with the file open (branch 6).
- Whether the workbook is being held by an antivirus scanner, an
  EDR product, Windows Search, OneDrive / SharePoint sync, or a
  backup agent (branch 5).
- Whether the workbook is on a network share and another machine
  holds the lock (branch 3) — the workbook path here is local
  (`C:\Robot\Data\`), so this branch is unlikely but not formally
  ruled out by the CLI alone.

Orchestrator's `uip` surface cannot enumerate host-side processes,
SMB lock holders, or AV/EDR handles. The agent must escalate to
host-side commands.

---

**Recommended Fix (Resolution):**

Ask the user to capture host-side evidence on `MOCK-HOST` at the
next failure, then re-run the investigation with the new data:

1. **Find Excel processes on the host:**
   ```powershell
   Get-Process EXCEL -ErrorAction SilentlyContinue |
     Select-Object Id, SessionId, UserName, StartTime, MainWindowTitle
   ```
   - No rows → branches 3 (remote lock on a UNC share) or 5
     (transient scanner) are the remaining candidates.
   - Rows under the Robot user (`UIPATH\AUTOMATION1`) with no
     `MainWindowTitle` → branch 2 (orphan), but the workflow source
     evidence already weakened this hypothesis — investigate further.
   - Rows under a human user → branch 1 (user editing) or branch 6
     (cross-session disconnect).

2. **Name the exact lock holder (Sysinternals `handle.exe`):**
   ```powershell
   handle.exe -a 'C:\Robot\Data\sales-2026-05.xlsx'
   ```
   - Names PID and process. If the holder is not `EXCEL.EXE`, it's
     branch 5 (scanner). If a different machine holds it, the
     command will return nothing locally — branch 3.

3. **If the workbook is on a UNC path (not in this scenario, but
   useful to confirm),** on the file server:
   ```powershell
   Get-SmbOpenFile | Where-Object { $_.Path -like '*sales-2026-05.xlsx*' }
   ```

Once the host-side evidence is captured, re-triage with the new
data. The branch will be identifiable. Apply the matching resolution
from the playbook's `## Resolution` section once the branch is
confirmed.

**Anti-pattern to avoid:** Confidently picking one of the host-side
branches (branch 1 / 5 / 6) without evidence. The CLI evidence does
not distinguish them; recommending the WRONG fix wastes operator
time and erodes trust.
