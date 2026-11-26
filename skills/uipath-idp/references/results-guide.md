# Results Guide

What `uip documents` prints and how to read it. Commands: [CLI Reference](cli-reference.md).

## Run envelope

`digitize` and `runs get` print the run as `Data`. Every key is always present; keys that depend on the run's state are `null` until then.

```json
{
  "Result": "Success",
  "Code": "DocumentsDigitize",
  "Data": {
    "RunId": "<RUN_ID>",
    "Capability": "Digitize",
    "Status": "Succeeded",
    "Engine": { "Ocr": { "Engine": "auto", "ApplyOnPdf": "Auto" }, "Layout": { "Engine": null } },
    "Result": { "PageCount": 2, "Markdown": "<MARKDOWN>", "Pages": [] },
    "Digitization": { "RunId": "<RUN_ID>" },
    "RunUrl": "<RUN_URL>",
    "Error": null,
    "CreatedAt": "<CREATED_AT>",
    "CompletedAt": "<COMPLETED_AT>"
  }
}
```

| Field | Meaning |
|---|---|
| `Status` | Closed set. `Queued`, `Running` → not final. `Succeeded`, `Failed` → final, never changes again. A run succeeds or fails for the whole document. |
| `Result` | `null` unless `Succeeded`. Always the full result, inline. Not the envelope's `Result`: this one is `Data.Result`. |
| `Engine` | What ran: `Ocr.Engine` (`auto` stays `auto`, a per-page choice), `Ocr.ApplyOnPdf` (`Auto`, `Always` or `Never`) and `Layout.Engine` (`uipath` or `null`). Report it when the user asks how the text was read. |
| `Digitization.RunId` | The digitized document. On a digitize run it equals `RunId`; use it as `pages get --run-id`. |
| `Error` | `null` unless `Failed`: the problem that failed the run ([Errors](#errors)). |
| `RunUrl` | The API route of the run. Read the run with `runs get`, not with curl (SKILL.md Critical Rule 1). |

How the run maps to the CLI result:

| `Data.Status` | `Result` | Envelope extras | Next step |
|---|---|---|---|
| `Queued` / `Running` (no `--wait`) | `Success` | `Instructions`: the `runs get … --wait` command, with the folder | Run it |
| `Succeeded` | `Success` | none | Read `Data.Result` |
| `Failed` | `Failure` | `Message` (`… failed: <Code>: <Detail>`), `ErrorCode`, `Retry`, `Instructions`, `Context.ErrorCode` | [Errors](#errors) |
| still running at `--timeout` | `TimeoutError` | The last-seen run in `Data`; `Instructions`: the `runs get … --wait` command | Run it (SKILL.md Critical Rule 5) |

## Digitize result

```json
"Result": {
  "PageCount": 2,
  "Markdown": "<!-- page: 1 -->\n\n# <HEADING>\n\n<table><tr><th>Description</th><th>Amount</th></tr>…</table>\n\n<!-- page: 2 -->\n\n…",
  "Pages": [ { "Number": 1, "Width": 2232, "Height": 3157, "Text": "<URL>", "Markdown": "<URL>", "Dom": "<URL>" } ]
}
```

- `Markdown`: every requested page, in the order digitized. Each page opens with `<!-- page: N -->`; split on `<!--\s*page:\s*(\d+)\s*-->` to get one page. Tables are HTML `<table>` with the `uipath` layout engine, lines of text without it.
- `Pages[].Number` is the page's number in this digitization, from 1 in the order digitized. A `--page-range` digitization is a document of its own: `--page-range 5-6` gives pages 1 and 2, and the file's page numbers are not reported. Map them back from the range you passed.
- `Pages[].Width` and `Height` are the page's size in pixels.
- `Pages[].Text`, `Markdown` and `Dom` are API URLs. Read them with `pages get`, never with curl.
- The page count is known only here: `uploads create` does not return it.

## Page formats

`pages get` returns one page in the format asked for.

| `--format` | `Content` |
|---|---|
| `text` | The page's plain text, in reading order |
| `markdown` | The page's part of `Result.Markdown` |
| `dom` | A JSON document holding the page: its words, each with its box on the page |

Use `text` or `markdown` to read a page, `dom` to locate a word on the page. With `--output-file`, the content goes to the file and `Data` holds its `Path` and `SizeBytes` instead.

## Errors

The API answers a problem with a `Code`, a `Retry` class and a `Detail`; `settings-invalid` also carries `Pointer` (the request field at fault) and `Allowed` (the valid values). The CLI shows it in one of two places:

- a **failed run**: `Result: Failure`, the problem in `Data.Error`, `<Code>: <Detail>` in `Message`, the code in `Context.ErrorCode`, the next step in `Instructions`;
- a **rejected request** (the start call, `runs get`, `pages get`, `uploads create`, a discovery call): `Result: Failure` or `ValidationError`, `Instructions` carrying `HTTP <status>: <title>: <detail>`, the code in `Context.ErrorCode`, the status in `Context.HttpStatus`.

Act on the envelope's `Retry`:

| `Data.Error.Retry` | CLI `ErrorCode` / `Retry` on a failed run | Do |
|---|---|---|
| `FixInput` | `invalid_argument` / `RetryWillNotFix` | Change the request using `Detail` (and `Allowed`), then start one new run |
| `Later` | `server_error` / `RetryLater` | Wait, then send the same request once more; on a second `Later`, report it |
| `Never` | `execution_failed` / `RetryWillNotFix` | Do not retry; report the code and the `RunId` |

Common codes (an open set: expect others):

| Code | Cause | Fix |
|---|---|---|
| `settings-invalid` | An unknown OCR or layout engine, or a layout engine with `--apply-on-pdf never` | Use `Allowed` and `Pointer`; re-read `discovery digitization-engines get` |
| `page-range-invalid` | A range outside the document, or a page outside the digitization on `pages get` | `Detail` states the page count; fix `--page-range` or the page number |
| `document-not-found` | The upload expired, or it was uploaded to another folder | Use its folder; upload again only when it expired |
| `run-not-found` | A wrong id, another folder, or a run whose output has expired | Pass the folder the run was started in |
| `run-not-final` | `pages get` while the digitization is running | `runs get --wait`, then read the page |
| `run-failed` | `pages get` on a failed digitization | Read its error with `runs get`; start a new run only when the cause is fixed |
| `unsupported-media-type`, `file-too-large` | The upload was rejected | Convert to PDF or an image; split a file over 160 MB |
| `upload-unavailable-for-tenant` | Uploads are not enabled for the tenant | Report it: an upload is the only way to pass a document |
| `folder-access-denied` | The caller may not use that folder | Report it; a person must grant access |
| `unauthenticated` | The token was refused | Run `uip login`, then send the same request once more |
| `api-version-invalid` | The CLI and the API disagree on the API version | Update `uip`; do not work around it |
| `rate-limited`, `discovery-unavailable` | Transient | Wait, retry once |
| `upstream-rejected` | A fault inside the service, not in the request | Report the code and the `RunId`; do not retry |
