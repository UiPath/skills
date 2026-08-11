# Final Resolution

---

**Root Cause:** The `Export to PDF` (`WordExportToPdf`) activity in
`Main.xaml` builds its output `FileName` by **string concatenation without a
`.pdf` extension** — `outFolder + "\" + reportName` → `C:\Reports\MonthlyReport`.
That resolved value is not a valid PDF target (no `.pdf`), so the activity
throws `System.ArgumentException: The export file path must specify a .pdf
file`.

**What went wrong:** The `ReportPdfGen` job (2026-06-17T09:40) opened
`Report.docx` fine, then faulted at `Export to PDF` with `The export file
path must specify a .pdf file. Value was 'C:\Reports\MonthlyReport'`. The
error names the exact malformed value — a folder + name with no extension.

**Why:** `WordExportToPdf` requires the output path to be a file ending in
`.pdf`. Building it as `outFolder + "\" + reportName` omits the extension
(and is fragile against missing separators / empty segments generally). The
document opened; the failure is purely the malformed output path.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ReportPdfGen -- Faulted at 2026-06-17T09:40:06Z (~4s)
- Folder: Report PDFs (key `c5d6e7f8-a9b0-4193-bc2d-3e4f50617283`), machine MOCK-ROBOT-14
- Logs: `Document 'data\Report.docx' opened` -> `Export to PDF: The export file path must specify a .pdf file. Value was 'C:\Reports\MonthlyReport'`.
- Final error: `System.ArgumentException: The export file path must specify a .pdf file. Value was 'C:\Reports\MonthlyReport'` -> `WordExportToPdf "Export to PDF"` -> `WordApplicationScope` -> `Main.xaml`.

### Project source (Root Cause)
- `Main.xaml`: `Export to PDF` `FileName = [outFolder + "\" + reportName]` with `outFolder = "C:\Reports"`, `reportName = "MonthlyReport"` — **no `.pdf` suffix**.
- The resolved value matches the error's `Value was 'C:\Reports\MonthlyReport'` exactly, confirming the missing-extension cause.

---

**Immediate fix:**

The document opens; the output path just needs a valid `.pdf` filename.

- **Append the `.pdf` extension and build the path cleanly:**
  ```vbnet
  Path.Combine(outFolder, reportName & ".pdf")
  ```
  (or, if concatenating: `outFolder & "\" & reportName & ".pdf"`).
- **Validate the pieces** — confirm `reportName` doesn't already carry an
  extension (avoid `MonthlyReport.pdf.pdf`), has no illegal filename
  characters or trailing spaces, and `outFolder` is an absolute path with a
  single separator.
- **Source:** `word-activities/playbooks/export-pdf-output-path-format.md`

> Distinct from the generic `Command Failed` you get when the output
> **folder** doesn't exist (see export-pdf-missing-output-dir) — here the
> error explicitly names the `.pdf` requirement and the malformed value.

---

**Preventive fix:**

1. **Always build file paths with `Path.Combine` + an explicit extension**
   for activities that require a typed output file, rather than bare string
   concatenation.
   - **Why:** concatenation silently drops the extension / separators.
   - **Who:** RPA developer.

2. **Assert the output path** ends in `.pdf` before the export (or in a
   pre-step), so a malformed path fails fast with a clear message.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Export to PDF output path is built without a .pdf extension, so the activity throws ArgumentException requiring a .pdf file | Medium | Confirmed | Yes | `ArgumentException: The export file path must specify a .pdf file. Value was 'C:\Reports\MonthlyReport'` + Main.xaml FileName = `outFolder + "\" + reportName` (no .pdf) | Build the path with a .pdf suffix: `Path.Combine(outFolder, reportName & ".pdf")` |

---

Would you like help editing the output-path expression to add the `.pdf`
suffix via `Path.Combine`?
