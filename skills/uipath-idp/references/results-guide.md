# Results Guide

What `uip documents` prints and how to read it. Commands: [CLI Reference](cli-reference.md).

## Run envelope

`digitize`, `extract`, `classify` and `runs get` print the run as `Data`. Every key is always present; keys that depend on the run's state are `null` until then.

```json
{
  "Result": "Success",
  "Code": "DocumentsExtract",
  "Data": {
    "runId": "<RUN_ID>",
    "capability": "extract",
    "status": "succeeded",
    "engine": { "modelId": "invoices", "ocr": { "engine": "uipath" }, "layout": { "engine": "uipath", "model": null } },
    "result": { "output": { } },
    "digitization": { "runId": "<DIGITIZATION_RUN_ID>" },
    "resultUrl": "https://cloud.uipath.com/<ORG>/<TENANT>/documents_/runs/<RUN_ID>",
    "warnings": [],
    "error": null,
    "traceId": "<TRACE_ID>",
    "createdAt": "<CREATED_AT>",
    "completedAt": "<COMPLETED_AT>"
  }
}
```

| Field | Meaning |
|---|---|
| `status` | Closed set. `queued`, `running` → not final. `succeeded`, `partial`, `failed` → final, never changes again. |
| `capability` | `digitize`, `extract` or `classify` — says which `result` shape to read. |
| `result` | `null` unless `succeeded`/`partial`. Always the full result, inline. |
| `engine` | What ran: `modelId` (extract/classify), OCR and layout engines. Report it when the user asks how a value was produced. |
| `digitization.runId` | The digitized document this run read. Reuse as `--digitization-run-id`; use as `pages get --run-id`. On a digitize run it equals `runId`. |
| `warnings[]` | Typed problems, same shape as `error`. Also summarised in the envelope's `Warning`. |
| `traceId` | Quote it when reporting a failure to support. |
| `resultUrl` | The API route of the run. Read it with `runs get <runId>`, not with curl (SKILL.md Critical Rule 1). |

How the envelope maps to the CLI result:

| `Data.status` | `Result` | Envelope extras | Next step |
|---|---|---|---|
| `queued` / `running` (no `--wait`) | `Success` | `Instructions`: the `runs get … --wait` command | Run it |
| `succeeded` | `Success` | `Warning` if `warnings[]` is non-empty | Read `result` |
| `partial` | `Success` | `Warning` starting `Run is partial;` + what failed | Read `result`, report the missing part (SKILL.md Critical Rule 8) |
| `failed` | `Failure` | `Message` (`… failed: <code>: <detail>`), `ErrorCode`, `Retry`, `Instructions` (next step), `Context.errorCode`, `Context.traceId` | [Errors](#errors) |
| still running at `--timeout` | `TimeoutError` | last-seen run in `Data` | `runs get <runId> --wait` (SKILL.md Critical Rule 6) |

## Extract result

`result.output` follows the model's `outputSchema`: a field group is an **array of rows**, a row has one key per field, a top-level field sits directly under `output`, a sub-group is an array inside its parent's row. Every taxonomy field is present, never omitted.

```json
"output": {
  "Invoice": [
    { "Invoice number": { "value": "INV-1043", "confidence": 0.99,
                          "attribution": [{ "page": 1, "box": [1820, 260, 410, 48], "text": "INV-1043" }] },
      "Total amount":   { "value": 3180.5, "confidence": 0.96,
                          "attribution": [{ "page": 2, "box": [1890, 2960, 300, 56], "text": "$3,180.50" }] },
      "Currency":       { "value": null, "confidence": null, "attribution": [] } }
  ]
}
```

| Key | Meaning |
|---|---|
| `value` | Typed per the taxonomy. `null` = the model found nothing. |
| `confidence` | Model score, `0`–`1`; `null` when the model gives none. |
| `attribution[]` | One entry per region the value came from (may span lines or pages); empty when `value` is `null`. |
| `attribution[].page` | Page in the digitized document (`digitization.runId`). |
| `attribution[].box` | `[xMin, yMin, width, height]` in that page's pixels (`pages[].width × height`). |
| `attribution[].text` | Source text as OCR read it (`$3,180.50`); may differ in form from `value` (`3180.5`). |

Field names contain spaces and capitals. Quote them in JMESPath: `--output-filter 'result.output.Invoice[0]."Total amount".value'`.

### Reporting extracted values

1. One line per field: group / field name, `value`, `confidence`. Group rows of a repeating group (line items) as a table.
2. `value: null` → "not found". Never fill it in (SKILL.md Critical Rule 10).
3. Non-null `value` with empty `attribution` (a `value-unattributed` warning) → mark it **unverified**.
4. Apply a confidence threshold only if the user set one; then list the fields under it separately.
5. Say which model ran (`engine.modelId`) and which pages were read when `--page-range` was used.
6. `partial` run → name what is missing before listing what came back.

## Classify result

```json
"segments": [
  { "pageRange": "1-3", "class": "claim_form",     "confidence": 0.95 },
  { "pageRange": "4-6", "class": "medical_report", "confidence": 0.88 },
  { "pageRange": "7",   "class": null,             "confidence": 0.41 }
]
```

- Without `--split`: exactly one segment covering the requested pages.
- `class` is one of the model's `classes[].name`, or `null` when nothing matched (default `allowUnknown`). With `--no-allow-unknown`, the best match plus a `low-confidence` warning instead.
- `pageRange` is directly usable as `--page-range` on extract, with `digitization.runId` as `--digitization-run-id`.

## Digitize result

```json
"result": {
  "pageCount": 3,
  "markdown": "# ACME Corp: Earnings Statement\n\n| Pay date | Net pay |\n|---|---|\n…",
  "pages": [ { "number": 1, "width": 2480, "height": 3508, "text": "<URL>", "dom": "<URL>", "image": "<URL>" } ]
}
```

- `markdown`: every requested page, in order, with no page markers. For one page's text use `pages get <n> --format text`.
- `pages[].text|dom|image` are API URLs: read them with `pages get`, never with curl.
- The page count is known only here — `uploads create` does not return it.

## Errors

Two places carry the API's RFC 9457 problem (`code`, `retry`, `detail`, `traceId`, and for `settings-invalid` also `pointer` — the JSON Pointer of the bad request field — and `allowed`, the valid values):

- a **failed run**: `Result: Failure`, problem in `Data.error`, `<code>: <detail>` in `Message`, `code` also in `Context.errorCode`, the next step its `retry` implies in `Instructions`;
- a **rejected request** (the start call, `runs get`, `pages get`, `uploads *`): the envelope's `Instructions` carries `<code>: <detail>`.

| API `retry` | CLI `ErrorCode` / `Retry` | Do |
|---|---|---|
| `fix-input` | `invalid_argument` / `RetryWillNotFix` (a failed run); for a rejected request, the HTTP class (`invalid_argument`, `not_found`, …) | Change the request using `detail` (and `allowed`), then start one new run |
| `later` | `RetryLater` | Wait, then send the same request once more; on a second `later`, report it |
| `never` | `execution_failed` / `RetryWillNotFix` | Do not retry; report the code and `traceId` |

Common codes (open set — expect others):

| Code | Cause | Fix |
|---|---|---|
| `model-not-found` | Model not in the resolved folder | `models list` in the right folder (SKILL.md Critical Rule 5) |
| `settings-invalid` | Unknown engine, `--layout-model` missing/forbidden, wrong model kind | Use `allowed` / `pointer`; re-read `digitizers list` |
| `settings-conflict` | `--digitization-run-id` on digitize | Pass a `--document-id` |
| `page-range-invalid` | Range outside the document | `detail` states the page count; fix `--page-range` |
| `document-not-found` | Upload expired or deleted | Upload again |
| `digitization-invalid` | `--digitization-run-id` is not a succeeded digitization | Use the run's `digitization.runId` |
| `run-not-found` | Wrong id, or another folder | Same folder as the run |
| `unsupported-media-type` / `file-too-large` | Upload rejected | Convert to PDF/image; split files over 160 MB |
| `idempotency-key-reused` | Same key, different body | New key, or the original body |
| `rate-limited`, `engine-busy`, `digitizer-timeout`, `discovery-unavailable` | Transient (`later`) | Wait, retry once |
| `page-limit-exceeded`, `content-policy`, `folder-access-denied` | `never` | Report; a person must act |

Warnings (in `warnings[]` and `Warning`): `value-unattributed` (value with no evidence — mark unverified), `low-confidence` (classify best-match under `--no-allow-unknown`).
