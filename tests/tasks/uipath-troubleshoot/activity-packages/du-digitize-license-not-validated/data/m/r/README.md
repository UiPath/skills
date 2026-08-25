# Digitize Document — invalid DU OCR API key (read the server response, not the AggregateException wrapper)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the invalid-API-key failure of `UiPath.IntelligentOCR.Activities` Digitize Document (UiPath Document OCR engine).

## What this exercises

A `Digitize Document` (UiPath Document OCR engine) calls the Document Understanding OCR service, which rejects the request because the API key is invalid. The job ends Faulted with `System.AggregateException` whose inner message is `Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey` (from `UiPath.DocumentUnderstanding.Digitizer.Digitization.PageDigitizer.ApplyOcr`). The agent must read the **inner server response** as the cause (invalid UiPath Document OCR `ApiKey`) — not stop at the generic `One or more errors occurred.` `AggregateException` wrapper, and not blame the document content, a missing/corrupt file, the **Digitizer PDF-component license** (`Invalid license for the PDF component`, a different local failure), DU-not-enabled-on-tenant, page-units, or request-size. The fix is to set a valid DU OCR API key (from the tenant's AI Units).

Signature captured **verbatim from a live `uip rpa` run** of Digitize Document + UiPath Document OCR against an invalid `ApiKey`; workflow/process names neutralized, no real key or document. Maps to the [du-license-or-endpoint-rejected](../../../../../skills/uipath-troubleshoot/references/activity-packages/intelligent-ocr-activities/playbooks/du-license-or-endpoint-rejected.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, AggregateException + `Invalid API key specified` / `UiPathOCRInvalidApiKey`) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the server response is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
