# Data model — making tables queryable (the add-table pattern)

Process Mining is **case-centric**: a table is queryable only if it is the `Cases` root or reaches `Cases` through a foreign key. A disconnected standalone dbt model is rejected at query time (`UserError_TableIsDeleted`).

## Two models — do not confuse them

| Model | Endpoint | Shape | Role |
|-------|----------|-------|------|
| **Data model** (structural) | `/apps/{id}/{stage}/dataModel` | `tables[]` of `{ type, name, primaryKey, foreignKeys }` | Defines tables and links; edited by `apps data-model add-table`, read by `apps data-model get`. |
| **Semantic model** | `/apps/{id}/{stage}/model` | `Processes` / `Metrics` / `Tables[].Fields[]` | Field-level view for `query info` and `apps model get`; edited with `apps model fields …` ([`model-editing.md`](model-editing.md)). |

Don't hand-author the semantic model's per-column fields; edit the structural model. `applyCurrentDatamodel` derives semantic fields while reconciling changes and preserving semantic edits (calculated fields, metrics, data-kind overrides); `add-table` does both.

## The built-in Case-child tables — use these before adding your own

The `uipath.custom` template provides `Cases`, `Event_log`, `Tags`, and `Due_dates`. Check whether your data fits the extension tables before adding a custom one.

| Table | PK / link | Fields | Use |
|-------|-----------|--------|-----|
| **Cases** | `Case_ID` (root) | case attributes | One row per process instance; root for links. |
| **Event_log** | FK→Cases | activity, timestamp, resource… | One row per activity; drives the process graph and is not directly group-by-able. |
| **Tags** | `Tag_ID`, FK→Cases | `Tag` (label), `Tag_type` (category) | Many categorical labels per case; filter/group cases by tags. |
| **Due_dates** | `Due_date_ID`, FK→Cases | `Due_date`/`Due_date_type`, `Expected_date`, `Actual_date`, `On_time` (bool), `Cost` (currency), `Difference` (duration) | Per-case deadlines/milestones; supports on-time %, breach counts/cost, and expected-vs-actual gaps. |

`Tags` and `Due_dates` are loose-linked Case-child tables: populate `Tags.sql` / `Due_dates.sql` with real rows keyed on `Case_ID`; do not repurpose them for unrelated analytics (see Anti-patterns).

**Decision:**
- Many per-case labels/categories → **Tags**.
- Per-case deadline/SLA/milestone with target vs actual → **Due_dates**.
- A per-case fact that fits one column → add a column to `Cases` (via `Event_log`).
- Anything not one-row-per-case (for example, a weekly aggregate or cross-case study) → custom loose-linked Case-child table via `add-table`.

## Why a bare dbt model is not queryable

`transformations create models/Workload_weekly.sql` creates a physical Snowflake table, but it is not queryable unless:
1. Register it in the data model with `add-table`; dbt alone does not make it queryable.
2. Link it to `Cases`; otherwise it is disconnected and returns `UserError_TableIsDeleted`.

`existingTables` (query layer live tables) comes from the last successful ingestion's materialization. A data-model edit takes effect only after **re-ingest**.

## The data-model table entry (DataModelDto)

```json
{
  "type": "Object",
  "name": "Workload_weekly",
  "primaryKey": "Workload_ID",
  "foreignKeys": [{ "table": "Cases", "column": "Case_ID" }]
}
```

| Key | Meaning |
|-----|---------|
| `type` | `"Object"` (default if omitted). |
| `name` | MUST equal the dbt model / physical table name. |
| `primaryKey` | Uniquely identifies a row; add a surrogate (`{{ pm_utils.id() }}`) if needed. |
| `foreignKeys` | `[{ table, column }]` links to a parent. For a standalone analytical table, loosely link to `Cases` with nullable `Case_ID`. |

`applyCurrentDatamodel` derives per-column display/kind; do **not** hand-author a `Fields[]` array.

## Loose-link recipe: expose a custom analytical table

A table that is not one-row-per-case must reach `Cases`: give it a **surrogate PK** and nullable `Case_ID` FK. Null satisfies the case-centric graph, and aggregate queries need not resolve it to real cases.

**Caveat:** null `Case_ID` makes the table analytically disconnected: case-level filters/selections (the normal PM dashboard scope) will not propagate, and rows cannot join to real cases. Use this only for genuinely case-independent aggregates (for example, a weekly total or cross-case study). If rows correspond to real cases, populate `Case_ID` with the real key so case filtering flows through.

1. Author the dbt model with these as its first two selected columns:

   ```sql
   select
       {{ pm_utils.id() }}   as "Workload_ID",   -- surrogate PK
       cast(null as varchar) as "Case_ID",       -- loose FK to Cases
       ...                                        -- your real columns
   ```

2. Run the build, registration, re-ingest, and query commands:

   ```bash
   uip pm transformations create <app> models/Workload_weekly.sql --file ./Workload_weekly.sql
   uip pm transformations apply <app> --wait
   uip pm apps data-model add-table <app> --file ./Workload_weekly.table.json  # edits /dev/dataModel + applyCurrentDatamodel
   uip pm ingestions create <app> --wait                                       # REQUIRED — materializes the table
   uip pm query run <app> --group-by Service_Component --metric Closed_Interactions:sum --output table
   ```

   `Workload_weekly.table.json` is the DataModelDto entry above.

`add-table` GETs `/dev/dataModel` with its ETag, upserts by name (replace or append), PUTs with `If-Match`, then POSTs `applyCurrentDatamodel`. It merges into the document it just read, so the ETag is a compare-and-swap: `add-table` takes no `--etag`, unlike `data-mapping update`, `model update`, and `transformations update`, which replace locally edited files and require it. On concurrent edit (`412`), re-run `add-table` to re-read and apply over the other write. If the returned data model has no ETag, the command fails rather than writing unguarded. It returns `IngestionNeeded: true`; the entity is not queryable until re-ingest completes.

## Publish vs re-ingest

- **Re-ingest** (`ingestions create`) materializes the table for dev `query`; it is required after `add-table`.
- **Publish** (`apps publish`) pushes dev changes to dashboards / the published stage; it is separate and unnecessary just to query in dev.