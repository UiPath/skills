# PDF Read Text — file not found (read the missing-file signature, not the PDF content)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the input-file-validation failure of `UiPath.PDF.Activities.ReadPDFText`.

## What this exercises

A `Read PDF Text` ("Read document text") faults at argument validation because the configured input PDF doesn't exist on the robot host. The job ends Faulted with `System.IO.FileNotFoundException: Could not find file "C:\RPA\Invoices\incoming\invoice_4471.pdf"`, thrown from `UiPath.PDF.Activities.PDF.ValidationHelper.ValidateInputFilePath` before the PDF is opened. The agent must read the **missing-file signature** as the cause (the input path) — not blame the PDF content/encryption (that would be a `UiPath.PDF.PdfException`), OCR (`Read PDF With OCR` only), a page range, or a workflow-logic bug. The fix is to make the file present at the configured path on the robot host (or correct the path).

Signature captured verbatim from a local `UiPath.PDF.Activities` 4.3.0 run (`ReadPDFText` against a non-existent path); the workflow name and file path were neutralized/scrubbed so the agent must diagnose from the exception message, not the filename. Maps to the [pdf-file-not-found-or-not-pdf](../../../../../skills/uipath-troubleshoot/references/activity-packages/pdf-activities/playbooks/pdf-file-not-found-or-not-pdf.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, FileNotFoundException + ReadPDFText stack) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the missing-file error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
