---
confidence: medium
---

# Export to PDF — Malformed Output Path / Missing .pdf Extension

## Context

What this looks like:
- Activity `Export to PDF` / `Save Document as PDF` (`UiPath.Word.Activities.WordExportToPdf`) fails to save, or throws an unexpected exception while writing the file
- The output file is missing, has no extension, or lands at a wrong/garbled path

What can cause it:
- The output **File Path** is built from **unformatted dynamic pieces** — e.g. a folder variable concatenated to a filename without a separator, or **without a `.pdf` suffix**, producing an invalid target (no extension, doubled/missing backslashes, trailing spaces).

What to look for:
- The output-path expression in the `.xaml`: is it a clean absolute path ending in `.pdf`, or a raw string concatenation?
- Missing separator between folder and file, a filename with no `.pdf`, or an unresolved/empty variable segment.

## Investigation

1. Read the `Export to PDF` node and capture the exact output-path expression. Evaluate what it resolves to for the failing run.
2. Check the resolved string: does it end in `.pdf`? Is there exactly one separator between folder and filename? Are all variable segments populated (no empty/`null` pieces)?

## Resolution

- **Build the path explicitly with a `.pdf` suffix.** Use `Path.Combine` and an explicit extension rather than bare string concatenation, e.g.:
  ```vbnet
  Path.Combine(targetFolderVar, fileNameVar & ".pdf")
  ```
  or, if concatenating, ensure the separator and suffix: `targetFolderVar & "\" & fileNameVar & ".pdf"`.
- **Validate the pieces** — confirm `fileNameVar` has no extension already (avoid `name.pdf.pdf`), no illegal filename characters, and no trailing whitespace; confirm `targetFolderVar` is an absolute path.
- Re-run and confirm the `.pdf` is created at the intended path.

> If the path is correct but the **folder** doesn't exist, the symptom is the generic `Command Failed` — see [export-pdf-missing-output-dir.md](./export-pdf-missing-output-dir.md).
