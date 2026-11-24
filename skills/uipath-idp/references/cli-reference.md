# CLI Reference — `uip documents`

Every command takes `--output json`. Preview builds of `uip` only (SKILL.md Critical Rule 1).

> **Keys are camelCase.** `Data` is the API's own JSON (`runId`, `result.markdown`, `digitization.runId`), not PascalCased. Write `--output-filter` expressions against those names, e.g. `--output-filter "result.pageCount"`.

## Shared options

| Option | On | Meaning |
|---|---|---|
| `--folder-path <path>` | `uploads create`, `digitize`, `runs get`, `pages get` (required); `discovery capabilities list` (optional) | Orchestrator folder, e.g. `"Finance/Invoices"`. |
| `--folder-key <key>` | same | Folder key (GUID), instead of `--folder-path`. Passing both is rejected. |
| `-l, --limit <number>` / `--offset <number>` | `* list` | Row window (default 50 / 0). `Pagination` in the envelope carries `Returned`, `Limit`, `Offset`, `Total`, `HasMore`. |

A required folder that is missing fails locally: `Result: ValidationError`, `Message: No folder given.`, nothing sent. `discovery digitization-engines list` takes no folder.

## Discovery

| Command | Output (`Data`) |
|---|---|
| `uip documents discovery capabilities list --output json` | `[{ name, route, status, description?, catalog?, inputs?, sunset?, reason? }]`. `status`: `available`, `preview`, `deprecated` (with `sunset`), `not-available` (with `reason`), `planned`. Tolerate other values. |
| `uip documents discovery digitization-engines list [--kind <ocr\|layout>] --output json` | One row per engine: `{ kind, engine, model?, description? }`. OCR engines include `auto`, which picks an engine per page by the page's alphabet. The only layout engine is `uipath`; the layout rows are absent when layout parsing is off for the tenant. |

## Uploads

```bash
uip documents uploads create "<FILE_PATH>" --folder-path "<FOLDER_PATH>" --output json
```

`Data`: `{ documentId, name, size, createdAt, expiresAt }`.

- One file per call, up to 160 MB; a larger file fails locally with `ValidationError`.
- Accepted: PDF, PNG, JPEG, TIFF, GIF, BMP. The type is read from the file's bytes; anything else answers `unsupported-media-type`.
- No OCR runs on upload.
- The `documentId` works only in the folder it was uploaded to.
- There is no command to read, list, download or delete an upload; it expires at `expiresAt`.

## Digitize

```bash
uip documents digitize --document-id "<DOCUMENT_ID>" --folder-path "<FOLDER_PATH>" [--page-range <RANGE>] [--ocr-engine <ENGINE>] [--apply-on-pdf <auto|always|never>] [--layout-engine uipath] --wait --timeout <SECONDS> --output json
```

Starts one run and prints the run envelope ([Results Guide](results-guide.md#run-envelope)).

**Document input: exactly one per call** (none or both → `ValidationError`, nothing sent):

| Option | Document |
|---|---|
| `--document-id <id>` | A file from `uploads create`, in the same folder |
| `--attachment-id <id>` | An Orchestrator attachment, read in the resolved folder |
| `--page-range <range>` (optional) | Pages to read, `1-3,5,8-` syntax; default every page. Order matters: `1,3,2` reads the pages in that order |

**Digitization options:**

| Option | Default | Meaning |
|---|---|---|
| `--ocr-engine <engine>` | `auto` | An `engine` from `discovery digitization-engines list --kind ocr`. `auto` picks per page by the page's alphabet and is reported as `auto` in `Data.engine.ocr.engine`. |
| `--apply-on-pdf <mode>` | `auto` | Whether PDF pages go through OCR. `auto` reads the text layer where a page has one and OCRs the rest; `always` OCRs every page (for a PDF whose text layer is wrong); `never` reads the text layer only, so a scanned page yields no text. Images are always OCR'd. |
| `--layout-engine <engine>` | none | Only `uipath`: tables as HTML `<table>` with row and column spans, forms, tagged figures and page furniture, in layout reading order. Without it, markdown is still produced and tables come as lines of text. Runs on OCR output, so not with `--apply-on-pdf never` (`settings-invalid`). |

**Run options:**

| Option | Default | Meaning |
|---|---|---|
| `--wait` | off | Poll until the run is final, then print it. Without it the run prints as `queued` or `running`, with the `runs get` command to read it later in `Instructions`. |
| `--timeout <seconds>` | `300` | With `--wait`: give up after this long (`0` = no limit). `Result: TimeoutError`, exit 4, the last-seen run in `Data`. The run continues on the server (SKILL.md Critical Rules 5 and 6). |
| `--idempotency-key <key>` | none | Up to 128 characters. Asks the service to answer the run already started for the same key and body within 24 hours, instead of starting a new one. |

`Data.runId` is the digitized document: pass it to `pages get --run-id`.

## Runs and pages

```bash
uip documents runs get "<RUN_ID>" --folder-path "<FOLDER_PATH>" [--wait] [--timeout <SECONDS>] --output json
uip documents pages get <PAGE_NUMBER> --run-id "<RUN_ID>" --format <text|markdown|dom> --folder-path "<FOLDER_PATH>" [--output-file "<OUTPUT_PATH>"] --output json
```

**`runs get`** prints the run envelope, the same shape as the start call. A final run prints as it does under `--wait` (a failed run is `Result: Failure`). Pass the folder the run was started in; another folder answers `run-not-found`.

**`pages get`** reads one page of a digitized document.

| Part | Meaning |
|---|---|
| `<page-number>` | Counts within the digitization, from 1 in the order digitized (`result.pages[].number`). A `--page-range` digitization is a document of its own: the file's page numbers are not reported. |
| `--run-id <id>` | A digitize run's `runId` (equal to its `digitization.runId`). |
| `--format text` | The page's plain text. |
| `--format markdown` | The page's markdown, as in `result.markdown`. |
| `--format dom` | The page's DOM: its words with their boxes. |
| `--output-file <path>` | Write the page to this file instead of printing it; the DOM is written as JSON. |

`Data` without `--output-file`: `{ runId, page, format, content }`. With it: `{ runId, page, format, path, sizeBytes }`.

A page outside the digitization answers `page-range-invalid`; a digitization still running answers `run-not-final` (wait with `runs get --wait`); a failed one answers `run-failed`.

## Exit codes

| Exit | `Result` | When |
|---|---|---|
| 0 | `Success` | Includes a succeeded run with warnings (check `Warning`) and a not-yet-final run printed without `--wait` |
| 1 | `Failure` | A `failed` run, or an API error other than the ones below |
| 2 | `AuthenticationError` | Not logged in, or the token was refused: run `uip login` |
| 3 | `ValidationError` | Bad options, a missing folder or a bad document input caught locally (nothing sent), or the API rejected the request as invalid |
| 4 | `TimeoutError` | `--wait` ran out; the run keeps going: read it with `runs get --wait` |
