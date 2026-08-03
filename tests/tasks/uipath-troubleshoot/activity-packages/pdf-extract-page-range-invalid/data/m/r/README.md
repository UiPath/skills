# PDF Extract Page Range — invalid Range (read the page-range parse error, not the file/content)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the malformed-`Range` failure of `UiPath.PDF.Activities` Extract PDF Page Range.

## What this exercises

An `Extract PDF Page Range` ("Extract document pages") opens its input PDF successfully but faults parsing the `Range` argument. The job ends Faulted with `UiPath.DocumentProcessing.Contracts.Extensions.InvalidPageRangeException: The input string 'abc' was not in a correct format.`, thrown from `PageRange.ParsePageRangePart` via `ValidationHelper.ParseRange`. The agent must read the **invalid page-range signature** as the cause (the `Range` argument) — not blame a missing file (`FileNotFoundException`), the PDF content/encryption (`PdfException`), an out-of-bounds page (`Page range is incorrect.`), or a workflow-logic bug. The fix is to correct the `Range` to a valid expression.

Signature captured verbatim from a local `UiPath.PDF.Activities` 4.3.0 run (`ExtractPDFPageRange` with `Range="abc"` against a valid PDF); the workflow name was neutralized so the agent must diagnose from the exception message. Maps to the [pdf-invalid-page-range](../../../../../skills/uipath-troubleshoot/references/activity-packages/pdf-activities/playbooks/pdf-invalid-page-range.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, InvalidPageRangeException + ExtractPDFPageRange stack) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the page-range parse error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
