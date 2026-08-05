# The transformation (ELT) layer — dbt on Snowflake

The transformation layer is a dbt project that runs on **Snowflake**. Loaded
source tables (one per input table) feed the models that produce the process
model. `transformations list/get/create/update/apply/run/status/logs` is the ELT
editor surface:

| Operation | Command |
|-----------|---------|
| List the model tree | `transformations list <app>` |
| Read a file (or save locally) + its ETag | `transformations get <app> <path> [--destination <file>]` |
| Edit an existing file (ETag-guarded) | `transformations update <app> <path> --file <local> --etag '<etag>'` |
| Create a new model file | `transformations create <app> <path> --file <local>` |
| Re-run the **full** transform on loaded data | `transformations apply <app> --wait` |
| Rebuild **one** dev model + dependents | `transformations run <app> --model models/X.sql` |
| Status / logs of the last build | `transformations status <app>` · `transformations logs <app>` |

## Model set for `uipath.custom`

Four template models: **`Event_log`** (built from the source; the events table),
**`Cases`** (aggregates Event_log — one row per case), **`Tags`** and
**`Due_dates`** (ship as safe `where 1=0` stubs depending only on `ref('Cases')`).
`Tags` and `Due_dates` are pre-registered **Case-child** tables — fill their stubs
with real rows keyed on `Case_ID` to get per-case labels (`Tag`/`Tag_type`) or
per-case SLAs (`Expected_date`/`Actual_date`/`On_time`/`Cost`) with **no add-table
needed**. See [`data-model.md`](data-model.md) for when to use
them vs a custom table. `Event_log` builds first and independently. `models/schema/sources.yml` is
generated from the data mapping and lists every input table with **all** its
columns (mapped → TargetName, unmapped → raw source name), so multi-table custom
apps can `source('sources', '<Table>')` any loaded table.

## The #1 gotcha — `Cases.sql` references optional columns

The template `models/Cases.sql` hard-references `Event_log."Case"`,
`"Case_status"`, `"Case_type"`, `"Case_value"`. A minimal mapping
(Case_ID/Activity/timestamp only) doesn't produce them ⇒ dbt
`000904 invalid identifier`. Fix — pull, null the missing refs, push, apply:

```sql
select
    Event_log."Case_ID",
    cast(null as varchar) as "Case",
    cast(null as varchar) as "Case_status",
    cast(null as varchar) as "Case_type",
    cast(null as float)   as "Case_value",
    count(*) as "Event_count"
from {{ source('sources', 'Event_log') }} as Event_log
group by Event_log."Case_ID"
```

A successful run then reports `SUCCESS_WITH_WARNINGS` with repeated
`UserWarning_MissingOptionalEventColumn` — **benign** for a minimal mapping.

## apply vs run; create vs update

- **`apply`** re-runs the **full** transform on already-loaded data — the fix-loop
  verb after a transform-only failure. **Do not re-ingest** for a SQL-only change.
- **`run --model models/X.sql`** rebuilds one dev model and its dependents.
- **`create <path> --file`** adds a **new** model file (PUT without ETag — there is no
  prior version to guard); **`update <path> --file`** edits an **existing** file and
  **requires `--etag`**: the `Data.ETag` the `get` you edited from returned. `update` on
  a missing path 404s — use `create`. A 409/412 means someone replaced the file after
  your `get`: re-`get` for the new content **and** ETag, re-apply your edit on top, then
  `update` with the new `--etag`. You can also inline intermediate logic as CTEs inside
  one model instead of many files.
- Use **`apply --wait`** to block to a terminal state and auto-print the dbt error.

## Snowflake / dbt notes

- **Quoted identifiers are case-sensitive** and must match the mapped `TargetName`
  exactly: `Event_log."Case_ID"`. Reference raw unmapped columns by their source
  name, e.g. `"# Reassignments"`.
- Parse messy source columns in SQL rather than fighting the loader: European
  dates via `try_to_timestamp(col, 'DD-MM-YYYY HH24:MI:SS')` (lenient on single
  digits), decimal-comma numbers via `try_to_double(replace(col, ',', '.'))`.
- **`pm_utils` macros** seen in templates: `as_varchar('literal')` (string
  literal) vs `to_varchar(col)` (cast), `to_timestamp('null')`, `to_boolean('true')`,
  `id()` = `row_number() over (order by (select null))` (surrogate key),
  `datediff('millisecond', a, b)`, `star(source, except=[...])`.
- Build type on `run`: `RunQueries = 0` (all) vs `RunModel = 1` (needs `modelPath`).
