# Final Resolution

---

**Root Cause:** The `Copy File` activity in `Main.xaml` targets the
destination `C:\AutomationData\Ledger\archive\ledger_2026.txt`, which
already exists, and the activity's Overwrite option is off. When the
activity called `System.IO.File.Copy`, .NET threw the raw
`System.IO.IOException: The file
'C:\AutomationData\Ledger\archive\ledger_2026.txt' already exists.`
(Modern file activities surface the raw `System.IO` exception, not a
UiPath `FileSystemException`.)

**What went wrong:** The `LedgerConsolidation` job (started
2026-06-24T11:20:05.900Z) faulted ~1.2 seconds after launch when the
`Copy File` activity tried to copy over an existing destination file.

**Why:** With Overwrite off, `File.Copy` refuses to replace an existing
target and raises `IOException: ... already exists.`. This is a
destination-conflict, not a missing source file (that would be
`FileNotFoundException`) and not a permissions problem (that would be
`UnauthorizedAccessException`). The prior run — or another process — left
`ledger_2026.txt` in place, so the copy could not proceed.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: LedgerConsolidation — Faulted at 2026-06-24T11:20:07.100Z (ran ~1.2 seconds)
- Folder: Finance (key `4b1c7e90-2a3d-4f5e-9c8b-1a2b3c4d5e6f`)
- Machine: MOCK-HOST
- ErrorCode: `Robot`
- Final error: `The file 'C:\AutomationData\Ledger\archive\ledger_2026.txt' already exists.` → `Main.xaml` → `CopyFile "Copy File"` → `Sequence "Main Sequence"` → `LedgerConsolidation "LedgerConsolidation"`

### System Activities (Root Cause)
- Activity: `CopyFile` (DisplayName: "Copy File"), Overwrite off
- Destination: `C:\AutomationData\Ledger\archive\ledger_2026.txt`
- Exception: `System.IO.IOException: The file 'C:\AutomationData\Ledger\archive\ledger_2026.txt' already exists.` thrown from `System.IO.FileSystem.CopyFile(... Boolean overwrite)` via `UiPath.Core.Activities.CopyFile.Execute`.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Enable the `Copy File` activity's Overwrite option, OR change the destination so it does not collide.
   - **Why:** With Overwrite off, `File.Copy` throws on any pre-existing target. The raw `IOException: ... already exists.` names the exact conflicting path.
   - **Where:** `Main.xaml` → `<ui:CopyFile ... Overwrite="False" ...>`. Set `Overwrite="True"` if replacing the file is intended; otherwise change the destination file name/folder (e.g. append a timestamp or run id) so each run writes a distinct file. Save, rebuild, republish.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/file-folder-operation-failed.md` ("Destination already exists" branch)

---

**Preventive fix:**

1. **Studio** — Decide the archive strategy explicitly: either always overwrite, or write to a uniquely-named destination per run (timestamp/run id). Add a Delete/rename or a "file exists" check before the copy if neither is desired.
   - **Why:** A fixed destination path with Overwrite off is guaranteed to fail on the second run.
   - **Who:** RPA developer

2. **Housekeeping** — If the archive folder is meant to accumulate one file per period, name outputs by period (e.g. `ledger_2026-06.txt`) so runs never collide.
   - **Why:** Prevents silent overwrite of prior archives while avoiding the collision fault.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Destination file already exists + Overwrite off | High | Confirmed | Yes | `IOException: ... already exists.` from `File.Copy(... overwrite)` | Enable Overwrite or use a unique destination |
| H2 | Missing source file / permission denied | Low | Rejected | No | Would be `FileNotFoundException`/`UnauthorizedAccessException`, not "already exists" | — |

---

Would you like help enabling Overwrite or switching to a per-run
destination name in `Main.xaml` and republishing? I can also clean up the
`.local/investigations/` folder if you no longer need it.
