# Final Resolution

---

**Root Cause:** The workflow's configured `WorkbookPath` is the
mapped-drive absolute literal `Z:\Data\sales-2026-05.xlsx`. The Z:
drive is mapped in the developer's interactive RDP session (they
can see the file when they log in with their account), but it is
NOT mapped under the Robot service's unattended session on the same
host. Windows drive letters mapped via `net use` are per-session;
the Robot service's session does not inherit interactive-user
mappings. The `Use Excel File` activity asks the OS to resolve
`Z:\Data\sales-2026-05.xlsx` from within the Robot's session, the
OS reports the drive root does not exist, and
`DirectoryNotFoundException` fires on the `Z:\` segment.

**What went wrong:** Failing job
`ee555555-aaaa-bbbb-cccc-dddddddddddd` started at
`2026-05-20T08:00:01.300Z` on `MOCK-HOST` under the
`UIPATH\AUTOMATION1` Robot user. The `Use Excel File` scope received
`Z:\Data\sales-2026-05.xlsx` and the .NET filesystem layer surfaced
the OS's "drive not found" condition as `DirectoryNotFoundException`
on the leading `Z:\` path segment. The user's claim that the file
is visible from RDP is true and reinforces the diagnosis -- the
file IS on Z: in the share, but the Z: mapping only exists in the
user's session, not the Robot's.

**Why:** Drive-letter mappings on Windows are scoped to the logon
session that created them. A user who runs `net use Z: \\server\share`
binds Z: for their own session. The Robot service runs in its own
session (the unattended Robot's profile under `UIPATH\AUTOMATION1`)
and starts with whatever drive mappings are persisted for that
account -- usually none, unless an admin set them up explicitly
while logged in as the Robot user. Persistent mappings created
under one user account are NOT shared with other users on the same
machine.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `ee555555-...`) -- Faulted at
  `2026-05-20T08:00:01.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.IO.DirectoryNotFoundException: Could not find a part of
  the path 'Z:\Data\sales-2026-05.xlsx'.`
- Faulting activity: `UseExcelFile_1` (`Use Excel File`) at
  `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`: `<uix:UseExcelFile WorkbookPath="Z:\Data\sales-2026-05.xlsx" .../>`
  -- the configured value is a literal absolute path with a mapped
  drive letter prefix. Not UNC (`\\server\share\...`), not relative.

### Path-shape classification (decisive)
- The path uses drive letter `Z:` -- a non-standard letter typically
  used for ad-hoc network share mappings (the common conventions
  are: A:/B: floppy, C: system, D: secondary, then arbitrary
  letters for shares).
- The exception is `DirectoryNotFoundException` on the leading
  segment, not `FileNotFoundException`. This rules out branch 1
  (file deleted) -- if Z: existed and only the file was missing,
  the exception would be `FileNotFoundException` on the leaf.
- The error path's drive-root portion `Z:\` is identified as the
  missing segment -- the OS reports the entire drive root does not
  exist from the Robot's perspective.

### User clue (decisive)
- "I can see `Z:\Data\sales-2026-05.xlsx` fine when I RDP into the
  host with my own account." This is the canonical per-session-
  drive-mapping fingerprint: the file IS reachable via Z: from
  the user's session, but the Robot's session has no Z: mapping.

### Cross-check -- what this is NOT
- Not branch 1 (file deleted): exception is `DirectoryNotFoundException`
  on the drive root, not `FileNotFoundException` on the leaf.
- Not branch 2 (UNC unreachable): the path uses a drive letter,
  not `\\server\share`.
- Not branch 3 (relative path / wrong CWD): the path is absolute
  (`Z:\...`); no relative segment to resolve against CWD.
- Not branch 5 (OneDrive placeholder): `Z:\` is a network-share
  mapping, not a OneDrive sync folder.
- Not branch 6 (extension / casing): the user's "works from my
  RDP session" clue confirms the path is valid in some session,
  ruling out a stable naming bug.

---

**Recommended Fix (Resolution):**

### Primary fix -- switch to UNC

In `Main.xaml`, change `UseExcelFile_1`'s `WorkbookPath` from
`Z:\Data\sales-2026-05.xlsx` to the underlying UNC path
`\\<server>\<share>\Data\sales-2026-05.xlsx`. UNC paths are NOT
per-session -- they resolve via SMB the same way under every
account that has access. This eliminates the drive-letter
abstraction entirely and is the standard pattern for unattended
Robot workflows.

To find the underlying UNC, the user can run from their own
interactive session (since their account has the mapping):

```powershell
net use Z:
# or:
(Get-PSDrive Z).DisplayRoot
```

The output names the `\\server\share` that backs Z:.

### Alternative -- persist the drive mapping under the Robot user

If the drive letter is load-bearing (another tool depends on Z:
specifically, or the workflow can't be edited right now):

1. Log into MOCK-HOST as the Robot user (`UIPATH\AUTOMATION1`).
2. Run `net use Z: \\server\share /persistent:yes /user:<robot-user>`
   to create a persistent mapping for that session.
3. Verify after logoff/login: `net use` should list Z:.

Or use a Windows GPO "Drive Maps" startup script scoped to the
Robot user / Robot machines, which guarantees the mapping is in
place when the Robot service session starts.

### Verification on the host (when in doubt)

Before committing to a fix, the user can confirm the diagnosis by
running on MOCK-HOST under the Robot user's session (PsExec or
"Run as service account"):

```cmd
net use
```

If the output lacks a row for Z:, branch 4 is confirmed. If Z: is
present but the file is still missing, re-triage with a different
fingerprint (branch 1 or branch 6 territory).

### Prevention

- Standardize on UNC paths for ALL unattended Robot workflows.
  Drive letters are a per-session abstraction and lead to
  "works on my machine" failures when the same workflow runs
  unattended.
- If drive letters MUST be used, persist the mapping via GPO
  (machine-scope) or via a documented run-once script that logs
  in as the Robot user and creates the persistent mapping.
- Audit existing workflows for drive-letter `WorkbookPath` values;
  migrate to UNC as part of workflow review.
