---
confidence: medium
---

# Read Range — Workbook File Or Directory Not Found

## Context

A `UiPath.Excel.Activities` Read Range (or any activity that opens a workbook) fails because the configured `WorkbookPath` does not resolve to an existing file on the host at runtime. The failure happens at the scope's open step, before any sheet or range parsing. The fingerprint is one of the .NET filesystem-resolution exceptions surfacing through the activity.

What this looks like:
- Activity fails with one of:
  - `System.IO.FileNotFoundException: Could not find file '<path>'.` — the parent directory exists but the file does not.
  - `System.IO.DirectoryNotFoundException: Could not find a part of the path '<path>'.` — one or more segments of the parent path do not exist.
  - On UNC paths, an inner `System.IO.IOException` with `The network path was not found` or `The network name cannot be found` may surface instead — same root condition, network layer.
- The path echoed in the error is the resolved path the runtime attempted to open. Capture it verbatim — it is the authoritative input.
- Affects every activity that opens a workbook: `Use Excel File`, `Excel Application Scope`, `Read Range`, `Write Range`, `Create Workbook` (when targeting a directory that doesn't exist), and so on.
- The error fires before sheet/range parsing — sheet name and range are irrelevant.

What can cause it (cause-branches — pick the right one from evidence):

1. **File moved or deleted upstream** — the workbook existed when the workflow was authored but has been deleted, archived, or moved by a human or another process. Symptom: parent directory still exists (`FileNotFoundException`, not `DirectoryNotFoundException`); the file is simply gone.
2. **UNC share unreachable** — workbook lives on a UNC path (`\\server\share\...`) and the share is not reachable from the Robot host at runtime. Causes: network outage, DNS failure, share permissions changed (Robot user no longer has read), server offline, VPN required but not connected. Symptom: error wording mentions network path / network name, OR the path resolves but the parent directory enumeration fails.
3. **Relative path resolved against wrong CWD** — workflow uses a relative path (e.g., `Data\sales.xlsx`) or a path expression that depends on the runtime working directory. Studio runs from the project directory; Robot may run from a different CWD (typically `%LocalAppData%\UiPath\Packages\<process-name>\<version>\`). Symptom: error path shows an unexpected prefix (NOT the user's project folder), or shows just the relative segment.
4. **Drive letter not mapped under the Robot's session** — workbook path uses a mapped drive letter (e.g., `Z:\Data\sales.xlsx`) that exists in an interactive user session but not in the Robot's unattended session. Mapped drives are per-session on Windows; the Robot service's session sees only its own drive mappings. Symptom: `DirectoryNotFoundException` on the drive root; the same path works when an admin RDPs in and runs it manually.
5. **OneDrive / SharePoint placeholder (Files-On-Demand)** — workbook lives in a folder synced by OneDrive or SharePoint client with Files-On-Demand enabled. The file appears in Explorer (placeholder icon) but its content has not been downloaded locally. The Robot user's session may lack the OneDrive client (it runs only under the interactive user), so the placeholder cannot be materialized. Symptom: file appears present when checked via Explorer under an interactive admin, but `Test-Path` from the Robot user's session returns False, OR returns True but file size is 0 / pinned.
6. **Extension or filename casing mismatch** — workflow references `Sales.xlsx` but the actual file is `Sales.xls`, `Sales.xlsm`, or `sales.xlsx`. Local NTFS is case-insensitive, so casing alone doesn't trigger this on a local path — but a SMB-mounted Linux share or a SharePoint document library can preserve case-sensitivity. Symptom: path appears to match but `FileNotFoundException` fires; explorer shows the file with different casing or extension.

What to look for:
- **The resolved path echoed in the exception** — the authoritative input. Don't trust the design-time expression alone; the runtime value may differ (especially for dynamic path expressions or relative paths).
- **`FileNotFoundException` vs `DirectoryNotFoundException`** — file missing vs. directory missing (branch 3, 4, or 2 mid-path).
- **UNC vs local path** — `\\server\share\...` points at branch 2; `C:\` at branches 1, 5, or 6; mapped drive letter (`Z:\`, `M:\`, etc.) at branch 4.
- **Pattern across recent runs** — every run fails identically → persistent (branches 1, 2, 4, 6). Intermittent → branch 2 transient or branch 5 stale-sync.
- **Whose session can see the file** — branches 4 and 5 are session-scoped. If an admin RDPs in and can see the file but the Robot job can't, those branches are likely.

## Investigation

Go in this order — cheaper checks first.

1. **Confirm the activity, configured `WorkbookPath`, and resolved path.** From workflow source: the activity (`Read Range` / `Use Excel File` / etc.) and the `WorkbookPath` expression — literal string, dynamic expression, or variable. From `uip or jobs get <job-key> --output json` → `Info`: the exception class (`FileNotFoundException` / `DirectoryNotFoundException` / wrapped `IOException`) and the resolved path echoed in the error. The resolved path is the authoritative runtime value.

2. **Classify the path shape.** Categorize the resolved path:
   - Absolute local (`C:\...`, `D:\...`) → branches 1, 5, or 6.
   - UNC (`\\server\share\...`) → branch 2 (or 6 if the share is case-sensitive).
   - Mapped drive letter (`Z:\`, `M:\`, etc. — any letter besides standard `C:` / `D:`) → branch 4.
   - Relative or no-drive prefix (`Data\sales.xlsx`, `sales.xlsx`) → branch 3.

3. **Identify which exception fired.** If `DirectoryNotFoundException` and the missing segment is the drive root → branch 4. If `DirectoryNotFoundException` and a middle segment is missing → branch 1 (parent deleted) or branch 2 (UNC unreachable). If `FileNotFoundException` (parent OK, file missing) → branch 1, 5, or 6 (continue).

4. **Recent-jobs pattern.** `uip or jobs list --folder-path '<folder>' --process-name '<process>' --limit 10 --output json`:
   - Every recent run fails with the same path → persistent. Continue with the branch identified above.
   - Mixed pass / fail with no pattern → likely branch 2 (transient UNC) or branch 5 (OneDrive sync race).
   - Failures clustered after a specific date → branch 1 (file deleted then) or branch 6 (file renamed then).
   - Some Robot hosts succeed, others fail → branch 4 (per-host drive mappings) or branch 2 (per-host network reachability).

5. **Workflow-source check for branch 3.** If the path shape is relative:
   - Locate the `WorkbookPath` expression in the workflow source.
   - Determine whether it depends on `Environment.CurrentDirectory`, `Directory.GetCurrentDirectory()`, `Path.GetFullPath(...)`, or a project-relative reference.
   - The Robot's CWD when running an unattended job is typically the per-package directory under `%LocalAppData%\UiPath\Packages\` (or the system equivalent), NOT the project folder. Any relative path resolves against that root.

6. **Host-side verification when CLI evidence is insufficient.** For branches 4 and 5 specifically, the Robot host's filesystem state at the moment of the failure is the authoritative evidence. Ask the user to run (on the Robot host, in the Robot user's session if possible):
   ```powershell
   # Confirm the resolved path
   $path = '<resolved-path-from-error>'
   "Test-Path: $(Test-Path $path)"
   "Item exists: $((Get-Item $path -ErrorAction SilentlyContinue) -ne $null)"
   if (Test-Path (Split-Path $path -Parent)) {
       "Parent directory exists: True"
       Get-ChildItem (Split-Path $path -Parent) | Select-Object Name, Length, Attributes
   } else {
       "Parent directory exists: False"
   }
   # For mapped drives (branch 4):
   net use
   # For OneDrive placeholders (branch 5):
   Get-Item $path -ErrorAction SilentlyContinue | Select-Object Attributes
   # 'Offline' or 'ReparsePoint' attributes indicate a Files-On-Demand placeholder.
   ```

7. **Branch-specific signals from host evidence (when step 6 runs):**
   - `Test-Path` returns False and parent directory contains files but not this one → **branch 1** (file deleted) or **branch 6** (renamed). Compare directory listing against expected name; if a different-cased / different-extension file is present → branch 6.
   - `Test-Path` returns False, parent directory does not exist, drive root does not exist → **branch 4** (drive not mapped).
   - `Test-Path` returns False for the same path that an interactive user CAN see in Explorer → **branch 4** (per-session drives) or **branch 5** (placeholder).
   - `Get-Item` shows `Attributes` containing `Offline` or `ReparsePoint` → **branch 5** (OneDrive placeholder).
   - UNC root listing fails with `The network path was not found` → **branch 2**.

The root cause is **why the path does not resolve** — not "the file is missing" generically. A confirmed finding names the configured path, the resolved path, and one of the cause-branches with evidence.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — File moved or deleted:**
  - Confirm where the file went (moved to a new location, archived to a different folder, or genuinely deleted). Restore from backup or version history if deletion was unintentional (SharePoint / OneDrive: Version History; local filesystem: shadow copies, backup tape).
  - If the file moved deliberately, update the `WorkbookPath` to the new location.
  - Prevention: do not store production workbooks in folders that humans regularly reorganize. Use a dedicated automation-data directory with restricted write access (or a SharePoint library with a documented "do not move" convention).

- **Branch 2 — UNC share unreachable:**
  - Verify network reachability: `Test-NetConnection <server> -Port 445` from the Robot host.
  - Check share permissions on the file server: the Robot user (or its group) must have at least Read on the share AND on the underlying NTFS.
  - For transient outages, add a Retry Scope around the workflow's open step with exponential back-off (3 attempts, 30s / 60s / 120s).
  - Prevention: do not put automation-critical workbooks on shares with unreliable connectivity. Either move to a more reliable share or migrate to SharePoint with the `o365-activities` cloud surface (uses Microsoft Graph, sidesteps SMB entirely).

- **Branch 3 — Relative path resolved against wrong CWD:**
  - **Best fix:** convert the relative path to an absolute path. Use a known anchor:
    - An Orchestrator asset that holds the data folder path: `assetData & "\sales.xlsx"`.
    - `Environment.GetEnvironmentVariable("UIPATH_DATA_DIR")` — a machine-scope env var that points to the data root.
    - `Path.Combine(Environment.SpecialFolder.LocalApplicationData, "MyAutomation", "sales.xlsx")` for per-user data.
  - **If you must keep a relative path,** anchor it explicitly with `Path.GetFullPath(Path.Combine(Directory.GetParent(Reflection.Assembly.GetEntryAssembly().Location).FullName, "Data", "sales.xlsx"))` — but absolute paths are more readable and less fragile.
  - Prevention: ban relative `WorkbookPath` values in workflow review. Always anchor to an explicit base.

- **Branch 4 — Drive letter not mapped under Robot session:**
  - **Best fix:** use the UNC path directly (`\\server\share\subpath\sales.xlsx`) instead of the drive letter. UNC paths do not depend on per-session drive mappings.
  - **If the drive letter is load-bearing** (e.g., a third-party tool also referenced by drive letter), persist the mapping for the Robot user: run `net use Z: \\server\share /persistent:yes /user:<robot-user>` once while logged in as the Robot user. Verify with `net use` afterwards.
  - **Or use the Windows GPO "Drive Maps" startup script** scoped to the Robot user.
  - Prevention: standardize on UNC paths for unattended Robot workflows. Drive letters are user-session abstractions and lead to "works on my machine" failures.

- **Branch 5 — OneDrive / SharePoint placeholder:**
  - **Best fix:** stop syncing the workbook locally; use the cloud surface. Switch the workflow to the `o365-activities` package: `Read Range` (Files / OneDrive) reads via Microsoft Graph against the cloud copy directly, bypassing the local placeholder problem entirely.
  - **If local sync is required:** mark the file as "Always keep on this device" via Explorer right-click, OR disable Files-On-Demand for the automation data folder (`attrib -p +s <path>`).
  - **For the underlying issue** (Robot session lacks the OneDrive client): run the OneDrive client under the Robot user's session, OR (preferred) move the workflow off the desktop OneDrive sync model entirely to the cloud surface.
  - Prevention: do not place automation-consumed workbooks in OneDrive/SharePoint sync folders on Robot hosts. Either put them on a non-synced filesystem path or consume them via Graph from the cloud.

- **Branch 6 — Extension or filename casing mismatch:**
  - Update the `WorkbookPath` to match the actual filename verbatim, including extension and casing.
  - On case-sensitive shares (Linux Samba, SharePoint document library accessed via WebDAV), the workflow MUST use exact-case names. Adopt a convention with the workbook publisher.
  - Prevention: when the path is sourced from external data (queue item, asset, CSV), normalize the case at validation time and confirm the file exists before reading. Workbook publishers should not rename files without coordinating with downstream consumers.

## Prevention (cross-branch)

- Validate `WorkbookPath` at job start via `File.Exists(path)` (or an explicit pre-check activity). Fail fast with a clear message naming the resolved path AND its parent-directory listing.
- Anchor every path. Avoid relative paths in unattended workflows; prefer absolute paths sourced from a single, documented anchor (asset, env var, or constant).
- Prefer UNC over drive letters for shared workbooks.
- Do not couple automation data to per-user OneDrive/SharePoint sync state on Robot hosts. Either keep automation data on plain filesystem paths or consume via the cloud `o365-activities` surface.
- Treat path layout as a contract between the workbook publisher and the workflow. Document the expected location and naming; renames are breaking changes.

## Related

- Other Excel Read Range failure fingerprints (file-locked, sheet-not-found, null-reference on formatted files) are separate playbooks — see [`../summary.md`](../summary.md).
- For shared / cloud Excel workbooks accessed via Microsoft Graph rather than the local filesystem, see [`o365-activities/overview.md`](../../o365-activities/overview.md).
