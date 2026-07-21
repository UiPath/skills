# Final Resolution

---

**Root Cause:** `Write CSV` cannot write `data\published.csv` because access to
the path is denied — the file is **read-only**, **open in Microsoft Excel**, or
the **robot's Windows user lacks write permission** to the folder. The activity
faults with `System.UnauthorizedAccessException: Access to the path
'C:\ProgramData\UiPath\Packages\CsvPublish\data\published.csv' is denied`.

**What went wrong:** The `CsvPublish` job (started 2026-06-15T13:07:55Z) read the
staging CSV successfully, then faulted at the `Write CSV` step with the
access-denied `UnauthorizedAccessException` on `published.csv`. The user reports
the output is sometimes open in Excel and is unsure of the robot's folder
permissions.

**Why:** Writing a file requires write access to it and its folder. The OS denies
the write when the file is marked read-only, when another app (Excel) holds it
open for editing, or when the robot's Windows user has no write permission on the
target directory. This is a permissions/attribute/open-handle denial — distinct
from `being used by another process` (an active lock) and from a missing
directory.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvPublish -- Faulted at 2026-06-15T13:07:57.060Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Outputs (key `ea030003-d4e5-4f60-8a03-000000000003`)
- Final error: `Write CSV: Access to the path 'C:\ProgramData\UiPath\Packages\CsvPublish\data\published.csv' is denied.` (`System.UnauthorizedAccessException`) -> `Main.xaml` -> `WriteCsvFile "Write CSV"` (the Read CSV step succeeded first)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.WriteCsvFile` (Write CSV) to `data\published.csv`.
- The error is `UnauthorizedAccessException ... is denied` (not `being used by another process`, not a missing path) — a permissions / read-only / open-in-Excel denial.
- The Read CSV of the staging file succeeded; only the write to the protected/locked output failed.

---

**Immediate fix:**

Make the output file/folder writable by the robot.

### Fix path A -- ensure the file isn't open / kill Excel
Confirm `published.csv` is not open in Excel during runs; add a **Kill Process**
activity targeting `EXCEL` right before `Write CSV` to clear stray/background
instances. Point human reviewers at a copy rather than the robot's output.

### Fix path B -- clear read-only
If the file has the read-only attribute, clear it before writing (or write a
fresh file).

### Fix path C -- grant write permission / writable path
Grant the robot's Windows user **Read/Write** on the `Outputs` folder, or write
to a location the robot can write to.

### Bulletproof alternative
If the activity keeps failing on a stubborn environment, build the CSV text and
write it with plain file I/O: **Output Data Table** (DataTable → string) then
**Write Text File** to the `.csv` path.

### Verification (hand to the user - off-host)
On MOCK-ROBOT, check whether `published.csv` is read-only, open in Excel, or in a
folder the robot user can't write to; after closing Excel / clearing read-only /
granting write, re-run and the write succeeds.

- **Source:** `csv-activities/playbooks/write-csv-access-denied.md`

---

**Preventive fix:**

1. **Workflow** -- add Kill Process EXCEL (or an availability check) before
   writes to shared output files, and write to robot-writable locations.
   - **Why:** Reviewer Excel sessions and folder permissions are recurring
     access-denied sources for unattended writes.
   - **Who:** RPA developer / platform team.

2. **Operational** -- keep the robot's output copy separate from the
   human-reviewed copy so reviewers don't block the write.
   - **Who:** Process owner.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Write CSV can't write published.csv: read-only / open in Excel / robot user lacks write permission (access denied) | High | Confirmed | Yes | `UnauthorizedAccessException: Access to the path ...published.csv is denied` at Write CSV; Read CSV succeeded first; user says it's sometimes open in Excel | Close/Kill Process EXCEL, clear read-only, or grant the robot Read/Write (or write to a writable path) |

---

Would you like the exact host check for what blocks the write on MOCK-ROBOT, or
help cleaning up the `.local/investigations/` folder?
