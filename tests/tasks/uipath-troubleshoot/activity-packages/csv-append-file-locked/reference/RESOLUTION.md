# Final Resolution

---

**Root Cause:** The target `daily.csv` is **locked by another process** — open in
Microsoft Excel on the robot host (or held by another session/job) — when the
`Append To CSV` activity runs. CSV append needs exclusive write access; the open
handle blocks it, so the activity faults with `System.IO.IOException: The process
cannot access the file because it is being used by another process`.

**What went wrong:** The `CsvDailyAppend` job (started 2026-06-13T09:30:41Z) read
the incoming rows, then faulted ~2 seconds later at `Append To CSV` to
`...\data\daily.csv` with the "being used by another process" IOException. The
user confirms colleagues sometimes leave `daily.csv` open in Excel — exactly the
lock that blocks the append.

**Why:** `Append To CSV` opens the target file for writing. Microsoft Excel
holds an exclusive lock on an open workbook, and Windows denies a second writer —
so any append while the file is open in Excel (or held by another job/iteration)
fails with the IOException. This is a file-access/lock problem, not a dependency
(`CsvHelper`) or data-shape (`DataTable`) issue.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvDailyAppend -- Faulted at 2026-06-13T09:30:43.470Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Daily Loads (key `ca020002-d4e5-4f60-8a02-000000000002`)
- Final error: `Append To CSV: The process cannot access the file '...\data\daily.csv' because it is being used by another process.` -> `Main.xaml` -> `AppendToCsvFile "Append To CSV"` (the Read CSV step succeeded first)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.AppendToCsvFile` (Append To CSV).
- The message is `System.IO.IOException ... being used by another process` — the file-lock signature, naming the exact `daily.csv` path.
- The Read CSV of the incoming file succeeded; only the write/append to the locked target failed. The user reports the CSV is sometimes open in Excel.

---

**Immediate fix:**

Free the target file before the append, and prevent concurrent holders.

### Fix path A -- ensure the file is not open / kill Excel (preferred)
Make sure `daily.csv` is not open in Excel when the job runs. For robustness, add
a **Kill Process** activity targeting `EXCEL` immediately before the `Append To
CSV` step to clear stray local Excel instances on the robot. Ensure earlier
activities released the file (don't hold it open across the append).

### Fix path B -- serialize access
If a concurrent job/iteration can hold the file, serialize writes (write per-run
temp files and merge, or gate access) so two writers never collide.

### Operational note
Discourage opening the production `daily.csv` in Excel during scheduled runs (or
point reviewers at a copy), since an open workbook lock will keep faulting the
append.

### Verification (hand to the user - off-host)
On MOCK-ROBOT at run time, confirm no `EXCEL.EXE` holds `daily.csv` (Task Manager
/ `handle.exe daily.csv`), or that no one has it open. After ensuring it's closed
(or adding Kill Process EXCEL), re-run and the append succeeds.

- **Source:** `csv-activities/playbooks/csv-file-locked-or-invalid-path.md`

---

**Preventive fix:**

1. **Workflow** -- add a Kill Process EXCEL (or an explicit "is the file free?"
   check / retry) before CSV writes that target shared files, and release files
   promptly.
   - **Why:** Shared CSVs reviewed in Excel are a recurring lock source for
     unattended appends.
   - **Who:** RPA developer.

2. **Operational** -- keep the robot's working copy separate from the
   human-reviewed copy so reviewers' Excel sessions don't lock the robot's file.
   - **Who:** Process owner.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | daily.csv is locked by another process (open in Excel) so Append To CSV cannot get write access | High | Confirmed | Yes | `IOException: being used by another process` at Append To CSV naming daily.csv; Read CSV succeeded first; user confirms it's sometimes open in Excel | Close/kill the Excel lock holder (Kill Process EXCEL before the step); serialize concurrent access |

---

Would you like the exact host command to find what holds the file lock on
MOCK-ROBOT, or help cleaning up the `.local/investigations/` folder?
