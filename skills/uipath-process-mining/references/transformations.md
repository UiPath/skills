# The transformation (ELT) layer — dbt on Snowflake

The transformation layer is a dbt project on **Snowflake**: loaded source tables (one per input table) feed models that produce the process model. `transformations list/get/create/update/apply/run/status/logs` are the ELT editor surface:

| Operation | Command |
|-----------|---------|
| List model tree | `transformations list <app>` |
| Read a file (or save locally) + its ETag | `transformations get <app> <path> [--destination <file>]` |
| Edit an existing file (ETag-guarded) | `transformations update <app> <path> --file <local> --etag '<etag>'` |
| Create a model file | `transformations create <app> <path> --file <local>` |
| Re-run the full transform on loaded data | `transformations apply <app> --wait` |
| Rebuild one dev model + dependents | `transformations run <app> --model models/X.sql` |
| Status / last-build logs | `transformations status <app>` · `transformations logs <app>` |

## Model set for `uipath.custom`

Four template models: **`Event_log`** (source-built events table), **`Cases`** (aggregates Event_log; one row per case), and **`Tags`** and **`Due_dates`** (safe `where 1=0` stubs depending only on `ref('Cases')`). `Tags` and `Due_dates` are pre-registered **Case-child** tables; fill their stubs with rows keyed on `Case_ID` for per-case labels (`Tag`/`Tag_type`) or SLAs (`Expected_date`/`Actual_date`/`On_time`/`Cost`); no add-table needed. See [`data-model.md`](data-model.md) for when to use them vs a custom table. `Event_log` builds first and independently. Generated `models/schema/sources.yml` lists every input table and column (mapped → TargetName, unmapped → raw source name), so multi-table custom apps can `source('sources', '<Table>')` any loaded table.

## The #1 gotcha — `Cases.sql` references optional columns

Template `models/Cases.sql` hard-references `Event_log."Case"`, `"Case_status"`, `"Case_type"`, and `"Case_value"`. Minimal mappings (Case_ID/Activity/timestamp only) omit these and cause dbt `000904 invalid identifier`. Fix by pulling the model, nulling missing refs, pushing it, then applying:

```sql
select
    Event_log."Case_ID",
    cast(null as varchar) as "Case",
    cast(null as varchar) as "Case_status",
    cast(null as varchar) as "Case_type",
    cast(null as float) as "Case_value",
    count(*) as "Event_count"
from {{ source('sources', 'Event_log') }} as Event_log
group by Event_log."Case_ID"
```

A successful run reports `SUCCESS_WITH_WARNINGS` with repeated `UserWarning_MissingOptionalEventColumn`; this is benign for a minimal mapping.

## apply vs run; create vs update

- **`apply`** re-runs the full transform on loaded data; use it as the fix-loop verb after transform-only failures. Do not re-ingest for SQL-only changes.
- **`run --model models/X.sql`** rebuilds one dev model and its dependents.
- **`create <path> --file`** adds a model file (PUT without ETag; no prior version to guard). **`update <path> --file`** edits an existing file and requires `--etag`, using the `Data.ETag` returned by the `get` you edited from. `update` on a missing path 404s; use `create`. On 409/412, re-`get` the new content and ETag, re-apply your edit, then `update` with the new `--etag`. You can also inline intermediate logic as CTEs inside one model instead of many files.
- Run **`apply --wait`** to block to a terminal state and auto-print the dbt error.

## Snowflake / dbt notes

- **Quoted identifiers are case-sensitive** and must exactly match mapped `TargetName`, e.g. `Event_log."Case_ID"`. Reference raw unmapped columns by source name, e.g. `"# Reassignments"`.
- Parse messy source columns in SQL: European dates with `try_to_timestamp(col, 'DD-MM-YYYY HH24:MI:SS')` (lenient on single digits); decimal-comma numbers with `try_to_double(replace(col, ',', '.'))`.
- Template `pm_utils` macros: `as_varchar('literal')` (string literal) vs `to_varchar(col)` (cast), `to_timestamp('null')`, `to_boolean('true')`, `id()` = `row_number() over (order by (select null))` (surrogate key), `datediff('millisecond', a, b)`, `star(source, except=[...])`.
- Build type on `run`: `RunQueries = 0` (all) vs `RunModel = 1` (needs `modelPath`).