# Final Resolution

---

**Root Cause:** The `Export to PDF` (`WordExportToPdf`) activity in
`Main.xaml` writes to `C:\Output\2026\Invoices\Invoice.pdf`, but that
**output folder does not exist** on the robot and **no `Create Folder`
precedes** the export. `WordExportToPdf` does not auto-create intermediate
directories, so the save fails — surfacing only as the generic
`Command Failed`.

**What went wrong:** The `InvoicePdfExport` job (2026-06-17T08:30) opened
`Invoice.docx` fine (log: `Document 'data\Invoice.docx' opened`), then
faulted at `Export to PDF` with `UiPath.Word.Activities.WordException:
Command Failed` — no further detail. The document opened, so the failure is
on the write side.

**Why:** `WordExportToPdf` hands the target path to Word's export; if the
parent directory is absent, the underlying save throws and the activity
reports a non-specific `Command Failed`. The workflow never creates
`C:\Output\2026\Invoices\`, and the path is a dated/nested tree that won't
pre-exist on a fresh run — so every run fails until the folder is created.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoicePdfExport -- Faulted at 2026-06-17T08:30:06Z (~4s)
- Folder: PDF Export (key `a3b4c5d6-e7f8-4193-9a0b-1c2d3e4f5061`), machine MOCK-ROBOT-13
- Logs: `Starting Microsoft Word` -> `Document 'data\Invoice.docx' opened` -> `Export to PDF: Command Failed`. The input opened; the export write failed.
- Final error: `UiPath.Word.Activities.WordException: Command Failed` -> `WordExportToPdf "Export to PDF"` -> `WordApplicationScope` -> `Main.xaml`.

### Project source (Root Cause)
- `Main.xaml`: `Export to PDF` `FileName = C:\Output\2026\Invoices\Invoice.pdf`. There is **no `Create Folder`** activity anywhere before the `Word Application Scope`.
- A nested, dated output path with no directory-creation step is the missing-output-directory configuration the generic `Command Failed` masks.

---

**Immediate fix:**

The input opens fine; the output directory is the gap.

- **Add a `Create Folder` before the export** — target the output directory
  (`C:\Output\2026\Invoices\` — or the folder portion of the path,
  `Path.GetDirectoryName(outputPath)`) **immediately before** the
  `Word Application Scope` / export step. `Create Folder` is a no-op when
  the folder already exists, so it's safe on every run and handles
  dynamically-built dated paths.
- **Or** point the export at a directory the robot is guaranteed to have,
  or have provisioning pre-create the target tree.
- **Source:** `word-activities/playbooks/export-pdf-missing-output-dir.md`

> The generic `Command Failed` carries no detail; a missing output directory
> is the most common cause here (nested dated path, no Create Folder). If
> adding Create Folder doesn't resolve it, re-check the path format (`.pdf`
> suffix / separators) and rule out a busy/locked Word COM session.

---

**Preventive fix:**

1. **Always create output directories before file-writing activities** that
   don't auto-create them (`Export to PDF`, many save activities).
   - **Why:** dated/nested output trees never pre-exist on a fresh robot.
   - **Who:** RPA developer.

2. **Surface the real error** — wrap the export so a generic `Command
   Failed` is logged with the resolved output path, making the missing
   folder obvious next time.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Export to PDF output directory does not exist and the activity won't auto-create it, so the save fails as generic Command Failed | Medium | Confirmed | Yes | `WordException: Command Failed` at WordExportToPdf after the input opened + output path `C:\Output\2026\Invoices\...` + no Create Folder in Main.xaml | Add a Create Folder for the output directory before the export |

---

Would you like help adding the `Create Folder` step (target =
`Path.GetDirectoryName` of the output path) before the export?
