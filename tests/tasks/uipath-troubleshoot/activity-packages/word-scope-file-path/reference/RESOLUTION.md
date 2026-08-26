# Final Resolution

---

**Root Cause:** The `Word Application Scope` in `Main.xaml` sets `FileName`
to the **relative** path `Output\OfferLetter.docx`. On the unattended robot
that relative path resolves against the robot's working directory -
`C:\Windows\System32\config\systemprofile` (the service account profile) -
not the project folder, so the document is not found and the scope faults
with `System.IO.FileNotFoundException`. The file exists in the project; the
path simply resolves to the wrong place on the robot.

**What went wrong:** The `OfferLetterGen` job (started
2026-06-12T08:20:01Z) faulted ~1.7 seconds in with
`Could not find file 'C:\Windows\System32\config\systemprofile\Output\OfferLetter.docx'`.
The resolved path - rooted at the service profile directory - is the
giveaway: the workflow passed a relative `Output\OfferLetter.docx` and the
runtime combined it with the robot's current working directory. The process
works from Studio (where the working directory is the project folder) and
fails only on the robot, confirming a relative-path resolution gap rather
than a genuinely missing file.

**Why:** A relative path has no fixed root - .NET resolves it against
`Environment.CurrentDirectory` at runtime. In Studio that is the project
folder, so `Output\OfferLetter.docx` is found. Under an unattended robot
the current directory is the robot/service working directory
(commonly `C:\Windows\System32\config\systemprofile`), so the same relative
path points somewhere the file does not exist. The fix is to make the path
absolute so it resolves identically everywhere.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: OfferLetterGen -- Faulted at 2026-06-12T08:20:03.220Z (ran ~1.7s)
- Job type: Unattended, Queue-triggered, machine MOCK-ROBOT-03
- Folder: Offer Letters (key `b8c9d0e1-f2a3-4193-c6d7-e8f901243506`)
- Final error: `System.IO.FileNotFoundException: Could not find file 'C:\Windows\System32\config\systemprofile\Output\OfferLetter.docx'` -> `Main.xaml` -> `WordApplicationScope "Word Application Scope"`

### Project source (Root Cause)
- `Main.xaml`: the `Word Application Scope` has `FileName="Output\OfferLetter.docx"` - a relative path with no absolute root.
- The error's resolved path is rooted at `C:\Windows\System32\config\systemprofile` (the robot service profile), which is exactly where a relative path lands on an unattended robot - not the project's `Output` folder.

---

**Immediate fix:**

The cause is a relative-path resolution gap. Hand the user the workflow
change (and one optional host check).

### Workflow fix
1. Make the document path **absolute** so it resolves the same on every
   host — an explicit absolute root or a UNC path the robot can reach
   (e.g. `\\fileserver\share\Offer Letters\OfferLetter.docx`), or a base
   folder stored in an Orchestrator asset with the filename combined onto
   it. Do **not** use `Path.Combine(Environment.CurrentDirectory, ...)`: on
   an unattended robot `Environment.CurrentDirectory` is the robot working
   directory (`...\systemprofile`) — the same root that just failed — so it
   resolves to the same missing path.
2. If the document is meant to be **generated** by this run rather than
   opened, enable the activity's **Create if not exists** option instead of
   pointing at a pre-existing file.
- **Source:** `word-activities/playbooks/word-scope-file-path-not-found.md`

### Host check (optional, Offer Letters / MOCK-ROBOT-03)
- Confirm the `Output\OfferLetter.docx` file was actually deployed with the
  published process (relative project files are not always present on the
  robot). If it relies on a mapped drive or a OneDrive/SharePoint
  Files-On-Demand placeholder, switch to a UNC path or ensure the file is
  hydrated before the run.

> Do NOT edit the document content or recreate the file as "missing" - the
> file exists; the path resolution is what's wrong.

---

**Preventive fix:**

1. **Always use absolute paths in unattended workflows** -- build file
   paths with `Path.Combine` against a known absolute root, never bare
   relative strings.
   - **Why:** the robot's working directory differs from the developer's,
     so relative paths silently resolve elsewhere.
   - **Who:** RPA developer.

2. **Validate file existence early** -- add a `Path Exists` check before the
   scope to fail with a clear message instead of a raw open error.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Word Application Scope's relative FileName resolves against the robot working directory (service profile), not the project folder, so the document is not found | Medium | Confirmed | Yes | FileNotFoundException resolved to `C:\Windows\System32\config\systemprofile\Output\OfferLetter.docx` + `FileName="Output\OfferLetter.docx"` relative in Main.xaml + works in Studio, fails on robot | Use an absolute path / Path.Combine (or Create if not exists if the doc is generated) |

---

Would you like help editing the workflow to build the path with
Path.Combine, or the exact steps to confirm the file is deployed to
MOCK-ROBOT-03?
