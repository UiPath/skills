---
name: uipath-idp
description: "UiPath IDP document capabilities via `uip documents` — upload a PDF or image to a folder, then digitize it: OCR to markdown, plus each page as text, markdown or DOM with word boxes. Pick OCR and layout engines (`discovery digitization-engines list`), check which capabilities a tenant can call (`discovery capabilities list`), wait on runs (`runs get --wait`) and read single pages (`pages get`). For training, labelling, publishing or deploying an IXP extraction model→uipath-ixp. For document nodes in a .flow→uipath-maestro-flow. For Document Understanding activities in XAML→uipath-rpa."
---

# UiPath IDP Document Capabilities

Turn documents into text with `uip documents`: upload a file to a folder, digitize it, and read the result as markdown or page by page. This skill reads documents; it does not train or run extraction models.

## When to Use This Skill

- User has a document (PDF, scan, image) and wants its text or markdown
- User wants OCR with a specific engine (non-Latin scripts), a PDF's text layer re-OCR'd, or layout parsing (HTML tables, forms, figures)
- User wants one page of a digitized document as text, markdown, or words with their boxes
- User asks which document capabilities or digitization engines a tenant has
- User holds a `runId` or `documentId` from an earlier call and wants its result or pages

## When NOT to Use This Skill

- **Creating, labelling, improving, publishing or deploying an extraction model** → `uipath-ixp`.
- **Adding a document node to a `.flow`** → `uipath-maestro-flow`.
- **Document Understanding activities inside an RPA workflow** → `uipath-rpa`.

## Critical Rules

1. **Verify `uip documents` syntax in the [CLI Reference](references/cli-reference.md) before running a command.** Copy the exact subcommand and options; never guess. Do NOT call the REST API with curl, and do NOT read CLI source. The tool ships in **preview builds of `uip` only**: if `uip documents` answers `unknown command`, report that this `uip` build has no Documents tool and stop.
2. **Always pass `--output json`** and parse the envelope: `Result`, `Code`, `Data`, plus `Message`, `Instructions`, `Warning`, `ErrorCode`, `Retry` and `Context` when present. `Data` keeps the API's camelCase keys (`runId`, `result.markdown`), so `--output-filter` expressions use those exact names. The examples under `--help` print the same keys capitalised; trust the real output.
3. **Name the folder on every folder-scoped call, and keep it the same.** `uploads create`, `digitize`, `runs get` and `pages get` need `--folder-path "<FOLDER_PATH>"` or `--folder-key "<FOLDER_KEY>"` (one, never both); without it they fail locally with `ValidationError` (`No folder given.`). An upload and its runs are visible only from their folder. When the user has not named a folder, ask; do not guess one.
4. **Upload a file once and reuse its `documentId`.** Another page range or another engine is a new `digitize` on the same `documentId`, in the same folder. Upload again only after `expiresAt`: an upload cannot be read back or deleted from the CLI.
5. **Start a run once, with `--wait`, and resume it with `runs get`. Never start it again.** Every `digitize` call starts a new digitization. On `Result: TimeoutError` the run is still going on the server: run the `runs get` command printed in `Instructions`, which already carries the folder.
6. **Keep `--timeout` under your shell's own command timeout.** `--wait` gives up after 300 seconds by default; a tool runner that kills commands sooner loses the output. Pass a lower `--timeout <SECONDS>` and resume as in Rule 5. Never poll in a shell loop.
7. **Read engine names from `discovery digitization-engines list`; never guess one.** The defaults (OCR `auto`, `--apply-on-pdf auto`, no layout engine) suit most documents. Change them only when the user asks or the text comes back wrong. A layout engine runs on OCR output, so `--layout-engine` cannot be combined with `--apply-on-pdf never`.
8. **Act on a failure by its `Retry`, not by guessing.** `RetryWillNotFix` with `ErrorCode: invalid_argument` → fix the request using the detail, then start ONE new run. `RetryLater` → wait, then send the same request once more. `RetryWillNotFix` with `ErrorCode: execution_failed` → do not retry; report the code and the `runId`. A run succeeds or fails for the whole document; there is no partial status. Full map: [Results Guide § Errors](references/results-guide.md#errors).
9. **Stop on `not-supported-yet`.** The service answers it (HTTP 501) for an input or option it does not run yet, and its detail says what to send instead. Follow the detail when you can; otherwise report it. Never retry the same call or go around the CLI.
10. **Read large documents page by page.** `Data.result.markdown` holds every page and grows with the page count. Read the count first (`--output-filter "result.pageCount"`), then one page at a time with `pages get`, or write a page to disk with `--output-file`.
11. **Report the text as it was digitized.** Do not correct, complete or translate OCR output unless the user asks. When the text looks wrong, say so and offer another engine or `--apply-on-pdf always`.

## Quick Start

The common case: one file, its markdown.

```bash
uip documents uploads create "<FILE_PATH>" --folder-path "<FOLDER_PATH>" --output json
uip documents digitize --document-id "<DOCUMENT_ID>" --folder-path "<FOLDER_PATH>" --wait --timeout <SECONDS> --output json
uip documents pages get <PAGE_NUMBER> --run-id "<RUN_ID>" --format markdown --folder-path "<FOLDER_PATH>" --output json
```

1. **Upload** → keep `Data.documentId`. Skip this step when the user already gave a `documentId`.
2. **Digitize** → check `Result` and `Data.status` ([Results Guide § Run envelope](references/results-guide.md#run-envelope)). `Data.result.markdown` is the whole document, each page opening with `<!-- page: N -->`. Keep `Data.runId` for the pages.
3. **Read pages** (optional) → one page as `text`, `markdown` or `dom` (Critical Rule 10).
4. **On `TimeoutError`** → the `runs get` command in `Instructions`, repeated while it keeps timing out (cap: 10 tries, then report the `runId` and stop).

## Task Navigation

| User request | Action |
|---|---|
| "What can I do here?" / "Is digitize available?" | `uip documents discovery capabilities list --output json`. Each row's `status` is `available`, `preview`, `deprecated`, `not-available` (with `reason`) or `planned`. Call only `available` and `preview` ones. |
| "Get the text / markdown of this document" / "OCR this" | [Quick Start](#quick-start). |
| "It's in Japanese / Arabic / Chinese" / "Use another OCR engine" | `uip documents discovery digitization-engines list --kind ocr --output json`, pick the engine whose `description` covers the script, then digitize with `--ocr-engine <ENGINE>`. The default `auto` already picks an engine per page by its alphabet. |
| "The PDF's text is garbled" / "OCR the PDF instead of its text layer" | Digitize with `--apply-on-pdf always`. `never` reads the text layer only, so a scanned page yields no text. |
| "Keep the tables" / "I need the form structure" | Digitize with `--layout-engine uipath`: tables come as HTML `<table>` with row and column spans, plus forms and tagged figures. Without it, tables come as lines of text. |
| "Only pages 2 to 4" | Add `--page-range 2-4` (syntax `1-3,5,8-`; the order given is the order digitized). |
| "Give me page 3" / "Where is this word on the page?" | `uip documents pages get 3 --run-id "<RUN_ID>" --format <text\|markdown\|dom> --folder-path "<FOLDER_PATH>" --output json`. `dom` holds the words with their boxes. |
| "Check on run X" / the wait timed out | `uip documents runs get "<RUN_ID>" --folder-path "<FOLDER_PATH>" --wait --timeout <SECONDS> --output json` (Critical Rule 5). |
| "When does my upload expire?" | `expiresAt` in the `uploads create` output. Keep it: the upload cannot be read again later. |

## Common Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `ValidationError`: `No folder given.` | A folder-scoped command ran without a folder | Add `--folder-path` or `--folder-key` (Critical Rule 3). |
| `run-not-found` on a run that exists | Read from another folder than the one it ran in | Pass the folder the run was started with. |
| `document-not-found` | The upload expired, or the id belongs to another folder | Use the upload's folder; upload again only when it expired. |
| `pages get` → `run-not-final` | The digitization is still `queued` or `running` | Wait with `runs get --wait`, then read the page. |
| `pages get` shows the wrong page after `--page-range 5-6` | Page numbers count within the digitization, from 1 in the order digitized | Page `1` is the file's page 5; map back from the range you passed. |
| `--output-filter "Result.Markdown"` returns nothing | `Data` keeps camelCase keys | Use `result.markdown`, `result.pageCount`, … as printed. |
| `settings-invalid` on digitize | An unknown engine, or `--layout-engine` together with `--apply-on-pdf never` | Take the engine from `discovery digitization-engines list`; the error's `allowed` lists the valid values. |
| `unsupported-media-type` on upload | The file is not a PDF, PNG, JPEG, TIFF, GIF or BMP; the type is read from the file's bytes, not its name | Convert the file, then upload it. |
| `upload-unavailable-for-tenant` | Uploads are not enabled for the tenant | Report it: an upload is the only way to pass a document. |
| `not-supported-yet` (501) | The service does not run that input or option yet | Critical Rule 9. |

## Unsupported Capabilities

Recognise the request, give the response, stop. Do NOT go looking for an endpoint.

| User request | Response |
|---|---|
| "Extract the fields" / "Classify this" / "Split this packet" | `uip documents` has no such command. Run `discovery capabilities list` and report that capability's `status`. Offer the digitized text instead; never present values you read from it as a model's extraction. |
| "Train / label / publish / deploy a model" | Out of this skill: hand off to `uipath-ixp`. |
| "Cancel this run" | No cancel exists; the run finishes on its own. Do not start a new one to replace it. |
| "List my runs" / "List my uploads" | No list exists: a run is read only by its `runId`. Ask for the id. |
| "Download / delete the uploaded file" | Not possible from the CLI; an upload expires on its own at `expiresAt`. |

## Reference Navigation

- [CLI Reference](references/cli-reference.md) — every `uip documents` command, its options and output
- [Results Guide](references/results-guide.md) — the run envelope, the digitize result, page formats, warnings, errors and the retry map
