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
    "engine": { "modelId": "invoices", "ocr": { "engine": "uipath", "applyOnPdf": "auto" }, "layout": { "engine": null } },
    "result": { "output": { } },
    "digitization": { "runId": "<DIGITIZATION_RUN_ID>" },
    "runUrl": "https://cloud.uipath.com/<ORG>/<TENANT>/documents_/runs/<RUN_ID>?api-version=1.0",
    "warnings": [],
    "error": null,
    "createdAt": "<CREATED_AT>",
    "completedAt": "<COMPLETED_AT>"
  }
}
```

| Field | Meaning |
|---|---|
| `status` | Closed set. `queued`, `running` → not final. `succeeded`, `failed` → final, never changes again. A run succeeds or fails for the whole document. |
| `capability` | `digitize`, `extract` or `classify` — says which `result` shape to read. |
| `result` | `null` unless `succeeded`. Always the full result, inline. |
| `engine` | What ran, set from the first answer: `modelId` (extract/classify), and the digitization's `ocr.engine` (`auto` stays `auto`, a per-page choice), `ocr.applyOnPdf` and `layout.engine` (`uipath` or `null`). Report it when the user asks how a value was produced. |
| `digitization.runId` | The digitized document this run read, set from the first answer. Use as `pages get --run-id`; attribution pages count within it. On a digitize run it equals `runId`. Readable from any folder. |
| `warnings[]` | Typed problems, same shape as `error` but without `status`, with `pointer` into `result` (e.g. `/output/Invoice/0/Currency`). Also summarised in the envelope's `Warning`. |
| `runUrl` | The API route of the run. Read it with `runs get <runId>`, not with curl (SKILL.md Critical Rule 1). |

There is no trace id in the body: the API returns it in the `traceparent` response header, which the CLI does not print; quote the `runId` when reporting a failure.

How the envelope maps to the CLI result:

| `Data.status` | `Result` | Envelope extras | Next step |
|---|---|---|---|
| `queued` / `running` (no `--wait`) | `Success` | `Instructions`: the `runs get … --wait` command | Run it |
| `succeeded` | `Success` | `Warning` if `warnings[]` is non-empty | Read `result` |
| `failed` | `Failure` | `Message` (`… failed: <code>: <detail>`), `ErrorCode`, `Retry`, `Instructions` (next step), `Context.errorCode` | [Errors](#errors) |
| still running at `--timeout` | `TimeoutError` | last-seen run in `Data` | `runs get <runId> --wait` (SKILL.md Critical Rule 6) |

## Extract result

`result.output` follows the model's `outputSchema`: a field group is an **array of rows**, a row has one key per field, a top-level field sits directly under `output`, a sub-group is an array inside its parent's row. Every taxonomy field is present, never omitted.

```json
"output": {
  "Invoice": [
    { "Invoice number": { "value": "INV-1043", "confidence": 0.99,
                          "attribution": [{ "page": 1, "box": { "x": 1840, "y": 220, "width": 300, "height": 48 }, "text": "INV-1043" }] },
      "Total amount":   { "value": 3180.5, "confidence": 0.96,
                          "attribution": [{ "page": 2, "box": { "x": 1900, "y": 2950, "width": 360, "height": 56 }, "text": "3,180.50" }] },
      "Currency":       { "value": null, "confidence": null, "attribution": [] } }
  ]
}
```

| Key | Meaning |
|---|---|
| `value` | Typed per the taxonomy. `null` = the model found nothing. |
| `confidence` | Model score, `0`–`1`; `null` when the model gives none. |
| `attribution[]` | One entry per region the value came from (may span lines or pages); empty when `value` is `null`. |
| `attribution[].page` | Page number in the digitized document (`digitization.runId`), from 1 in the order digitized — the `n` of `pages get`. When the digitization is a whole packet (classify, then extract a segment), it counts within the packet, not within the segment. |
| `attribution[].box` | `{ x, y, width, height }` in that page's pixels (`pages[].width × height`), origin top left. The DOM's `Box` is the same rectangle as `[top, left, width, height]`. |
| `attribution[].text` | Source text as OCR read it (`$3,180.50`); may differ in form from `value` (`3180.5`). |

Field names contain spaces and capitals. Quote them in JMESPath: `--output-filter 'result.output.Invoice[0]."Total amount".value'`.

### Reporting extracted values

1. One line per field: group / field name, `value`, `confidence`. Group rows of a repeating group (line items) as a table.
2. `value: null` → "not found". Never fill it in (SKILL.md Critical Rule 10).
3. Non-null `value` with empty `attribution` (a `value-unattributed` warning) → mark it **unverified**.
4. Apply a confidence threshold only if the user set one; then list the fields under it separately.
5. Say which model ran (`engine.modelId`) and which pages were read when `--page-range` was used.
6. `value-unattributed` / `low-confidence` warnings → name the field or segment (the warning's `pointer`) next to its value.

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
- `pageRange` counts in the file's pages and is directly usable as `--page-range` on extract with the same `--document-id`; the packet's digitization is reused when the extract model's settings match the classifier's.

## Digitize result

```json
"result": {
  "pageCount": 2,
  "markdown": "<!-- page: 1 -->\n\n# NORTHWIND SUPPLIES\n\n<table><tr><th>Description</th><th>Amount</th></tr>…</table>\n\n<!-- page: 2 -->\n\n…",
  "pages": [ { "number": 1, "width": 2232, "height": 3157, "text": "<URL>", "dom": "<URL>", "image": "<URL>" } ]
}
```

- `markdown`: every requested page, in the order digitized. Each page opens with `<!-- page: N -->` (split on `<!--\s*page:\s*(\d+)\s*-->` to get one page); running heads and page numbers come as `<!-- page-header: … -->` / `<!-- page-footer: … -->`. Tables are HTML `<table>` with the `uipath` layout engine, lines of text without it. For one page's text use `pages get <n> --format text`.
- `pages[].number` is the page's number in this digitization, from 1 in the order digitized. A `--page-range` digitization is a document of its own: `--page-range 5-6` gives pages 1, 2, and the file's page numbers are not reported — map them back from the range you passed. A PDF page is rendered at 270 DPI; an image keeps its own size.
- `pages[].text|dom|image` are API URLs: read them with `pages get`, never with curl.
- The page count is known only here — `uploads create` does not return it.

## Errors

Two places carry the API's RFC 9457 problem (`code`, `retry`, `status`, `detail`, and for `settings-invalid` also `pointer` — the JSON Pointer of the bad request field — and `allowed`, the valid values; `successor` on `model-retired`):

- a **failed run**: `Result: Failure`, problem in `Data.error`, `<code>: <detail>` in `Message`, `code` also in `Context.errorCode`, the next step its `retry` implies in `Instructions`;
- a **rejected request** (the start call, `runs get`, `pages get`, `uploads *`): the envelope's `Instructions` carries `<code>: <detail>`.

| API `retry` | CLI `ErrorCode` / `Retry` | Do |
|---|---|---|
| `fix-input` | `invalid_argument` / `RetryWillNotFix` (a failed run); for a rejected request, the HTTP class (`invalid_argument`, `not_found`, …) | Change the request using `detail` (and `allowed`), then start one new run |
| `later` | `RetryLater` | Wait, then send the same request once more; on a second `later`, report it |
| `never` | `execution_failed` / `RetryWillNotFix` | Do not retry; report the code and the `runId` |

Common codes (open set — expect others):

| Code | Cause | Fix |
|---|---|---|
| `model-not-found` | Model not in the resolved folder | `models list` in the right folder (SKILL.md Critical Rule 5) |
| `model-retired` (410) | A retired predefined model | Use `successor` when set, else another model from `models list` |
| `settings-invalid` | Unknown OCR or layout engine (only `uipath`), a layout engine with `applyOnPdf: never`, wrong model kind, unknown option in the body | Use `allowed` / `pointer`; re-read `digitizers list` |
| `engine-unavailable-for-tenant` | An engine the catalog knows but the tenant may not use | Pick another engine from `digitizers list` |
| `page-range-invalid` | Range outside the document, or a page outside the digitization on `pages get` | `detail` states the page count; fix `--page-range` / the page number |
| `document-not-found` | Upload expired or deleted, or an attachment not in the folder | Upload again |
| `run-not-found` | Wrong id, another folder (extract/classify), or the upload was deleted | Same folder as the run |
| `run-not-digitization` | `pages get` on an extract/classify run's own `runId` | Use its `digitization.runId` |
| `run-not-final` (409, `later`) | `pages get` while the digitization runs | `runs get <digitization.runId> --wait`, then read the page |
| `run-failed` (409, `never`) | `pages get` on a failed digitization | Report it; start a new run only if the cause is fixed |
| `not-implemented` (501, `never`) | `pages get --format dom\|image` on a digitize run: only page text is served today | Read `--format text` or `result.markdown` |
| `unsupported-media-type` / `file-too-large` | Upload rejected | Convert to PDF/image; split files over 160 MB |
| `idempotency-key-reused` (422) | Same key, different body | New key, or the original body; `pointer` names the field that differs |
| `api-version-invalid` | The CLI and the API disagree on `api-version` | Update `uip`; do not work around it |
| `rate-limited`, `engine-busy`, `digitizer-timeout`, `discovery-unavailable` | Transient (`later`) | Wait, retry once |
| `page-limit-exceeded` (over 2,000 pages), `content-policy`, `folder-access-denied`, `upload-access-denied` | `never` | Report; a person must act |

Warnings (in `warnings[]` and `Warning`): `value-unattributed` (value with no evidence — mark unverified), `low-confidence` (classify best-match under `--no-allow-unknown`).
