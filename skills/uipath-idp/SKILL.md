---
name: uipath-idp
description: "UiPath IDP document primitives via `uip documents` — upload a file (PDF/image) once, then digitize it (OCR → markdown, per-page text/DOM/PNG), extract a model's fields with confidence and page/box attribution, or classify/split a packet into typed page ranges; discover the folder's models (`models list`) and OCR/layout engines (`digitizers list`), wait on runs, chain classify→extract on one digitization. For training, labelling, publishing or deploying an IXP extraction model→uipath-ixp. For IxP/document nodes in a .flow→uipath-maestro-flow. For Document Understanding activities in XAML→uipath-rpa."
---

# UiPath IDP Document Primitives

Run documents through the IDP Platform's Document Primitives API (`documents_`) with `uip documents`: upload once, then digitize, extract or classify with a model that already exists. This skill runs models; it does not train them.

<!-- DEMO ONLY: remove this block before opening a PR (personal path). -->
> **Demo setup — local CLI and local API.** This environment runs a local preview build of `uip` from source against the local Documents API (the Aspire stack's gateway). Wherever this skill or its references write `uip`, run `UIPATH_DOCUMENTS_URL=http://localhost:13571/local/local/documents_ UIPATH_CLI_DISABLE_VERSION_SYNC=1 bun /Users/vladdeac/dev/cli/packages/cli/index.ts` instead — e.g. `UIPATH_DOCUMENTS_URL=http://localhost:13571/local/local/documents_ UIPATH_CLI_DISABLE_VERSION_SYNC=1 bun /Users/vladdeac/dev/cli/packages/cli/index.ts documents models list --output json`. Every shell command starts fresh, so put both variables on every call. The URL is user-approved for this demo; the `[WARN] UIPATH_DOCUMENTS_URL is set` line on stderr is expected. `UIPATH_CLI_DISABLE_VERSION_SYNC=1` skips the daily update check, which needs npm (not on PATH here). Do not install or update `uip` from npm for this demo: the published CLI has no `documents` tool.
<!-- /DEMO ONLY -->



## When to Use This Skill

- User has a document (PDF, scan, image) and wants its fields, its text/markdown, or its document type
- User wants a packet split into documents (page ranges) and each part extracted
- User asks which extraction or classification models a tenant or folder can run, and what fields or classes each returns
- User wants OCR with a specific engine (non-Latin scripts) or layout parsing (`gemini`, `gpt`, `uipath`)
- User wants proof of where a value came from: the page and box an extracted value was read from
- User holds a `runId`, `documentId` or `digitization.runId` from an earlier call and wants its result or pages

## When NOT to Use This Skill

- **Creating, labelling, improving, publishing or deploying an extraction model** → `uipath-ixp`. When no model in `models list` fits the documents, hand off there; a model deployed to an Orchestrator folder then appears in `models list --folder-path <that folder>`.
- **Adding a document node to a `.flow`** → `uipath-maestro-flow`.
- **Document Understanding activities inside an RPA workflow** → `uipath-rpa`.

## Critical Rules

1. **Verify `uip documents` syntax in the [CLI Reference](references/cli-reference.md) before running a command** — copy the exact subcommand and options; never guess. Do NOT call the REST API with curl, and do NOT read SDK or CLI source. The tool registers on **preview CLI builds only**: if `uip documents` answers `unknown command`, report that the Documents tool needs a preview build of `uip` (and `uip tools install @uipath/documents-tool`) and stop — do not substitute `uip ixp` or raw HTTP.
2. **Always pass `--output json`** and parse the envelope: `Result`, `Code`, `Data`, plus `Instructions`, `Warning`, `ErrorCode`, `Retry` when present. `Data` keeps the API's camelCase keys (`runId`, `result.output`), so `--output-filter` expressions use those exact names.
3. **Upload a file once and reuse its `documentId`.** Every capability takes the same `documentId`; never upload the same file again to run another model on it. After the first run, pass that run's `digitization.runId` as `--digitization-run-id` on later calls for the same document — it skips OCR entirely.
4. **Read the model id from `models list` before every extract or classify — never guess one.** Pass `--model` a `modelId` or an exact `name` from `uip documents models list --capability <extract|classify> --output json`. Do NOT invent ids like `invoice` from the document type. If no listed model fits the documents, stop and say so: training one is `uipath-ixp`'s job, not something to approximate with another model.
5. **Leave the folder out unless the user or the model names one.** No `--folder-path`/`--folder-key` means the tenant's Shared folder, where the public endpoint models live. When the user names a folder, or the model was deployed to one, pass it on `models list` AND on every following `extract`/`classify`/`runs get`/`pages get` — a run is visible only from the folder it ran in, so reading it from another folder answers `run-not-found`. `uploads` and `digitizers list` take no folder.
6. **Start a run once, with `--wait`, and resume it with `runs get` — never start it again.** Every `digitize`/`extract`/`classify` call starts a billed run. On `Result: TimeoutError` the run is still going on the server: run `uip documents runs get <run-id> --wait --output json` (the command is in `Instructions`). Starting the capability again creates a second run. If the start call itself got no response, re-send it with the same `--idempotency-key` you sent the first time, never without one.
7. **Keep `--timeout` under your shell's own command timeout.** `--wait` defaults to 300 seconds; a tool runner that kills commands sooner (e.g. 120 s) loses the output. Pass `--timeout <seconds>` below that limit (e.g. `--timeout 100`), and resume with `runs get --wait` as in Rule 6. Never poll in a shell loop.
8. **A `partial` run is not a complete result.** `Result: Success` with `Data.status: "partial"` carries a `Warning` naming what failed; `result` holds only what succeeded. Report the missing part explicitly — never present a partial result as the whole document.
9. **Act on a failed run by its `Retry`, not by guessing.** A failed run is `Result: Failure` with the run in `Data`, the API's `<code>: <detail>` in `Message` (the code also in `Context.errorCode`), and the next step in `Instructions`. `RetryWillNotFix` with `ErrorCode: invalid_argument` → fix the request (page range, model, engine, document) using the detail, then start ONE new run. `RetryLater` → wait, then start the same request once more. `RetryWillNotFix` with `ErrorCode: execution_failed` (API `retry: never`) → do not retry; report it. Full map: [Results Guide § Errors](references/results-guide.md#errors).
10. **Report only what the model returned — never fill in a value yourself.** A field with `value: null` is "not found in the document", even when you can read the value on the page. Do not correct, reformat or compute values; report `value` as returned, with its `confidence`. Apply a confidence threshold only when the user gives one.
11. **Flag every value without evidence.** A non-null `value` whose `attribution` is empty comes with a `value-unattributed` warning: report it as unverified, next to the other values, not mixed in silently. When the user asks to check a value, open the page it was read from (`pages get <page> --run-id <digitization.runId> --format image --output-file <path>`) and look at its `box`; never re-extract the value by reading the document yourself.
12. **One document per call; split packets with `classify --split`.** Extract a packet segment by segment: `--digitization-run-id <classify digitization.runId> --page-range <segment.pageRange>`, choosing each segment's model from `models list` by its `class`. A segment with `class: null` goes back to the user for review — never extract it with a guessed model. Recipe: [Workflows Guide § Packet](references/workflows-guide.md#3-classify-a-packet-then-extract-each-segment).
13. **Never delete an upload unless the user asks for that document to be deleted.** `uploads delete <document-id> -y` removes the file and every digitization of it, and cannot be undone; uploads expire on their own (`expiresAt`).

## Quick Start

The common case: one file, its fields.

```bash
uip documents uploads create "<FILE_PATH>" --output json
uip documents models list --capability extract --output json
uip documents extract --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" --wait --timeout 100 --output json
```

1. Upload → keep `Data.documentId`.
2. Pick the model whose `name` and `outputSchema` match the document → keep `modelId` (Critical Rule 4).
3. Extract → `Data.result.output` follows that model's `outputSchema`; each field is `{ value, confidence, attribution[] }`. Keep `Data.digitization.runId` for further calls on this document.
4. Report the values per [Results Guide § Reporting](references/results-guide.md#reporting-extracted-values).

## Task Navigation

| User request | Action |
|---|---|
| "What can I do here?" / "Is extract available?" | `uip documents capabilities list --output json` — each entry's `status` is `available`, `preview`, `deprecated`, `not-available` (with `reason`) or `planned`. Call only `available`/`preview` ones. |
| "Which models can I use?" / "What fields does model X return?" | `uip documents models list [--capability extract\|classify] [--folder-path <path>] --output json`, or one model: `uip documents models get "<model>" --output json`. Extract models carry `outputSchema` (the shape of `result.output`), classify models `classes`. |
| "Extract the fields from this document" | [Quick Start](#quick-start); detail in [Workflows Guide § 1](references/workflows-guide.md#1-extract-one-document). |
| "What type of document is this?" | `uip documents classify --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" --wait --output json` — one segment covering the whole document. |
| "Split this packet" / "Process this bundle of documents" | `classify --split`, then one `extract` per segment — [Workflows Guide § 3](references/workflows-guide.md#3-classify-a-packet-then-extract-each-segment). |
| "Get the text / markdown of this document" / "OCR this" | `uip documents digitize --document-id "<DOCUMENT_ID>" --wait --output json` → `Data.result.markdown`. One page's text: `pages get <n> --run-id <run-id> --format text`. [Workflows Guide § 2](references/workflows-guide.md#2-digitize-a-document). |
| "It's in Japanese / Arabic / Chinese" / "Use a different OCR engine" | `uip documents digitizers list --kind ocr --output json`, pick the engine whose `description` covers the script, then `digitize --ocr-engine <engine>` and pass its `runId` as `--digitization-run-id` to extract/classify. Extract and classify take no engine options. |
| "Where did this value come from?" / "Show me on the page" | `uip documents pages get <attribution.page> --run-id <digitization.runId> --format image --output-file "<PNG_PATH>" --output json`, then view the PNG at `attribution.box` (`[xMin, yMin, width, height]` in page pixels). |
| "Run another model on the same file" | Reuse the `documentId` — or, faster, the previous run's `digitization.runId` via `--digitization-run-id` (Critical Rule 3). |
| "Only pages 2–4" | Add `--page-range 2-4` (syntax `1-3,5,8-`). |
| "Check on run X" / the wait timed out | `uip documents runs get <run-id> --wait --timeout 100 --output json` (Critical Rule 6). |
| "Delete the uploaded file" | `uip documents uploads delete <document-id> -y --output json` — only when asked (Critical Rule 13). |
| "When does my upload expire?" | `uip documents uploads get <document-id> --output json` → `expiresAt`. |
| "Call my local / dev Documents service" | Prefix each command with `UIPATH_DOCUMENTS_URL="<API_ROOT_URL>"` — only for a URL the user named, since the login token is sent there. [CLI Reference § Pointing at another API root](references/cli-reference.md#pointing-at-another-api-root-debugging). |

## Common Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `models list` is empty, or lacks the model the user named | Listed the Shared folder while the model is deployed to another folder | Ask for, or resolve, the folder and re-run with `--folder-path`. |
| `runs get` / `pages get` → `run-not-found` | Read from a different folder than the run used | Pass the same `--folder-path`/`--folder-key` the run was started with (Critical Rule 5). |
| `--output-filter "Result.Output"` returns nothing | `Data` keeps camelCase keys | Use `result.output`, `digitization.runId`, … as printed. |
| `--format image` → `ValidationError` | An image is written to a file, never printed | Add `--output-file <path>`. |
| `document-not-found` on a `documentId` that worked before | The upload expired or was deleted | Upload the file again — the only case where re-uploading is right. |
| `settings-invalid` on digitize with `--layout-engine gemini` | `gemini`/`gpt` need `--layout-model`; other engines reject it | Take `defaultModel` (or one of `models[]`) from `digitizers list --kind layout`. |
| `digitization-invalid` | Passed an extract/classify run's own `runId` as `--digitization-run-id` | Pass that run's `digitization.runId` instead. |

## Unsupported Capabilities

Recognise the request, give the response, stop. Do NOT go looking for an endpoint.

| User request | Response |
|---|---|
| "Train / fine-tune / label / deploy a model" | Out of this skill — hand off to `uipath-ixp`. |
| "Summarize / redact / check rules on this document" | Run `capabilities list` and report that capability's `status` (`planned`, `preview`, `not-available` with `reason`). Call it only if it is `available` and documented in the CLI Reference — today none of them is. |
| "Cancel this run" | No cancel exists yet; the run finishes on its own. Do not start a new one to replace it. |
| "List my past runs" / "run history" | No list route: a run is read only by its `runId`. Ask for the id, or point to the operators' view in the product. |
| "Extract with my own JSON schema / field list" | Extraction runs a model's own taxonomy only; there is no schema input. Use the closest listed model, or build one with `uipath-ixp`. |

## Reference Navigation

- [CLI Reference](references/cli-reference.md) — every `uip documents` command, its options and output
- [Workflows Guide](references/workflows-guide.md) — extract one document, digitize, classify a packet then extract each segment, verify a value on its page
- [Results Guide](references/results-guide.md) — run envelope, `output` / `segments` / `markdown` shapes, warnings, errors and the retry map
