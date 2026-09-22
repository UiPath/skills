# Final Resolution

---

**Root Cause:** The workflow's `WorkbookPath` is a relative literal
`"Data\sales-2026-05.xlsx"`. The .NET runtime resolves relative paths
against `Environment.CurrentDirectory` at the moment the activity
executes. Studio's CurrentDirectory is the project folder, so the
workflow worked on the developer's machine (their `Data\` subfolder
contained the workbook). The Robot's unattended runtime CWD is
`%LocalAppData%\UiPath\Packages\<process>\<version>\`, which has no
`Data\` subfolder -- so the resolved path becomes
`C:\Users\automation1\AppData\Local\UiPath\Packages\ExcelDailyImport\1.0.0\Data\sales-2026-05.xlsx`,
which does not exist, and `Use Excel File` faults with
`DirectoryNotFoundException` on the missing `Data\` segment.

The user's actual data folder (`C:\Robot\Data\`) is unrelated to the
resolved path -- the Robot is not "looking in the wrong place" in
a meaningful sense; the workflow simply asked for a relative path
and the runtime resolved it against the standard package CWD.

**What went wrong:** Failing job
`cc333333-9999-aaaa-bbbb-ccccddddeeee` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope received the
relative path `Data\sales-2026-05.xlsx` and asked the OS to open it.
The OS resolved it against the Robot's CWD
(`C:\Users\automation1\AppData\Local\UiPath\Packages\ExcelDailyImport\1.0.0\`),
producing the full resolved path echoed in the error. The `Data\`
segment of that path does not exist on disk, so
`DirectoryNotFoundException` fired before `FileNotFoundException`
would have.

**Why:** Workflow authors who develop in Studio see relative paths
"just work" because Studio's CurrentDirectory is the project folder
during interactive debugging. Robot unattended sessions deliberately
do NOT use the project folder as CurrentDirectory -- the per-package
directory is a sandbox that's recreated on each install/update.
Relative paths are a portability hazard between the two execution
contexts.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `cc333333-...`) -- Faulted at
  `2026-05-20T08:00:01.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`. Robot user:
  `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.IO.DirectoryNotFoundException: Could not find a part of
  the path 'C:\Users\automation1\AppData\Local\UiPath\Packages\ExcelDailyImport\1.0.0\Data\sales-2026-05.xlsx'.`
- Faulting activity: `UseExcelFile_1` (`Use Excel File`) at `Main.xaml`.

### Resolved path (decisive)
- Prefix: `C:\Users\automation1\AppData\Local\UiPath\Packages\ExcelDailyImport\1.0.0\`
  -- the per-package directory under the Robot user's
  `%LocalAppData%`. This is the standard Robot unattended CWD.
- Tail: `Data\sales-2026-05.xlsx` -- matches the workflow's
  configured `WorkbookPath` literal exactly.
- Together: confirms the runtime resolved a relative path against
  the package CWD, not against the user's intended `C:\Robot\Data\`.

### Workflow source (decisive)
- `Main.xaml`: `<uix:UseExcelFile WorkbookPath="Data\sales-2026-05.xlsx" .../>`
  -- the configured value is a literal relative path. No drive
  letter, no leading `\`, no UNC prefix, no `Path.Combine` or
  absolute-path expression.

### Cross-check -- what this is NOT
- Not branch 1 (file deleted): the file likely exists at
  `C:\Robot\Data\sales-2026-05.xlsx` (the user explicitly says so);
  the runtime is not looking for that path.
- Not branch 2 (UNC unreachable): the resolved path is local
  (`C:\Users\...`), not UNC.
- Not branch 4 (unmapped drive): the resolved path is on the
  Robot user's profile drive (`C:`), which is always available.
- Not branch 5 (OneDrive placeholder): the resolved path is under
  `%LocalAppData%\UiPath\Packages\`, not a OneDrive sync folder.
- Not branch 6 (casing / extension mismatch): the filename
  `sales-2026-05.xlsx` matches what the user expects; the issue
  is the prefix, not the leaf.

---

**Recommended Fix (Resolution):**

### Primary fix -- absolute path

In `Main.xaml`, change `UseExcelFile_1`'s `WorkbookPath` from the
relative `"Data\sales-2026-05.xlsx"` to the absolute literal
`"C:\Robot\Data\sales-2026-05.xlsx"`. Cheapest fix, no further
runtime divergence between Studio and Robot.

### Alternative -- anchored path

If the data root must be configurable (different environments, or
the user-data folder differs per host), source the root from a
known anchor and combine:

```vb
' From an Orchestrator asset
Dim dataRoot = GetAsset("DataRoot")    ' e.g., "C:\Robot\Data\"
Dim workbook = Path.Combine(dataRoot, "sales-2026-05.xlsx")
```

Then set the activity's `WorkbookPath` to the assigned `workbook`
variable. The asset can vary across environments without code
changes; the runtime CWD never enters the resolution.

### Validation at job start (prevention)

Add a `File.Exists(workbookPath)` check immediately before
`Use Excel File`, failing fast with a message that names the
resolved path AND the parent directory listing. Catches CWD
divergence at the first run on a new host.

### Prevention -- ban relative paths in unattended workflows

Workflow review should reject relative `WorkbookPath` (and any
relative filesystem path) for unattended Robot runs. The standard
anchoring patterns:

- Orchestrator asset for the data root, combined via `Path.Combine`.
- `Environment.GetEnvironmentVariable("ROBOT_DATA_DIR")` for a
  machine-scope env var.
- `Path.Combine(Environment.GetFolderPath(SpecialFolder.LocalApplicationData), "MyAutomation", ...)`
  for per-user data deliberately under `%LocalAppData%`.
- Absolute literals when the path is genuinely stable.
