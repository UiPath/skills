# Data model — making tables queryable (the add-table pattern)

Process Mining is **case-centric**. A table is queryable only if it is the **Cases**
root or reaches `Cases` through a foreign key. A standalone dbt model with no link
to `Cases` is treated as disconnected and rejected at query time
(`UserError_TableIsDeleted`).

## Two models — do not confuse them

| Model | Endpoint | Shape | Role |
|-------|----------|-------|------|
| **Data model** (structural) | `/apps/{id}/{stage}/dataModel` | `tables[]` of `{ type, name, primaryKey, foreignKeys }` | What tables exist + how they link. **`add-table` edits this.** `apps model get` reads it. |
| **Semantic model** | `/apps/{id}/{stage}/model` | `Processes` / `Metrics` / `Tables[].Fields[]` | Field-level view `query info` reads. **Derived** from the data model by `applyCurrentDatamodel` — do not hand-edit for add-table. |

Edit the structural data model; `applyCurrentDatamodel` regenerates the semantic
model (its per-column fields) from it. `add-table` does both.

## The built-in Case-child tables — use these before adding your own

The `uipath.custom` template ships four data-model tables. Two are the process
backbone; two are ready-made Case-child extension slots. **Check whether your data
fits Tags or Due_dates before hand-rolling a custom table** — they exist to save you
the add-table round-trip.

| Table | PK / link | Fields | Use it for |
|-------|-----------|--------|------------|
| **Cases** | `Case_ID` (root) | case attributes | One row per process instance (the case). The root everything links to. |
| **Event_log** | FK→Cases | activity, timestamp, resource… | The event log — one row per activity. The process itself. Not directly group-by-able (it drives the process graph). |
| **Tags** | `Tag_ID`, FK→Cases | `Tag` (label), `Tag_type` (category) | **Multi-valued categorical labels per case.** A case can carry many tags. Use for flags/segments/attributes that don't fit one Case column — e.g. `Tag_type="Region", Tag="EU"`; `Tag_type="Flag", Tag="Escalated"`. Filter/group cases by tag. |
| **Due_dates** | `Due_date_ID`, FK→Cases | `Due_date`/`Due_date_type` (which deadline), `Expected_date`, `Actual_date`, `On_time` (bool), `Cost` (currency), `Difference` (duration) | **Per-case SLA / deadline / milestone tracking.** A case can have many due dates (multiple SLAs/milestones). Use for on-time %, SLA-breach counts, cost-of-breach, expected-vs-actual gaps. |

Both `Tags` and `Due_dates` are themselves Case-child tables (FK→`Cases`) — they are
the template's built-in example of the loose-link pattern below. Populate them by
authoring their dbt models (`Tags.sql` / `Due_dates.sql`) to emit real rows keyed on
`Case_ID`. This is the **intended** use — distinct from the anti-pattern of
repurposing them to smuggle unrelated analytics through (see Anti-patterns).

**Decision:**
- Per-case label / category, possibly many per case → **Tags**.
- Per-case deadline / SLA / milestone with target vs actual → **Due_dates**.
- Per-case fact that fits one column → add a column to `Cases` (via `Event_log`).
- Anything not one-row-per-case (a weekly aggregate, a cross-case study) → a **custom
  Case-child table** via `add-table` (loose-linked; below).

## Why a bare dbt model is not queryable

`transformations create models/Workload_weekly.sql` builds a physical Snowflake
table, but `query info` will not list it and `query run` cannot group by it. Two
gates:

1. **Not in the data model.** dbt produces tables; the data model decides which
   become queryable entities. Register it (`add-table`).
2. **Not linked to Cases.** Even once registered, a table with no path to `Cases` is
   disconnected → `UserError_TableIsDeleted`. Give it a foreign key to `Cases`.

And one timing gate: `existingTables` (what the query layer treats as "live") is
derived from the **last successful ingestion's** materialization — so a data-model
edit only takes effect after a **re-ingest**.

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
| `primaryKey` | A column that uniquely identifies a row — add a surrogate (`{{ pm_utils.id() }}`) if the table has none. |
| `foreignKeys` | `[{ table, column }]` links to a parent. For a standalone analytical table, link **loosely** to `Cases` on a nullable `Case_ID` column. |

Per-column display/kind is derived by `applyCurrentDatamodel` — you do **not**
hand-author a `Fields[]` array.

## Loose-link recipe: expose a custom analytical table

The table isn't one-row-per-case, but must still reach `Cases`. Give it a **surrogate
PK** and a **nullable `Case_ID`** carrying the FK — a null FK is enough to satisfy the
case-centric graph; aggregate queries don't need it to resolve to real cases.

1. Author the dbt model. First two selected columns:

   ```sql
   select
       {{ pm_utils.id() }}   as "Workload_ID",   -- surrogate PK
       cast(null as varchar) as "Case_ID",       -- loose FK to Cases
       ...                                        -- your real columns
   ```

2. Build, register, **re-ingest**, query:

   ```bash
   uip pm transformations create <app> models/Workload_weekly.sql --file ./Workload_weekly.sql
   uip pm transformations apply <app> --wait
   uip pm apps model add-table <app> --file ./Workload_weekly.table.json      # edits /dev/dataModel + applyCurrentDatamodel
   uip pm ingestions create <app> --wait                                       # REQUIRED — materializes the table
   uip pm query run <app> --group-by Service_Component --metric Closed_Interactions:sum --output table
   ```

   Where `Workload_weekly.table.json` is the DataModelDto entry above.

`add-table` GETs `/dev/dataModel` (with its ETag), **upserts** the table by name
(replace if present, else append), PUTs it back `If-Match`-guarded, then POSTs
`applyCurrentDatamodel`. A concurrent edit surfaces as `412`. It returns
`IngestionNeeded: true` — the entity is not queryable until the re-ingest completes.

## Publish vs re-ingest

- **Re-ingest** (`ingestions create`) materializes the table so **dev** `query` sees
  it. Required for add-table.
- **Publish** (`apps publish`) pushes dev changes to the **dashboards / published**
  stage. Separate step; not needed just to query in dev.
