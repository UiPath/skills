# `uip pm` — CLI mechanics & conventions

Shared mechanics for every `uip pm` command. See domain references ([`app-types.md`](app-types.md), [`data-model.md`](data-model.md), [`model-editing.md`](model-editing.md), [`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)) for decisions. **Drive Process Mining through the CLI — do not hand-roll the REST API.**

## Command groups

| Group | Verbs | For |
|-------|-------|-----|
| `app-types` | `list`, `get` | Templates ([`app-types.md`](app-types.md)). |
| `apps` | `list`, `create`, `delete`, `publish` | App and lifecycle ([`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)). |
| `apps data-mapping` | `get`, `update` | Input mapping ([`pre-flight.md`](pre-flight.md)). |
| `apps model` | `get`, `update`, `fields list\|set\|remove` | Semantic model ([`model-editing.md`](model-editing.md)). |
| `apps data-model` | `get`, `add-table` | Structural table graph (PK/FK, roles; [`data-model.md`](data-model.md)). |
| `files` | `upload` | Load a data file to an input table. |
| `ingestions` | `create`, `logs` | Parse and load raw data (the LT of ELT). |
| `transformations` | `list`, `get`, `create`, `update`, `apply`, `run`, `status`, `logs` | dbt dev loop ([`transformations.md`](transformations.md)). |
| `query` | `run`, `details`, `percentile`, `rca`, `insights`, `info`, `layout` | Pull numbers ([`querying.md`](querying.md)). |

**Do not confuse models:** `apps model` edits semantic `/model` (field kinds/calculated fields with `apps model fields …`); `apps data-model` edits the structural `/dataModel` table graph (register queryable tables with `apps data-model add-table`).

## The output envelope

Every command prints `Result` (`Success` / `Failure` / `ValidationError`), `Code` (stable machine tag, e.g. `PmAppsCreate`, `PmQueryRun`), `Data` (payload), and `Instructions` (next-step/fix hints on failures — "run `uip login`", "see `uip pm apps list`" — and some successful mutations: `add-table`, `data-mapping update`, `fields set`, which require re-ingest/publish). Exit codes: `0` success, `1` failure, `3` validation (commander rejected a flag before an API call, e.g. unknown `--stage`).

- `--output json|table|…` selects rendering; `--output-filter <JMESPath>` projects/reshapes `Data` (e.g. `"[].{Key:AppTypeKey,Version:Version}"`). `list` commands unwrap API `{ Data: [...] }` for a consistent shape.
- If a command's `--limit` has a default, `--output-filter` requires explicit `--limit` or exits `3` (to avoid filtering only the first page). Only `ingestions logs` has a `pm` default (`100`): pair them, e.g. `ingestions logs <app> --limit 200 --output-filter "[?contains(Message,'error')]"`. `app-types list`, `apps list`, and `query run` have no default and need no extra flag.

## The ETag get-modify-put pattern

Editable resources (`data-mapping`, `model`, `data-model`, `transformations`) use `If-Match` guards; ETag requirements differ:

| | Commands | ETag |
|---|---|---|
| Edited file locally | `apps data-mapping update`, `apps model update`, `transformations update` | `--etag` REQUIRED: use the matching `get`'s ETag. |
| Reads and merges in one command | `apps data-model add-table`, `apps model fields set\|remove` | No `--etag`; guards with the ETag it just read. |

```bash
uip pm apps model get <app> --destination model.json      # prints Data.ETag
# ...edit model.json...
uip pm apps model update <app> --file model.json --etag 'W/"3"'
```

- Get ETags from `get`: editable-resource `get` returns `Data.ETag`, including with `--destination` (which writes only the document). Project it with `--output-filter ETag`.
- The CLI never re-reads ETag immediately before writing; that defeats the guard. Do not work around a rejected write by re-`get`ting only for a fresh ETag.
- On 409 `UserError_ETagFileConflict` / 412: for `update`, re-run `get` for the latest version and ETag, re-apply your change, then update with the new `--etag` (a blind retry fails again). For `add-table` / `fields set|remove`, just re-run; they re-read and re-apply. `Instructions` says which applies.
- `fields set`/`remove` and `model update` return new edit `Versions`; `data-mapping`/`data-model` edits return `IngestionNeeded: true` (below). A resource without an ETag fails rather than writing unguarded.

## Async work — always `--wait`

Run `ingestions create` and `transformations apply` with `--wait` (and `--timeout`) to block to a terminal state, auto-print loader/dbt errors on failure, and exit non-zero. Never hand-roll an `apps list` poll loop.

## Stages — `--stage dev|published`

Every data / transform / query command takes `--stage`, default **`dev`**. Writes (`data-mapping update`, `transformations`, model/data-model edits) are dev-only; `published` is read-only. Develop on `dev` (a subset), publish, then read `--stage published` ([`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)).

## `IngestionNeeded` — the deferred-effect signal

Mapping and data-model edits change raw-data parsing/structure and take effect only on the next `ingestions create`, not `transformations apply` (which only reruns SQL over parsed data). They return `IngestionNeeded: true`. For SQL-only changes, apply; do not re-ingest ([`transformations.md`](transformations.md)).

## Field ids come from `query info`

`query run`/`percentile` bodies require hashed field ids (`F__<Table>__<Col>__<hash>`), not column names. Discover them with `query info`, or use sugar to resolve human names: `query run <app> --group-by <col> --metric <col>:<fn>` (`fn ∈ average|count|sum|min|max`). See [`querying.md`](querying.md) for AST and restrictions.

## Quick Start — CSV → queryable process app

```bash
# 0. Pre-flight (see pre-flight.md): check UTF-8 encoding, delimiter, date format (dd-mm vs mm-dd); strip junk all-empty rows.

# 1. Discover template and target fields
uip pm app-types list --output-filter "[].{Key:AppTypeKey,Version:Version,Name:DefaultName}"

# 2. Create app from mapping (isNotNull/isUnique default per field)
uip pm apps create "My Process" --type uipath.custom --data-mapping ./mapping.json

# 3. Upload and ingest; wait for completion/error
uip pm files upload <appId> ./data.csv --input-table Event_log
uip pm ingestions create <appId> --file-format csv --field-delimiter ";" --encoding utf-8 --wait

# 4. If Cases.sql transform failed: pull, patch, apply (transformations.md)
uip pm transformations get <appId> models/Cases.sql --destination Cases.sql   # note Data.ETag
# ...edit...
uip pm transformations update <appId> models/Cases.sql --file Cases.sql --etag 'W/"639…"'
uip pm transformations apply <appId> --wait

# 4b. If mapping was wrong, fix it in place; don't recreate (pre-flight.md)
uip pm apps data-mapping get <appId> --destination mapping.json              # note Data.ETag
# ...edit...
uip pm apps data-mapping update <appId> --file mapping.json --etag 'W/"639…"'
uip pm ingestions create <appId> --wait          # mapping changes need re-ingest

# 5. Query
uip pm query info <appId>                                   # discover fields/metrics
uip pm query run  <appId> --group-by Service_Component --metric Event_count:average --output table
```