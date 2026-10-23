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
| `uip documents models list [--capability <extract\|classify>] --output json` | `[{ modelId, name, capability, outputSchema \| classes, createdAt }]`. Empty → `Instructions` says to pass the model's folder. |
| `uip documents models get <model> [--capability <extract\|classify>] --output json` | One model. `<model>` is a `modelId` or exact `name`; an exact `modelId` wins. A name shared by several models fails with `invalid_argument` listing their ids — pass the id. |
| `uip documents digitizers list [--kind <ocr\|layout>] --output json` | One row per engine: `{ kind: "ocr", engine, model?, description? }` or `{ kind: "layout", engine, byoSupported, description?, defaultModel?, models?: [{ modelId, modelSubscriptionType }] }`. Takes no folder. |

**Models.** `outputSchema` (extract) is a JSON Schema: each top-level property is a field group (`type: array` of row objects) or a single field; a sub-group is an array inside its parent's row. `classes` (classify) is `[{ name, description? }]` — every value `segments[].class` can take. A fine-tuned `modelId` (GUID) is one fixed version; a newer version is a new id. Public endpoint models (`invoices`, `mlClassifier`, …) are listed in the Shared folder.

## Uploads

Tenant-level: no folder option.

| Command | Output (`Data`) |
|---|---|
| `uip documents uploads create <file> --output json` | `{ documentId, name, size, sha256, expiresAt }`. One file, ≤ 160 MB (larger fails locally with `ValidationError`). Media type is detected by the server: an unsupported type answers `unsupported-media-type`. No OCR runs. |
| `uip documents uploads get <document-id> --output json` | Same shape. |
| `uip documents uploads delete <document-id> -y --output json` | `{ documentId, deleted: true }`. Removes the file and all its digitizations. **Irreversible**; `-y, --yes` required (the CLI never prompts). |

## Capability runs

`digitize`, `extract` and `classify` each start one run and print the run envelope ([Results Guide](results-guide.md#run-envelope)).

**Document input — exactly one per call** (none or two → `ValidationError`, no request sent):

| Option | Document |
|---|---|
| `--document-id <id>` | a file from `uploads create` |
| `--attachment-id <id>` | an Orchestrator attachment |
| `--digitization-run-id <id>` | a digitized document: a digitize run's `runId`, or any run's `digitization.runId`. Skips OCR. **Not on `digitize`.** |
| `--page-range <range>` (optional) | pages to read, `1-3,5,8-` syntax; default every page |

**Run options** (all three):

| Option | Default | Meaning |
|---|---|---|
| `--wait` | off | Poll until final, then print the final run. Without it the run prints as `queued`/`running` with `Instructions` holding the `runs get` command. |
| `--timeout <seconds>` | `300` | Give up waiting after this long (`0` = no limit): `Result: TimeoutError`, exit 4, last-seen run in `Data`. The run continues server-side (SKILL.md Critical Rules 6–7). |
| `--idempotency-key <key>` | none | ≤ 128 chars. Same key + same body within 24 h returns the run already started, not a new one. Same key + different body → `idempotency-key-reused`. |

### digitize

```bash
uip documents digitize --document-id "<DOCUMENT_ID>" [--page-range <range>] [--ocr-engine <engine>] [--layout-engine <engine>] [--layout-model <model>] --wait --output json
```

| Option | Default | Meaning |
|---|---|---|
| `--ocr-engine <engine>` | `auto` | An `engine` from `digitizers list --kind ocr`. `auto` lets the service choose; the choice is reported in `Data.engine.ocr.engine`. |
| `--layout-engine <engine>` | none | An `engine` from `digitizers list --kind layout`. Markdown is produced either way. |
| `--layout-model <model>` | — | **Required with `gemini` and `gpt`, rejected with every other engine.** One of that engine's `models[].modelId`; `defaultModel` is the recommended one. |

`Data.runId` is the digitized document: pass it as `--digitization-run-id` and to `pages get --run-id`.

### extract

```bash
uip documents extract --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" [--page-range <range>] --wait --output json
```

`--model <model>` (required) — an extract model's `modelId` or exact `name`. Resolved against `models list` in the same folder before the run starts: unknown → `not_found`; a classify model → `invalid_argument`. No engine options: the model brings its own digitization settings, and reuses an earlier digitization of the same file made with them.

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
| `uip documents pages get <page-number> --run-id <run-id> --format <text\|dom\|image> [--output-file <path>] --output json` | `--run-id` is a digitized document (a digitize `runId` or a `digitization.runId`). Without `--output-file`: `{ runId, page, format, content }` — `content` is the page's plain text, or its DU DOM (words with `Box`, `Polygon`, `OcrConfidence`). With it: `{ runId, page, format, path, sizeBytes }`. **`--format image` requires `--output-file`** — the PNG is `width × height` page pixels, the space attribution boxes use. A page outside the document → `page-range-invalid`. |

## Exit codes

| Exit | `Result` | When |
|---|---|---|
| 0 | `Success` | Includes a `partial` run (check `Warning`) and a not-yet-final run without `--wait` |
| 1 | `Failure` | A `failed` run, or an API error other than the ones below (404, 409, 5xx, …) |
| 2 | `AuthenticationError` | Not logged in, or 401/403 — run `uip login` |
| 3 | `ValidationError` | Bad options or document input caught locally (nothing sent), or the API rejected the request with 400/422 (`settings-invalid`, `page-range-invalid`, …) |
| 4 | `TimeoutError` | `--wait` ran out; the run keeps going — `runs get <run-id> --wait` |
