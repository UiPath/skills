# PDF Read Text — corrupt / invalid PDF (read the parse error, not a missing file)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the corrupt-input-stream failure of `UiPath.PDF.Activities.ReadPDFText`.

## What this exercises

A `Read PDF Text` ("Read document text") finds and opens its input file but the Digitizer reader cannot parse the bytes. The job ends Faulted with `UiPath.PDF.PdfException: Invalid input stream`, raised from `UiPath.PDF.PdfReader..ctor`. The agent must read the **corrupt/unreadable-PDF signature** as the cause — not blame a missing file (`FileNotFoundException`), encryption (`PdfIncorrectPasswordException` / Manage-PDF-Password's `A password for the encrypted PDF file was not supplied`), OCR (`No OCR Engine assigned.`), an invalid page range (`InvalidPageRangeException`), or a workflow-logic bug. The fix is to replace the input with a valid PDF (and fix any upstream step that produced the bad file).

Signature source: the `Invalid input stream` re-throw in `UiPath.PDF` `PDFReader` (verbatim string literal in the package source); workflow name neutralized. The companion file-not-found and invalid-range scenarios were live-confirmed via `uip rpa run`; this corrupt case uses the source-verbatim signature (a live confirmation run was blocked by a Studio host cache). Maps to the [pdf-corrupt-or-image-input](../../../../../skills/uipath-troubleshoot/references/activity-packages/pdf-activities/playbooks/pdf-corrupt-or-image-input.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, PdfException: Invalid input stream) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the parse error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
