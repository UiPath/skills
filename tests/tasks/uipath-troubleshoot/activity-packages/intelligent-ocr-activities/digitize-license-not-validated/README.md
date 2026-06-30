# Digitize Document — DU API key 401 (read the license-validation error, not the document)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the `DUApiException` HTTP 401 case of `UiPath.IntelligentOCR.Activities` Digitize Document (UiPath Document OCR).

## What this exercises

A `Digitize Document` (UiPath Document OCR engine) calls the Document Understanding server, which rejects the request with HTTP 401. The job ends Faulted with `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException: Your license could not be validated. Please make sure that the API key parameter is correctly configured.`. The agent must read the **API-key/license-validation 401** as the cause — not blame the document content, a missing/corrupt file, the **Digitizer PDF-component license** (`Invalid license for the PDF component`, a different failure), DU-not-enabled-on-tenant, page-units (403), or request-size (413). The fix is to set a valid DU API key.

Signature source: the 401 branch of `DUServerCaller` in `UiPath.IntelligentOCR` (`Your license could not be validated...` is a verbatim string literal in the package source); workflow/process names neutralized, no real key or document. This package's classic-DU activities cannot be run to their DU fault in the local `uip rpa` host (the Digitizer/Docotic component is unlicensed there, so every `DigitizeDocument` run fails earlier with `Invalid license for the PDF component`); the 401 signature is therefore taken verbatim from source rather than a live run. Maps to the [du-license-or-endpoint-rejected](../../../../../skills/uipath-troubleshoot/references/activity-packages/intelligent-ocr-activities/playbooks/du-license-or-endpoint-rejected.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, DUApiException 401) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the 401 error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
