# Results Guide

What `uip documents` prints and how to read it. Commands: [CLI Reference](cli-reference.md).

## Run envelope

`digitize` and `runs get` print the run as `Data`. Every key is always present; keys that depend on the run's state are `null` until then.

```json
{
  "Result": "Success",
  "Code": "DocumentsDigitize",
  "Data": {
    "runId": "<RUN_ID>",
    "capability": "digitize",
    "status": "succeeded",
    "engine": { "modelId": null, "ocr": { "engine": "auto", "applyOnPdf": "auto" }, "layout": { "engine": null } },
    "result": { "pageCount": 2, "markdown": "<MARKDOWN>", "pages": [] },
    "digitization": { "runId": "<RUN_ID>" },
    "runUrl": "<RUN_URL>",
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
| `result` | `null` unless `succeeded`. Always the full result, inline. |
| `engine` | What ran: `ocr.engine` (`auto` stays `auto`, a per-page choice), `ocr.applyOnPdf` and `layout.engine` (`uipath` or `null`). Report it when the user asks how the text was read. |
| `digitization.runId` | The digitized document. On a digitize run it equals `runId`; use it as `pages get --run-id`. |
| `warnings[]` | Typed problems, the same shape as `error` without `status`. Also summarised in the envelope's `Warning`. |
| `error` | `null` unless `failed`: the problem that failed the run ([Errors](#errors)). |
| `runUrl` | The API route of the run. Read the run with `runs get`, not with curl (SKILL.md Critical Rule 1). |

How the run maps to the CLI result:

| `Data.status` | `Result` | Envelope extras | Next step |
|---|---|---|---|
| `queued` / `running` (no `--wait`) | `Success` | `Instructions`: the `runs get … --wait` command, with the folder | Run it |
| `succeeded` | `Success` | `Warning` when `warnings[]` is not empty | Read `result` |
| `failed` | `Failure` | `Message` (`… failed: <code>: <detail>`), `ErrorCode`, `Retry`, `Instructions`, `Context.ErrorCode` | [Errors](#errors) |
| still running at `--timeout` | `TimeoutError` | The last-seen run in `Data`; `Instructions`: the `runs get … --wait` command | Run it (SKILL.md Critical Rule 5) |

## Digitize result

```json
"result": {
  "pageCount": 2,
  "markdown": "<!-- page: 1 -->\n\n# <HEADING>\n\n<table><tr><th>Description</th><th>Amount</th></tr>…</table>\n\n<!-- page: 2 -->\n\n…",
  "pages": [ { "number": 1, "width": 2232, "height": 3157, "text": "<URL>", "markdown": "<URL>", "dom": "<URL>" } ]
}
```

- `markdown`: every requested page, in the order digitized. Each page opens with `<!-- page: N -->`; split on `<!--\s*page:\s*(\d+)\s*-->` to get one page. Tables are HTML `<table>` with the `uipath` layout engine, lines of text without it.
- `pages[].number` is the page's number in this digitization, from 1 in the order digitized. A `--page-range` digitization is a document of its own: `--page-range 5-6` gives pages 1 and 2, and the file's page numbers are not reported. Map them back from the range you passed.
- `pages[].width` and `height` are the page's size in pixels.
- `pages[].text`, `markdown` and `dom` are API URLs. Read them with `pages get`, never with curl.
- The page count is known only here: `uploads create` does not return it.

## Page formats

`pages get` returns one page in the format asked for.

| `--format` | `content` |
|---|---|
| `text` | The page's plain text, in reading order |
| `markdown` | The page's part of `result.markdown` |
| `dom` | A JSON document holding the page: its words, each with its box on the page |

Use `text` or `markdown` to read a page, `dom` to locate a word on the page. With `--output-file`, the content goes to the file and `Data` holds its `path` and `sizeBytes` instead.

## Errors

The API answers a problem with a `code`, a `retry` class and a `detail`; `settings-invalid` also carries `pointer` (the request field at fault) and `allowed` (the valid values). The CLI shows it in one of two places:

- a **failed run**: `Result: Failure`, the problem in `Data.error`, `<code>: <detail>` in `Message`, the code in `Context.ErrorCode`, the next step in `Instructions`;
- a **rejected request** (the start call, `runs get`, `pages get`, `uploads create`, a discovery call): `Result: Failure` or `ValidationError`, `Instructions` carrying `HTTP <status>: <title>: <detail>`, the code in `Context.ErrorCode`, the status in `Context.HttpStatus`.

Act on the envelope's `Retry`:

| API `retry` | CLI `ErrorCode` / `Retry` on a failed run | Do |
|---|---|---|
| `fix-input` | `invalid_argument` / `RetryWillNotFix` | Change the request using `detail` (and `allowed`), then start one new run |
| `later` | `server_error` / `RetryLater` | Wait, then send the same request once more; on a second `later`, report it |
| `never` | `execution_failed` / `RetryWillNotFix` | Do not retry; report the code and the `runId` |

Common codes (an open set: expect others):

| Code | Cause | Fix |
|---|---|---|
| `settings-invalid` | An unknown OCR or layout engine, or a layout engine with `--apply-on-pdf never` | Use `allowed` and `pointer`; re-read `discovery digitization-engines list` |
| `page-range-invalid` | A range outside the document, or a page outside the digitization on `pages get` | `detail` states the page count; fix `--page-range` or the page number |
| `document-not-found` | The upload expired, or it was uploaded to another folder | Use its folder; upload again only when it expired |
| `run-not-found` | A wrong id, another folder, or a run whose output has expired | Pass the folder the run was started in |
| `run-not-final` | `pages get` while the digitization is running | `runs get --wait`, then read the page |
| `run-failed` | `pages get` on a failed digitization | Read its error with `runs get`; start a new run only when the cause is fixed |
| `unsupported-media-type`, `file-too-large` | The upload was rejected | Convert to PDF or an image; split a file over 160 MB |
| `upload-unavailable-for-tenant` | Uploads are not enabled for the tenant | Report it: an upload is the only way to pass a document |
| `not-supported-yet` (501) | The service does not run that input or option yet | Follow `detail`, or report it; do not retry (SKILL.md Critical Rule 9) |
| `folder-access-denied` | The caller may not use that folder | Report it; a person must grant access |
| `unauthenticated` | The token was refused | Run `uip login`, then send the same request once more |
| `api-version-invalid` | The CLI and the API disagree on the API version | Update `uip`; do not work around it |
| `rate-limited`, `discovery-unavailable` | Transient | Wait, retry once |
| `upstream-rejected` | A fault inside the service, not in the request | Report the code and the `runId`; do not retry |

Warnings come in `Data.warnings[]` and are summarised in the envelope's `Warning`. Report them next to the result; a run with warnings is still `succeeded`.
