# CLI Reference — `uip documents`

Every command takes `--output json`. Preview CLI builds only (SKILL.md Critical Rule 1).

> **Keys are camelCase.** `Data` is the API's own JSON (`runId`, `result.output`, `digitization.runId`), not PascalCased. Write `--output-filter` expressions against those names, e.g. `--output-filter "result.output"`.

## Shared options

| Option | On | Meaning |
|---|---|---|
| `--folder-path <path>` | every command except `uploads *` and `digitizers list` | Orchestrator folder (e.g. `"Finance/Invoices"`). Omitted → the tenant's Shared folder. |
| `--folder-key <key>` | same | Folder key (GUID), instead of `--folder-path`. Passing both is rejected. |
| `-t, --tenant <tenant-name>` | every command | Tenant; omitted → the `uip login` session. |
| `-l, --limit <number>` / `--offset <number>` | `* list` | Row window (default 50 / 0). `Pagination` in the envelope carries `Returned`, `Limit`, `Offset`, `Total`, `HasMore`. |

## Pointing at another API root (debugging)

`UIPATH_DOCUMENTS_URL` replaces `{baseUrl}/{org}/{tenant}/documents_` with a full API root, e.g. a service on `http://localhost:5000` (a path such as `/my-org/my-tenant/documents_` is kept). Authentication still comes from `uip login`, so **the login token is sent to that URL** — every command prints a `[WARN] UIPATH_DOCUMENTS_URL is set: …` line on stderr.

```bash
UIPATH_DOCUMENTS_URL="<API_ROOT_URL>" uip documents models list --output json
```

- Set it only when the user asks to target a specific Documents API URL, inline on the command as above — never export it, and never point it at a host the user did not name.
- An unusable value (not a URL, not `http`/`https`, a query string or fragment) fails before login with `ErrorCode: configuration_error`; fix or unset the variable.
- An unexpected `[WARN] UIPATH_DOCUMENTS_URL is set` means a leftover export: tell the user, and run `unset UIPATH_DOCUMENTS_URL` only with their go-ahead.

## Discovery

| Command | Output (`Data`) |
|---|---|
| `uip documents capabilities list --output json` | `[{ name, route, status, description?, catalog?, sunset?, reason? }]`. `status`: `available`, `preview`, `deprecated` (+ `sunset`), `not-available` (+ `reason`), `planned` — tolerate other values. |
| `uip documents models list [--capability <extract\|classify>] --output json` | `[{ modelId, name, capability, outputSchema \| classes, createdAt, predefined }]`. Empty → `Instructions` says to pass the model's folder. |
| `uip documents models get <model> [--capability <extract\|classify>] --output json` | One model. `<model>` is a `modelId` or exact `name`; an exact `modelId` wins. A name shared by several models fails with `invalid_argument` listing their ids — pass the id. |
| `uip documents digitizers list [--kind <ocr\|layout>] --output json` | One row per engine: `{ kind: "ocr", engine, model?, description? }` or `{ kind: "layout", engine, description? }`. The only layout engine is `uipath`; the layout list is empty when layout parsing is off for the tenant. Takes no folder. |

**Models.** `outputSchema` (extract) is a JSON Schema: each top-level property is a field group (`type: array` of row objects) or a single field; a sub-group is an array inside its parent's row. `classes` (classify) is `[{ name, description? }]` — every value `segments[].class` can take. A fine-tuned `modelId` (GUID) is one fixed version, `predefined: null`; a newer version is a new id. A predefined model's `modelId` is its catalog slug (`invoices`, `mlclassification`, …), deployed by an administrator into a folder — the Shared folder for calls without one; its `predefined` carries `catalogKey`, `revision` and `lifecycle` (`status` `active` or `deprecated`, with `sunset` and `successor`). Revisions only add fields, so a listed taxonomy stays valid.

## Uploads

Tenant-level: no folder option.

| Command | Output (`Data`) |
|---|---|
| `uip documents uploads create <file> --output json` | `{ documentId, name, size, sha256, createdAt, expiresAt }`. One file, ≤ 160 MB (larger fails locally with `ValidationError`). Media type is detected by the server: an unsupported type or an empty file answers `unsupported-media-type`. No OCR runs. The same bytes uploaded again, by anyone in the tenant, answer the same record (same `documentId`, `name` and `expiresAt`). |
| `uip documents uploads get <document-id> --output json` | Same shape. |
| `uip documents uploads delete <document-id> -y --output json` | `{ documentId, deleted: true }`. Removes the file, every digitization of it and every run made on it; those runs then answer `run-not-found`. Allowed to an uploader of the file or a tenant administrator (others → `upload-access-denied`). **Irreversible**; `-y, --yes` required (the CLI never prompts). |

## Capability runs

`digitize`, `extract` and `classify` each start one run and print the run envelope ([Results Guide](results-guide.md#run-envelope)).

**Document input — exactly one per call** (none or two → `ValidationError`, no request sent):

| Option | Document |
|---|---|
| `--document-id <id>` | a file from `uploads create` |
| `--attachment-id <id>` | an Orchestrator attachment, read in the resolved folder |
| `--page-range <range>` (optional) | pages to read, `1-3,5,8-` syntax; default every page. Order matters: `1,3,2` reads the pages in that order and is a different digitization from `1-3` |

A digitization is not an input: extract and classify find or make their own with the model's settings.

**Run options** (all three):

| Option | Default | Meaning |
|---|---|---|
| `--wait` | off | Poll until final, then print the final run. Without it the run prints as `queued`/`running` with `Instructions` holding the `runs get` command. |
| `--timeout <seconds>` | `300` | Give up waiting after this long (`0` = no limit): `Result: TimeoutError`, exit 4, last-seen run in `Data`. The run continues server-side (SKILL.md Critical Rules 6–7). |
| `--idempotency-key <key>` | none | 1–128 chars. Same key + same body within 24 h returns the run already started (its current state, final or not), not a new one. Same key + different body → `idempotency-key-reused` (422), `pointer` naming the first field that differs. |

### digitize

```bash
uip documents digitize --document-id "<DOCUMENT_ID>" [--page-range <range>] [--ocr-engine <engine>] [--apply-on-pdf <auto|always|never>] [--layout-engine uipath] --wait --output json
```

| Option | Default | Meaning |
|---|---|---|
| `--ocr-engine <engine>` | `auto` | An `engine` from `digitizers list --kind ocr`. `auto` picks per page by the page's alphabet (`uipath` for Latin, `uipath_extended` otherwise) and is reported as `auto` in `Data.engine.ocr.engine`. |
| `--apply-on-pdf <mode>` | `auto` | Whether PDF pages go through OCR: `auto` reads the text layer where a page has one and OCRs the rest; `always` OCRs every page (a PDF whose text layer is wrong); `never` reads the text layer only, so a scanned page yields no text, and no `--layout-engine` can run (`settings-invalid`). Images are always OCR'd. |
| `--layout-engine <engine>` | none | Today only `uipath`: tables as HTML `<table>` with spans, forms, tagged figures and page furniture, layout reading order. Without it, markdown is still produced and tables come as lines of text. There is no `auto` layout engine and no layout model. It runs on OCR output, so not with `--apply-on-pdf never`. |

The same document, settings and `--page-range` digitized again answer the existing run instead of a new one (not served yet: today every digitize call starts a new digitization). `Data.runId` is the digitized document: pass it to `pages get --run-id`. A later extract or classify reuses it only when the model's settings equal these.

### extract

```bash
uip documents extract --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" [--page-range <range>] --wait --output json
```

`--model <model>` (required) — an extract model's `modelId` or exact `name`. Resolved against `models list` in the same folder before the run starts: unknown → `not_found`; a classify model → `invalid_argument`. No engine options: the model brings its own digitization settings, and reuses an earlier digitization of the same document made with them that covers the requested pages.

### classify

```bash
uip documents classify --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" [--split] [--no-allow-unknown] --wait --output json
```

| Option | Default | Meaning |
|---|---|---|
| `--model <model>` | required | A classify model's `modelId` or exact `name`. |
| `--split` | off | Contiguous page ranges, each with a class. Off → exactly one segment for the whole document. |
| `--no-allow-unknown` | allow | Pages matching no class get the best match plus a `low-confidence` warning, instead of `class: null`. |

No confidence threshold option: apply the user's threshold to `segments[].confidence` yourself.

## Runs and pages

| Command | Output (`Data`) |
|---|---|
| `uip documents runs get <run-id> [--wait] [--timeout <seconds>] --output json` | The run envelope; same shape as the start call. A final run prints as for `--wait` (failed → `Result: Failure`). |
| `uip documents pages get <page-number> --run-id <run-id> --format <text\|dom\|image> [--output-file <path>] --output json` | `--run-id` is a digitized document (a digitize `runId` or a `digitization.runId`), readable from any folder; an extract/classify run's own `runId` → `run-not-digitization`. `<page-number>` counts within the digitization, from 1 in the order digitized (`result.pages[].number`); a `--page-range` digitization is a document of its own, so the file's page numbers are not reported. Without `--output-file`: `{ runId, page, format, content }` — `content` is the page's plain text, or its DU DOM (words with `Box` `[top, left, width, height]`, `Polygon`, `OcrConfidence`). With it: `{ runId, page, format, path, sizeBytes }`. **`--format image` requires `--output-file`** — the PNG is `width × height` page pixels (a PDF page at 270 DPI: A4 is 2232 × 3157), the space attribution boxes use. A page outside the digitization → `page-range-invalid`; a digitization still running → `run-not-final` (wait with `runs get`); a failed one → `run-failed`. Today a digitize run serves `--format text` only: `dom` and `image` answer 501 `not-implemented` (exit 1, do not retry). |

## Exit codes

| Exit | `Result` | When |
|---|---|---|
| 0 | `Success` | Includes a succeeded run with warnings (check `Warning`) and a not-yet-final run without `--wait` |
| 1 | `Failure` | A `failed` run, or an API error other than the ones below (404, 409, 5xx, …) |
| 2 | `AuthenticationError` | Not logged in, or 401/403 — run `uip login` |
| 3 | `ValidationError` | Bad options or document input caught locally (nothing sent), or the API rejected the request with 400/422 (`settings-invalid`, `page-range-invalid`, …) |
| 4 | `TimeoutError` | `--wait` ran out; the run keeps going — `runs get <run-id> --wait` |
