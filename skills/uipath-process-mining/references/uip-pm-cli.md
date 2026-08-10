# `uip pm` — CLI mechanics & conventions

The low-level "how to drive the tool" layer — the shared plumbing every `uip pm`
command uses. The *decisions* — which template, when to add a table, why an app locks
open — live in the domain references ([`app-types.md`](app-types.md),
[`data-model.md`](data-model.md), [`model-editing.md`](model-editing.md),
[`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)). **Drive Process Mining through the
CLI — do not hand-roll the REST API.**

## Command groups

| Group | Verbs | For |
|-------|-------|-----|
| `app-types` | `list`, `get` | Discover/inspect templates ([`app-types.md`](app-types.md)). |
| `apps` | `list`, `create`, `delete`, `publish` | The app itself + its lifecycle ([`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)). |
| `apps data-mapping` | `get`, `update` | The **input mapping** (source table/column → target field) ([`pre-flight.md`](pre-flight.md)). |
| `apps model` | `get`, `update`, `fields list\|set\|remove` | The **semantic** model — fields with their data kinds, calculated fields, metrics, dashboards ([`model-editing.md`](model-editing.md)). |
| `apps data-model` | `get`, `add-table` | The **structural** model — the table graph (PK/FK, roles) that `add-table` edits ([`data-model.md`](data-model.md)). |
| `files` | `upload` | Load a data file to an input table. |
| `ingestions` | `create`, `logs` | Parse + load the raw data (the LT of ELT). |
| `transformations` | `list`, `get`, `create`, `update`, `apply`, `run`, `status`, `logs` | The dbt dev loop ([`transformations.md`](transformations.md)). |
| `query` | `run`, `details`, `percentile`, `rca`, `insights`, `info`, `layout` | Pull numbers out ([`querying.md`](querying.md)). |

> **`apps model` vs `apps data-model` — don't confuse them.** `apps model` is the
> **semantic** model (`/model`); `apps data-model` is the **structural** table graph
> (`/dataModel`). Editing a field's data kind or a calculated field is `apps model
> fields …`; registering a new queryable table is `apps data-model add-table`.

## The output envelope

Every command prints a stable envelope and sets a branchable exit code:

- **`Result`** — `Success` / `Failure` / `ValidationError`; **`Code`** — a stable
  machine tag (`PmAppsCreate`, `PmQueryRun`, …); **`Data`** — the payload;
  **`Instructions`** — a next-step/fix hint, present on failures ("run `uip login`",
  "see `uip pm apps list`") and on some successful mutating commands (`add-table`,
  `data-mapping update`, `fields set`) pointing at the required re-ingest/publish.
- Exit `0` success, `1` failure, `3` validation (commander rejected a flag before any
  API call — e.g. an unknown `--stage`).
- **`--output json|table|…`** picks the rendering; **`--output-filter <JMESPath>`**
  projects/reshapes `Data` (e.g. `"[].{Key:AppTypeKey,Version:Version}"`). `list`
  commands unwrap the API's `{ Data: [...] }` so the shape matches across commands.
- **`--output-filter` on a command whose `--limit` has a default requires an explicit
  `--limit`** — otherwise it exits `3` rather than silently filtering only the first
  page. In `pm` that is **`ingestions logs`** alone (default `100`): pair them, e.g.
  `ingestions logs <app> --limit 200 --output-filter "[?contains(Message,'error')]"`.
  `app-types list` / `apps list` / `query run` declare no `--limit` default, so
  filtering them needs nothing extra.

## The ETag get-modify-put pattern

Every editable resource — `data-mapping`, `model`, `data-model`, `transformations` — is
written `If-Match`-guarded, so a concurrent edit (someone in the UI between your read and
your write) is rejected instead of silently overwritten. **Which side supplies the ETag
splits the commands into two groups — get this wrong and the command won't run.**

| | Commands | ETag |
|---|---|---|
| **You edited the file locally** | `apps data-mapping update`, `apps model update`, `transformations update` | **`--etag` REQUIRED** — the one the matching `get` returned |
| **The command reads and merges in one go** | `apps data-model add-table`, `apps model fields set\|remove` | **No `--etag`** — it guards with the ETag of the read it just did |

```bash
uip pm apps model get <app> --destination model.json      # prints Data.ETag
#   ...edit model.json...
uip pm apps model update <app> --file model.json --etag 'W/"3"'
```

- **Get the ETag from the `get`.** Every `get` of an editable resource returns
  `Data.ETag` (also with `--destination`, which writes only the document to disk).
  Project it with `--output-filter ETag`.
- **The CLI never re-reads the ETag just before writing** — that would make the
  precondition pass no matter who wrote in between, defeating the guard. Do not work
  around a rejected write by re-`get`ting only for a fresh ETag.
- **On a conflict, recovery differs by group.** `update` (409
  `UserError_ETagFileConflict` / 412): re-run the `get` for the latest version **and its
  new ETag**, re-apply your change on top of *that* version, then update again with the
  new `--etag` — a blind re-run just fails again. `add-table` / `fields set|remove`:
  **just re-run** — they re-read and re-apply on top of the other write. `Instructions`
  states which applies.
- `fields set`/`remove` and `model update` return the new edit `Versions`;
  `data-mapping`/`data-model` edits return `IngestionNeeded: true` (see below).
- A resource returned **without** an ETag fails the command rather than writing
  unguarded.

## Async work — always `--wait`

`ingestions create` and `transformations apply` are async. Pass **`--wait`** (with
`--timeout`) to block to a terminal state, auto-print the loader/dbt error on failure,
and exit non-zero. Never hand-roll an `apps list` poll loop.

## Stages — `--stage dev|published`

Every data / transform / query command takes `--stage`, default **`dev`**. Writes
(`data-mapping update`, `transformations`, model/data-model edits) are **dev-only**;
`published` is read-only. Develop on `dev` (a subset), `publish`, then read
`--stage published` ([`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)).

## `IngestionNeeded` — the deferred-effect signal

Mapping and data-model edits change how raw data is *parsed / structured*, so they take
effect only on the **next `ingestions create`**, not on `transformations apply` (which
only re-runs SQL over already-parsed data). Those commands return `IngestionNeeded:
true` as the reminder. A SQL-only change is the opposite — `apply`, don't re-ingest
([`transformations.md`](transformations.md)).

## Field ids come from `query info`

`query run`/`percentile` bodies reference **hashed field ids**
(`F__<Table>__<Col>__<hash>`), not column names. Discover them with `query info`, or —
better — let the sugar resolve human names: `query run <app> --group-by <col> --metric
<col>:<fn>` (`fn ∈ average|count|sum|min|max`). Full AST + restrictions in
[`querying.md`](querying.md).

## Quick Start — CSV → queryable process app

```bash
# 0. Pre-flight (cheap local checks — see pre-flight.md): encoding (UTF-8?),
#    delimiter, date format (dd-mm vs mm-dd), strip junk all-empty rows.

# 1. Discover the template + its target fields
uip pm app-types list --output-filter "[].{Key:AppTypeKey,Version:Version,Name:DefaultName}"

# 2. Create the app from a data mapping (isNotNull/isUnique default per field)
uip pm apps create "My Process" --type uipath.custom --data-mapping ./mapping.json

# 3. Upload + ingest (block until done; prints the loader error on failure)
uip pm files upload <appId> ./data.csv --input-table Event_log
uip pm ingestions create <appId> --file-format csv --field-delimiter ";" --encoding utf-8 --wait

# 4. If the transform failed on Cases.sql: pull → patch → apply (transformations.md)
uip pm transformations get <appId> models/Cases.sql --destination Cases.sql   # note Data.ETag
#   ...edit...
uip pm transformations update <appId> models/Cases.sql --file Cases.sql --etag 'W/"639…"'
uip pm transformations apply <appId> --wait

# 4b. If the MAPPING was wrong instead — fix it in place, don't recreate (pre-flight.md)
uip pm apps data-mapping get <appId> --destination mapping.json              # note Data.ETag
#   ...edit...
uip pm apps data-mapping update <appId> --file mapping.json --etag 'W/"639…"'
uip pm ingestions create <appId> --wait          # a mapping change needs a re-ingest

# 5. Query it
uip pm query info <appId>                                   # discover fields/metrics
uip pm query run  <appId> --group-by Service_Component --metric Event_count:average --output table
```
