# Final Resolution

---

**Root Cause:** The workbook `C:\Robot\Data\sales-2026-05.xlsx` was
deleted or moved from the Robot host between the prior (Successful)
run and the current (Faulted) run. The workflow's configured
`WorkbookPath` is an absolute literal that has not changed; the file
simply went missing. The recent-jobs pattern -- multiple Successful
runs against the same path followed by a single FileNotFoundException
-- rules out a stable configuration issue and points at branch 1 of
the playbook.

**What went wrong:** Failing job
`aa111111-8888-9999-aaaa-bbbbccccdddd` started at
`2026-05-20T08:00:01.300Z`. Its `Use Excel File` scope attempted to
open `C:\Robot\Data\sales-2026-05.xlsx` and the .NET filesystem
layer returned `FileNotFoundException` because the file does not
exist on disk at that path.

`or jobs list` for the same process shows:
- Current run `aa111111-...` -- Faulted at `2026-05-20T08:00:01.812Z`
- Prior run `bb222222-...` (one hour earlier) -- Successful, completed
  cleanly at `2026-05-20T07:00:08.105Z`
- Older runs `cc333333-...`, `dd444444-...` -- both Successful

The exception class is `FileNotFoundException` (not
`DirectoryNotFoundException`), meaning the parent directory
`C:\Robot\Data\` still exists; only the workbook is missing.

**Why:** Between `07:00:08Z` (last Successful run) and `08:00:01Z`
(current attempt), something on the Robot host removed
`sales-2026-05.xlsx`. The CLI evidence cannot determine WHAT removed
it (the audit / file-system journal lives on the host, not in
Orchestrator). Likely candidates are: a human cleaned up the folder,
an upstream rotation / archiving script moved the file, or another
automation deleted it.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `aa111111-...`) -- Faulted at
  `2026-05-20T08:00:01.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`.
- Error (verbatim from `or jobs get`):
  `System.IO.FileNotFoundException: Could not find file 'C:\Robot\Data\sales-2026-05.xlsx'.`
- Faulting activity: `UseExcelFile_1` (`Use Excel File`) at `Main.xaml`.

### Recent-jobs pattern (decisive)
- Prior run: key `bb222222-...`, `Source: Schedule`, **State:
  Successful**, completed `2026-05-20T07:00:08.105Z`. Same process,
  same workbook path.
- Older runs `cc333333-...` (06:00 cycle) and `dd444444-...` (05:00
  cycle) are also Successful. The workflow + path has been working
  hourly until this firing.

### Workflow source (rules out other branches)
- `Main.xaml`: `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" .../>`
  -- absolute literal path. Not relative (rules out branch 3),
  not a mapped drive letter (rules out branch 4), not UNC (rules
  out branch 2).
- Path is on the local C: drive of `MOCK-HOST` -- no network
  involvement.

### Cross-check -- what this is NOT
- Not branch 2 (UNC unreachable): path is local, not UNC.
- Not branch 3 (wrong CWD on relative path): path is absolute.
- Not branch 4 (unmapped drive): path uses C:, the standard system
  drive, always available.
- Not branch 5 (OneDrive placeholder): `C:\Robot\Data\` is a plain
  filesystem path, not a OneDrive / SharePoint sync folder.
- Not branch 6 (extension / casing mismatch): the prior runs used
  the same literal path successfully; the issue is not a stable
  naming difference.

---

**Recommended Fix (Resolution):**

1. **Find where the file went.** Check on `MOCK-HOST`:
   ```powershell
   # Is there a renamed-and-archived copy nearby?
   Get-ChildItem 'C:\Robot\Data\' -Filter 'sales-2026-05*'
   Get-ChildItem 'C:\Robot\Data\' -Filter '*archive*'
   Get-ChildItem 'C:\Robot\Data\' -Filter '*.xlsx' | Sort-Object LastWriteTime -Descending
   # File-system audit (if enabled) or shadow copy
   ```

2. **If the deletion was intentional** (e.g., monthly rotation
   created `sales-2026-06.xlsx` and deleted the prior month's
   file): update the workflow's `WorkbookPath` to the new naming
   convention. Consider making the path dynamic based on the
   current date: `Path.Combine(dataRoot, $"sales-{DateTime.Today:yyyy-MM}.xlsx")`.

3. **If the deletion was unintentional**: restore from backup,
   shadow copies, or version history (Windows: `vssadmin list
   shadows` then mount; SharePoint / OneDrive sync: Version
   History → Restore on the source).

4. **Prevention -- validate at job start.** Add a `File.Exists`
   check immediately before the `Use Excel File` scope, failing
   with a message that names the missing path AND a directory
   listing of the parent. Turns a generic FileNotFoundException
   into a one-glance diagnosis.

5. **Prevention -- coordinate file lifecycle.** Treat the workbook
   path as a contract between whoever maintains the file and the
   workflow that consumes it. Document the location; require
   coordination for deletions / renames / rotations.
