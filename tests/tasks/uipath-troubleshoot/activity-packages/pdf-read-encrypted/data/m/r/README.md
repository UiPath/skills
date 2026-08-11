# PDF Read Text — encrypted PDF / wrong password (read the password signature, not a missing/corrupt file)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the encrypted-PDF failure of `UiPath.PDF.Activities.ReadPDFText`.

## What this exercises

A `Read PDF Text` ("Read document text") opens a password-protected PDF but no/wrong `Password` was supplied, so the reader faults. The job ends Faulted with `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException: The password is incorrect.` (from `UiPath.PDF.PdfReader..ctor` via `ReadPDFText.GetFileReader`). The agent must read the **encrypted-PDF/password signature** as the cause — not blame a missing file (`FileNotFoundException`), a corrupt PDF (`Invalid input stream`), Manage-PDF-Password argument strings, or a workflow-logic bug. The fix is to set the correct `Password` on the activity.

Signature captured **verbatim from a live `uip rpa` run**: a valid PDF was encrypted with `Manage PDF Password`, then `Read PDF Text` opened it with no password → `The password is incorrect.`. Workflow/process names neutralized; no real document. Maps to the [pdf-encrypted-or-wrong-password](../../../../../skills/uipath-troubleshoot/references/activity-packages/pdf-activities/playbooks/pdf-encrypted-or-wrong-password.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, PdfException: The password is incorrect.) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the password error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
