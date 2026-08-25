# Final Resolution

---

**Root Cause:** The `MonthlyReportFiller` workflow opens the template
`MonthlyTemplate.docx` in a `Word Application Scope` and edits it **in
place** (no save-as-new). On the failing scheduled run, a Microsoft Word
instance was already running on the host (an orphaned WINWORD.EXE from a
prior run holding the file handle). The lock left the template partially
written, so Word opened it and reported `The file appears to be corrupted`.
The document is not genuinely corrupt - it is locked / half-written by a
stale Word session.

**What went wrong:** The scheduled `MonthlyReportFiller` job (started
2026-06-10T06:00:05Z) ran for ~6 seconds, logged `Starting Microsoft
Word`, then warned `A Microsoft Word instance was already running on the
host when the scope started`, then faulted with `Word experienced an error
trying to open the file 'C:\UiPath\Reporting\data\MonthlyTemplate.docx'.
The file appears to be corrupted`. The job worked for its first few runs
and the template opens fine when double-clicked on the user's own machine -
both point at host state, not a defective template or workflow logic.

**Why:** Classic `Word Application Scope` opens the document via COM and
saves back to the same `FileName` on close. When a previous run left
WINWORD.EXE orphaned (e.g., the scope did not dispose, or a prior schedule
overlapped), the orphan holds the template's file handle. The next run
finds the file locked / half-written and Word raises a corruption error.
Editing the template in place compounds it: each failed run can leave the
source further damaged, because the workflow writes back to the original
template path instead of a fresh output file.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: MonthlyReportFiller -- Faulted at 2026-06-10T06:00:11.870Z (ran ~6.5s)
- Job type: Unattended, Schedule-triggered on machine MOCK-HOST
- Folder: Reporting (key `d4e5f6a7-b8c9-4193-a5b6-c7d8e9f01403`)
- Warning log: `[Word Application Scope] A Microsoft Word instance was already running on the host when the scope started.`
- Final error: `Word experienced an error trying to open the file 'C:\UiPath\Reporting\data\MonthlyTemplate.docx'. The file appears to be corrupted.` -> `Main.xaml` -> `WordApplicationScope "Word Application Scope"`

### Project source (Root Cause)
- `Main.xaml`: the `Word Application Scope` opens `FileName="data\MonthlyTemplate.docx"` and edits it with `Replace Text in Document` - there is no save-as / distinct output path, so it overwrites the template in place.
- Combined with the "Word already running" warning and the "worked the
  first few runs, opens fine locally" detail, the evidence points at an
  orphaned/locked Word session and an in-place template overwrite, not a
  corrupt source.

---

**Immediate fix:**

The cause is a host-state lock plus an in-place overwrite. Hand the user
one host check and the workflow change.

### Host check (Reporting / MOCK-HOST, as the robot's Windows user)
1. During or right after a failing run, open Task Manager and look for
   orphaned `WINWORD.EXE` processes with no visible window; end them. Or
   run `Stop-Process -Name WINWORD -Force` in PowerShell.
2. Restore the template from a known-good copy (the in-place overwrites may
   have damaged the current `MonthlyTemplate.docx`).

### Workflow fix
1. Add a **Kill Process** activity configured for `WINWORD` immediately
   **before** the `Word Application Scope` to clear any locked session, and
   confirm the scope always disposes (no `Try/Catch` swallowing its exit)
   so Word closes cleanly after each run.
2. Stop overwriting the template in place: save the edited document to a
   **new output file** (a distinct path, e.g. built with `Path.Combine`),
   leaving `MonthlyTemplate.docx` untouched as the source.
- **Source:** `word-activities/playbooks/word-scope-file-corrupted.md`

> The template is not genuinely corrupt - it is locked / half-written by a
> stale Word session. If the source file was damaged by prior in-place
> runs, also open it with `File > Open > Open and Repair` and save a clean
> copy.

---

**Preventive fix:**

1. **Never edit source templates in place** -- workflows should read a
   template and write a fresh output file per run.
   - **Why:** In-place overwrites turn a transient lock into permanent
     template damage.
   - **Who:** RPA developer.

2. **Always dispose Word scopes + guard against overlap** -- ensure the
   `Word Application Scope` disposes on every path, and avoid overlapping
   schedules that can leave orphaned WINWORD.EXE.
   - **Who:** RPA developer + scheduler owner.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An orphaned/locked Word session left the in-place-edited template half-written, so the next run opens it as "corrupted" | Medium | Confirmed | Yes | "Word already running" warning + corruption error on a job that worked before + in-place template overwrite in Main.xaml + opens fine locally | Kill Process WINWORD before the scope (+ dispose), and save to a new file instead of overwriting the template |

---

Would you like help editing the workflow to add the Kill Process step and
save to a new output file, or the exact host commands to clear orphaned
WINWORD.EXE on MOCK-HOST?
