# Final Resolution

---

**Root Cause:** `Download File from URL` streams to a temporary file and then
finalizes it to the target name. The workflow's next step, `Read CSV` on
`data\daily.csv`, runs **before the file is finalized**, so the real `daily.csv`
isn't present yet (a `daily.csv.tmp` is) and the read faults with
`System.IO.FileNotFoundException: Could not find file '...\data\daily.csv'`. It's
intermittent — when the stream finalizes in time, the run succeeds.

**What went wrong:** The `ReportDownloader` job (started 2026-06-16T11:40:08Z)
logged `[Download File from URL] Completed download ...`, then `[Read CSV] Reading
data\daily.csv ...; folder currently contains data\daily.csv.tmp`, and faulted
with `Could not find file '...\data\daily.csv'. A partially-downloaded
'data\daily.csv.tmp' is present.` The `.tmp` artifact and the most-runs-fail /
sometimes-works pattern confirm a finalize race, not a permanently wrong path.

**Why:** Treating the file as ready the instant the download activity returns is
unsafe — the OS may still be flushing/renaming the temp file. A downstream read
on the final name then misses it. The fix is to wait for the **finalized** file
before consuming it.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ReportDownloader -- Faulted at 2026-06-16T11:40:11.020Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Report Intake (key `fa030003-d4e5-4f60-8a03-000000000003`)
- Final error: `Read CSV: Could not find file '...\data\daily.csv'. A partially-downloaded 'data\daily.csv.tmp' is present.` (`System.IO.FileNotFoundException`) -> `Main.xaml` -> `ReadCsvFile "Read CSV"` (after `Download File from URL` reported completion)

### File Operations (Root Cause)
- Activity surface: `UiPath.Activities.System.FileOperations.DownloadFileFromUrl` followed immediately by `Read CSV` on the final name.
- Logs: download "Completed" -> Read CSV runs with a `daily.csv.tmp` present -> file-not-found on `daily.csv`. The `.tmp` + intermittency = finalize race.

---

**Immediate fix:**

Wait for the finalized file before consuming it.

### Fix path A -- Retry Scope gating the final file (preferred)
Wrap the download (or the `Read CSV`) in a **Retry Scope** whose condition is a
`File Exists` / `Path Exists` check on the **final** target — i.e. `daily.csv`
exists and there is **no** `.tmp` — with a retry interval of ~5 seconds. This
re-checks until the stream finalizes before proceeding.

### Fix path B -- File Exists gate before the read
Before `Read CSV`, poll `File Exists` for the exact final name `daily.csv` (not
`*.tmp`); only read once the finalized file is present.

### Verification (hand to the user - off-host)
Confirm a `daily.csv.tmp` appears transiently and the failure is intermittent
(timing). After adding the Retry Scope / File Exists gate on the final name, the
read waits for finalization and the intermittent failures stop.

- **Source:** `file-operations/playbooks/download-file-stuck-tmp.md`

---

**Preventive fix:**

1. **Workflow** -- never consume a just-downloaded file immediately; gate
   downstream steps on a File Exists check for the finalized name/extension (or a
   Retry Scope).
   - **Why:** Download/finalize races are intermittent and pass in dev but fail
     under load.
   - **Who:** RPA developer.

2. **Validation** -- assert the final extension is present (and no `.tmp`
   lingers) before reading.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Read CSV runs before the download finalizes daily.csv (file still .tmp), so the final name isn't found yet (finalize race) | High | Confirmed | Yes | Download "Completed" then Read CSV "Could not find file daily.csv. A partially-downloaded daily.csv.tmp is present"; intermittent | Retry Scope / File Exists gate on the final target extension before consuming the file |

---

Would you like help adding a Retry Scope / File Exists gate before the read, or
cleaning up the `.local/investigations/` folder?
