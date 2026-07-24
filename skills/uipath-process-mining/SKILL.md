---
name: uipath-process-mining
description: "UiPath Process Mining via `uip pm` — build and operate a process app end-to-end from a CSV / event log: discover app templates, create an app with a data mapping, upload files, ingest, author the dbt (Snowflake) transformation layer, and query the result (aggregate group-by/metrics, details, percentiles, RCA, insights). Covers the `uipath.custom` event-log template, the `Cases.sql` optional-column gotcha, exposing custom analytical tables as Case-linked data-model tables (the add-table pattern + re-ingest; case-centric model; Tags/Due_dates for per-case labels/SLAs), the `query run --group-by/--metric` sugar, `--wait` on async ingest/transform, and the apply-not-reingest fix loop. For Orchestrator / Data Fabric / Integration Service→uipath-platform. For `.flow`/Maestro→uipath-maestro-flow. For IXP document models→uipath-ixp."
when_to_use: "User mentions process mining, a process app, an event log, `uip pm`, mining a CSV/log, data ingestion into a process app, dbt/SQL transformations of a process app, steps-to-resolution / throughput / variant / rework analysis, or wants to query a process app (aggregate, details, percentile, root-cause, insights). Also 'build a process app from this data', 'ingest this log', 'fix my Cases.sql', 'why can't I query my custom table', 'add a table to the data model', 'group by X average Y in process mining'. For Orchestrator/queues/Data Fabric→uipath-platform; for a `.flow`→uipath-maestro-flow; for IXP/Document Understanding→uipath-ixp."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Process Mining — `uip pm` Assistant

Build and operate a UiPath Process Mining process app end-to-end from the terminal with `uip pm`: from a raw CSV to a queryable process model. The whole loop — templates, data mapping, upload, ingest, the dbt/Snowflake transformation layer, and querying — is scriptable; **use the CLI, don't hand-roll the Process Mining REST API.**

**This works for every app type**, not just `uipath.custom`: the pipeline (mapping → upload → ingest → transform → data model → query) is identical across the `uipath.custom` event-log template and the source-system templates (P2P / O2C / IM / AP / … on SAP, Oracle, NetSuite, ServiceNow, Salesforce, …). Only **what the data mapping / extract must contain** differs. See [`references/app-types.md`](references/app-types.md).

The command groups: `uip pm app-types` (templates), `apps` (create/list/delete), `files` (upload), `ingestions` (create/logs), `transformations` (list/get/create/update/apply/run/status/logs — the dbt dev loop), and `query` (run/details/percentile/rca/insights/info/layout).

## When to Use This Skill

- **Build a process app from data** — you have a CSV / event log and want a mined process (throughput, variants, rework, steps-to-resolution).
- **Author the transformation layer** — edit the dbt (Snowflake) SQL models that produce the process model, then re-run.
- **Query a process app** — pull numbers out: aggregate group-by + metrics, raw detail rows, percentiles, root-cause analysis, process insights.
- **Expose custom analysis** — surface your own analytical table (a weekly aggregate, an impact study) as a queryable entity.
- **Manage the app lifecycle** — stages (dev → published), RBAC, deletion.

## App lifecycle & the ELT editor

An app moves through: **create** (from a template + data mapping) → **load** (`files upload` + `ingestions create`) → **transform** on the **dev** stage (the ELT editor — the dbt model tree) → **publish** to the **published** stage → **query** / build dashboards. `--stage dev|published` selects the stage on every data/transform/query command (default `dev`).

The **ELT editor** is the `transformations` command group operating on the dbt (Snowflake) model tree — the extract-load-transform layer that turns loaded source tables into the process model:

| Operation | Command |
|-----------|---------|
| List the model tree | `transformations list <app>` |
| Read a file (or save locally) | `transformations get <app> <path> [--destination <file>]` |
| Edit an existing file (ETag-safe) | `transformations update <app> <path> --file <local>` |
| Create a new model file | `transformations create <app> <path> --file <local>` |
| Re-run the **full** transform on loaded data | `transformations apply <app> --wait` |
| Rebuild **one** dev model + dependents | `transformations run <app> --model models/X.sql` |
| Status / logs of the last build | `transformations status <app>` · `transformations logs <app>` |

## Critical Rules

1. **To make a custom analytical table queryable, register it as a Case-linked data-model table, then RE-INGEST.** Process Mining is **case-centric**: a queryable table must be the `Cases` root or reach `Cases` via a foreign key — an unlinked table is rejected at query time (`UserError_TableIsDeleted`). First check the built-in Case-child slots: **`Tags`** (multi-valued per-case labels: `Tag`/`Tag_type`) and **`Due_dates`** (per-case SLA/deadline: `Expected`/`Actual`/`On_time`/`Cost`) — populate their dbt models rather than adding a table when your data fits. Otherwise register a custom table with **`uip pm apps model add-table <app> --file <table.json>`**, where the file is a DataModelDto entry `{ name, primaryKey, foreignKeys:[{table:"Cases",column:"Case_ID"}] }` (loose-link a standalone aggregate with a surrogate PK + nullable `Case_ID`). `add-table` edits `/dev/dataModel` (upsert, ETag-safe) then `applyCurrentDatamodel`; the table only becomes queryable after **`ingestions create --wait`** (a data-model edit takes effect only on the next ingestion). Full recipe + Tags/Due_dates decision table in [`references/data-model.md`](references/data-model.md).

2. **Match the template to the data — the rest of the pipeline is identical for all app types.** A single denormalized log (Case, Activity, Timestamp [+ attributes]) ⇒ `uipath.custom` ("Event log"). Otherwise pick the `<process>.<system>` template matching your source system AND process (Purchase-to-Pay on SAP ⇒ `uipath.p2p.sap`; incidents from ServiceNow ⇒ `uipath.im.servicenow`) — but only when you actually have that system's **full multi-table extract**, not a single log you exported from it. Every template shares the same model shape and the same mapping→ingest→transform→query machinery; only the expected input tables differ. Discover with `app-types list`, inspect a template with `app-types get`. See [`references/app-types.md`](references/app-types.md).

3. **Patch the `uipath.custom` `Cases.sql` optional-column gotcha (custom-only).** Source-system templates ship their own correct transformations — this gotcha is specific to the `uipath.custom` event-log template. The template's `models/Cases.sql` references `Event_log."Case"`, `"Case_status"`, `"Case_type"`, `"Case_value"`. A minimal mapping (Case_ID/Activity/timestamp only) doesn't produce those ⇒ dbt `000904 invalid identifier`. Fix: pull the file, replace the missing refs with `cast(null as varchar/float)`, push, and **`transformations apply`**. `Tags.sql`/`Due_dates.sql` are safe `where 1=0` stubs.

4. **After a transform-only failure, `apply` — don't re-ingest.** The data is already loaded. Fix SQL (`transformations get` → edit → `transformations update`/`create`) then `transformations apply` (re-transforms loaded data). Re-ingest only when the raw data or the mapping/parse settings change.

5. **Use `--wait` on async commands.** `ingestions create --wait` and `transformations apply --wait` block to a terminal state, print the dbt/loader error on failure, and exit non-zero — no hand-rolled `apps list` poll loop.

6. **Query field ids come from `query info`, not column names.** `query run`/`percentile` bodies take the hashed `F__<Table>__<Col>__<hash>` ids. Prefer the sugar: `query run <app> --group-by <col> --metric <col>:<fn>` resolves human names for you (fn ∈ `average|count|sum|min|max`).

7. **Develop on `dev` with a data subset; publish the full dataset.** The `dev` stage is for iterating on the mapping and transformations — keep it fast by loading a **small representative subset** of the data. Once the model is right, **publish** so the **published** stage carries the **full** dataset for real analysis and sharing. Query/transform against `--stage dev` while developing; point consumers at `--stage published`.

8. **RBAC is folder/role-based at the platform layer, not the process app itself.** A process app lives in a folder; who can view vs. edit vs. publish is governed by Orchestrator/Identity roles and folder assignments — configure it with [`uipath-admin`](/uipath:uipath-admin) (roles, role assignments, effective-access) and [`uipath-platform`](/uipath:uipath-platform) (folders). See [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md). `uip pm` itself does not grant access.

## Quick Start — CSV → queryable process app

```bash
# 0. Pre-flight (cheap local checks — see references/pre-flight.md): encoding (UTF-8?),
#    delimiter, date format (dd-mm vs mm-dd), and strip junk all-empty rows.

# 1. Discover the template + its target fields
uip pm app-types list --output-filter "[].{Key:AppTypeKey,Version:Version,Name:DefaultName}"

# 2. Create the app from a data mapping (isNotNull/isUnique now default per field)
uip pm apps create "My Process" --type uipath.custom --data-mapping ./mapping.json

# 3. Upload + ingest (block until done; prints the loader error on failure)
uip pm files upload <appId> ./data.csv --input-table Event_log
uip pm ingestions create <appId> --file-format csv --field-delimiter ";" --encoding utf-8 --wait

# 4. If the transform failed on Cases.sql (Rule 3): pull → patch → apply
uip pm transformations get <appId> models/Cases.sql --destination Cases.sql
#   ...edit...
uip pm transformations update <appId> models/Cases.sql --file Cases.sql
uip pm transformations apply <appId> --wait

# 5. Query it
uip pm query info <appId>                                   # discover fields/metrics
uip pm query run  <appId> --group-by Service_Component --metric Event_count:average --output table
```

## Extending the model with custom analysis

The killer use case is your own SQL. Add analytical dbt models with `transformations create <path> --file` (use `update` for existing files; inline intermediates as CTEs if you prefer fewer files), then **register each queryable output as a Case-linked data-model table + re-ingest (Rule 1)** so `query` can read it. Full recipe + the DataModelDto entry shape (`type`/`name`/`primaryKey`/`foreignKeys`) and the Tags/Due_dates decision table in [`references/data-model.md`](references/data-model.md); the transformation dev loop and dbt/pm_utils notes in [`references/transformations.md`](references/transformations.md); the query AST and sugar in [`references/querying.md`](references/querying.md).

## Reference Navigation

| File | Read when |
|------|-----------|
| [`references/app-types.md`](references/app-types.md) | choosing/targeting a template — custom vs source-system, why the pipeline is the same for all, what the mapping/extract must contain per family |
| [`references/pre-flight.md`](references/pre-flight.md) | before any upload — encoding/delimiter/date-format/empty-row checks and the minimal `mapping.json` recipe |
| [`references/transformations.md`](references/transformations.md) | authoring/fixing dbt models — the `Cases.sql` patch, apply-vs-run, pm_utils macros, Snowflake identifier quoting |
| [`references/data-model.md`](references/data-model.md) | exposing a custom table to `query`/dashboards — the case-centric add-table pattern (DataModelDto + re-ingest) and the Tags/Due_dates decision table |
| [`references/querying.md`](references/querying.md) | pulling numbers out — the aggregate body AST, the `--group-by/--metric` sugar, the `AggregationFunction` enum, and the event-table restriction |
| [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md) | dev vs published stages, publishing, and where process-app RBAC is configured |

## Anti-patterns — what NOT to do

- **Repurposing `Tags.sql`/`Due_dates.sql`** to smuggle an *unrelated* analytics table through a pre-registered entity. Fine — intended, even — to populate them with their real semantics (per-case labels; per-case SLAs); wrong to jam a weekly aggregate into `Due_dates` to dodge add-table. It corrupts those features and fights their primary key. Register a real Case-linked table instead (Rule 1).
- **Adding a data-model table with no link to `Cases`** — it registers but every query fails `UserError_TableIsDeleted`. Give a standalone table a surrogate PK + nullable `Case_ID` FK to `Cases` (Rule 1).
- **Forgetting to re-ingest after `add-table`.** The data-model edit is inert until the next `ingestions create` re-materializes the tables (Rule 1).
- **Re-uploading + re-ingesting after a transform-only failure.** The data is loaded; fix the SQL and `transformations apply`. Re-ingest only when raw data or parse settings change (Rule 4).
- **Hand-rolling an `apps list` poll loop.** Use `--wait` on `ingestions create` / `transformations apply` (Rule 5).
- **Passing column names in a raw `query run` body**, or hand-writing the aggregate AST. Bodies take hashed field ids from `query info`; use the `--group-by/--metric` sugar (Rule 6).
- **Patching `Cases.sql` on a source-system template.** That gotcha is `uipath.custom`-only; source templates ship correct transformations — feed the expected extract and extend, don't rewrite (Rule 3).
- **Using a source template for a single flat log** (or `uipath.custom` for a full multi-table extract). Match the template to the data shape (Rule 2).
- **Iterating on the full dataset.** Develop on `dev` with a small subset; publish the full data (Rule 7).
