---
confidence: high
---

# PDF — File not found or not a PDF

## Context

A PDF activity faults at **argument validation**, before the file is parsed, because the input path is missing, points at a non-`.PDF` file, or (for Merge/Join) the file list is invalid. The failure is the input path / list, not the PDF content.

What this looks like — `System.ArgumentException` / `System.ArgumentNullException` carrying one of these verbatim resource strings:

- `Could not find file "<path>"` — the single input file does not exist on the robot host.
- `The input file does not have a .PDF extension: <path>` — the path resolves but is not a `.PDF` (e.g. a `.txt`, `.docx`, or extension-less file).
- `The provided file path is invalid` — the path argument is empty/null or malformed.
- `Could not find one or more of the specified files. Check the logs for a detailed list.` — Merge/Join PDFs: at least one file in the list is missing (the detailed list is in the job logs).
- `One or more of the specified files does not have .PDF extension. Check the logs for a detailed list.` — Merge/Join PDFs: a listed file isn't a PDF.
- `The file list must contain at least two files` — Merge/Join PDFs called with fewer than two inputs.
- `You need to specify the files to merge` — Merge/Join with no file collection set.

What can cause it:
- **Wrong / relative path on the robot host** — the path is valid on the developer machine but absent or differently mapped under the unattended robot account, or it is relative and resolves against an unexpected working folder.
- **Upstream produced an empty/null path** — a variable feeding `File` was never assigned.
- **Wrong file type** — the path points at a non-PDF file (the activity rejects by extension).
- **Incomplete Merge input** — fewer than two files, or a list entry that doesn't exist / isn't a PDF.

What to look for:
- The exception **type is `ArgumentException`/`ArgumentNullException`** and the message is one of the fixed strings above — this is a pre-parse validation failure, so the PDF was never opened. The fix is the path/list argument, never the PDF content.

> **Different cause — do not apply this playbook:**
> - `UiPath.PDF.PdfException` (incl. `Invalid input stream`) means the file was found and opened but is encrypted or corrupt → use [pdf-encrypted-or-wrong-password.md](./pdf-encrypted-or-wrong-password.md) or [pdf-corrupt-or-image-input.md](./pdf-corrupt-or-image-input.md).

## Investigation

1. **Read the message** and identify which string matched (single-file vs Merge/Join vs empty path).
2. **Capture the file path(s)** from the activity arguments / job logs. For the Merge variants, the per-file detail list is logged.
3. **Confirm the file exists on the robot host** that ran the job — not the developer machine. Check whether the path is absolute; if relative, determine what folder it resolves against under the robot account.
4. **For a wrong-extension error**, confirm the actual file type at that path.

## Resolution

- **If `Could not find file` / `Could not find one or more of the specified files`:** correct the path to a file that exists on the robot host, or stage the file there. If the path is relative, make it absolute or anchor it to a known folder. With explicit user approval, fix the upstream expression if the path came from an empty variable.
- **If `does not have a .PDF extension`:** point the activity at an actual `.PDF` file (convert/rename the source first if it isn't a PDF).
- **If `The provided file path is invalid` / `You need to specify the files to merge`:** set the `File` / file-list argument; fix the upstream variable that produced an empty value.
- **If `The file list must contain at least two files`:** supply at least two PDF paths to Merge/Join.
