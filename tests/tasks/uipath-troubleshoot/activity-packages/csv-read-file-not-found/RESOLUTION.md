# Final Resolution

---

**Root Cause:** The `CsvFetcher` process downloads `daily-export.csv` and then
reads it with `Read CSV` immediately after. The download writes the file
asynchronously, so on most runs the file is **not yet fully on disk** when
`Read CSV` executes — the activity faults with `System.IO.FileNotFoundException:
Could not find file '...\data\daily-export.csv'`. The file is present when
checked later, which confirms a **timing race**, not a permanently wrong path.

**What went wrong:** The `CsvFetcher` job (started 2026-06-14T13:55:30Z) logged
`[Download Daily Export] Requested daily-export.csv ...` then, ~0.6 s later,
`[Read CSV] Reading data\daily-export.csv` and immediately `Could not find file
'...\data\daily-export.csv'`. The read fired before the downloaded file landed on
disk. The user reports it fails on most runs but occasionally works — the
hallmark of a race.

**Why:** `Read CSV` opens the file at the moment it runs. When a preceding step
produces the file asynchronously (HTTP download, export, cloud sync), the file
may not be flushed/closed yet, so the path doesn't resolve at read time even
though it appears moments later. (The same error also comes from a path variable
quoted as a literal — `"MyPathVar"` instead of `MyPathVar` — or a relative path
resolving against the wrong working directory; here the path is correct and the
failure is intermittent, so the cause is timing.)

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvFetcher -- Faulted at 2026-06-14T13:55:32.180Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Downloads (key `da030003-d4e5-4f60-8a03-000000000003`)
- Final error: `Read CSV: Could not find file 'C:\ProgramData\UiPath\Packages\CsvFetcher\data\daily-export.csv'.` (`System.IO.FileNotFoundException`) -> `Main.xaml` -> `ReadCsvFile "Read CSV"`

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.ReadCsvFile` (Read CSV), `FilePath=[exportPath]` (`data\daily-export.csv`).
- Log order: "Requested daily-export.csv from the reporting API" -> "Reading data\daily-export.csv" -> "Could not find file ...". The read runs immediately after the download request, before the file is on disk.
- Intermittent (fails most runs, occasionally works) — the signature of a timing race, not a wrong/quoted path.

---

**Immediate fix:**

Make `Read CSV` wait until the downloaded file actually exists.

### Fix path A -- File Exists retry before the read (preferred)
Insert a wait loop before `Read CSV`: poll `Path Exists` / `File Exists` for
`data\daily-export.csv` (with a sensible timeout), and only read once it's
present. Prefer this over a fixed delay so it is robust to variable download
times. (A `Retry Scope` around the read achieves the same.)

### Fix path B -- brief Delay (weaker)
A short `Delay` before the read can mask the race, but a fixed wait is brittle if
the download is sometimes slower — use the File Exists retry instead.

### Fix path C -- rule out a path problem
Confirm the `FilePath` is correct and that the path variable is passed as the
variable (`exportPath`), not quoted as a literal string (`"exportPath"`), and
that it's an absolute or correctly-resolved path. (Here the path is right and the
failure is intermittent, so timing is the cause — but verify to be safe.)

### Verification (hand to the user - off-host)
Confirm a download/export step runs immediately before `Read CSV`, and that
failures are intermittent (race) rather than every run (which would indicate a
wrong/quoted path). After adding the File Exists retry, the read waits for the
file and the intermittent failures stop.

- **Source:** `csv-activities/playbooks/read-csv-file-not-found.md`

---

**Preventive fix:**

1. **Workflow** -- never read a just-produced file immediately; gate downstream
   reads on a File Exists retry (or Retry Scope) so async writes complete first.
   - **Why:** Read-after-download races are intermittent and hard to spot — they
     pass in dev and fail under load.
   - **Who:** RPA developer.

2. **Paths** -- pass path variables unquoted and use absolute/`Path.Combine`-built
   paths so a timing race is never confused with a path error.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Read CSV runs before the upstream download finishes writing daily-export.csv, so the file isn't on disk yet (timing race) | High | Confirmed | Yes | Log: download request then immediate "Could not find file"; file present later; intermittent (fails most runs) | Guard the read with a File Exists retry / Delay so it waits for the download; verify the path / unquoted path variable |

---

Would you like help adding a File Exists retry before the Read CSV, or cleaning
up the `.local/investigations/` folder?
