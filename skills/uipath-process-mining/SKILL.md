---
name: uipath-process-mining
description: "UiPath Process Mining via `uip pm` — build and operate a process app end-to-end from a CSV / event log: templates, data mapping, upload, ingest, dbt (Snowflake) transformations, publish, query (metrics, percentiles, RCA). Covers `uipath.custom`, the `Cases.sql` optional-column gotcha, Case-linked data-model tables (add-table + re-ingest), the apply-not-reingest fix loop, in-place mapping fix via `apps data-mapping get|update` (no app rebuild), and `apps model fields` — field data kind, calculated fields, the numeric→duration mismatch that locks dashboards open. For Orchestrator/Data Fabric/Integration Service→uipath-platform. For `.flow`/Maestro→uipath-maestro-flow. For IXP→uipath-ixp."
when_to_use: "User mentions process mining, a process app, an event log, `uip pm`, mining a CSV/log, ingesting data into one, dbt/SQL transformations, steps-to-resolution / throughput / variant / rework analysis, or querying one. Also 'build a process app from this data', 'ingest this log', 'fix my Cases.sql', 'why can't I query my custom table', 'add a table to the data model', 'group by X average Y', 'fix/change/read my data mapping', 'wrong date format in the mapping', 'change a field's data kind', 'set a field to duration', 'add a calculated field/metric', 'my dashboards won't open', 'Must be duration not numeric'. For Orchestrator/Data Fabric→uipath-platform; `.flow`→uipath-maestro-flow; IXP→uipath-ixp."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Process Mining — `uip pm` Assistant

Build and operate UiPath Process Mining apps with `uip pm`, from CSV to queryable process model: templates, mapping, upload, ingestion, dbt/Snowflake transformations, and queries. **Use the CLI, not the Process Mining REST API.**
Build and operate a UiPath Process Mining process app end-to-end from the terminal with `uip pm`: from a raw CSV to a queryable process model. The whole loop — templates, data mapping, upload, ingest, the dbt/Snowflake transformation layer, and querying — is scriptable; **use the CLI, don't hand-roll the Process Mining REST API.**

The pipeline is the same for `uipath.custom` and source-system templates (P2P / O2C / IM / AP / …; SAP, Oracle, NetSuite, ServiceNow, Salesforce, …); only mapping/extract differs. See [`references/app-types.md`](references/app-types.md). CLI mechanics—command groups, `Result`/`Code`/`Data`, ETag get-modify-put, `--wait`, `--stage`, and field-id discovery—are in [`references/uip-pm-cli.md`](references/uip-pm-cli.md).

## When to Use This Skill

- Build process apps from CSV/event logs (throughput, variants, rework, steps-to-resolution).
- Author or rerun dbt (Snowflake) transformations; query aggregates, raw rows, percentiles, root causes, or process insights.
- Expose custom analytical tables as queryable entities; edit fields, calculated fields, or data-kind mismatches.
- Manage stages, RBAC, or deletion.

## App lifecycle

Create from template + mapping → upload + ingest → transform on `dev` → publish to `published` → query/build dashboards. Develop with a small `dev` subset, then publish the full dataset ([`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md)). `transformations` edits the ELT/dbt (Snowflake) model tree; see [`references/transformations.md`](references/transformations.md) for commands and apply-vs-run.

## Critical Rules

1. **Custom analytical tables must be Case-linked and re-ingested to become queryable.** A queryable table must be the `Cases` root or reach `Cases` via a foreign key; otherwise queries reject it with `UserError_TableIsDeleted`. Prefer built-in Case-child slots: **`Tags`** for per-case labels (`Tag`/`Tag_type`) and **`Due_dates`** for per-case SLA/deadline (`Expected_date`/`Actual_date`/`On_time`/`Cost`). Otherwise run `uip pm apps data-model add-table <app> --file <table.json>` with a DataModelDto entry `{ name, primaryKey, foreignKeys:[{table:"Cases",column:"Case_ID"}] }`; standalone aggregates need a surrogate PK and nullable `Case_ID`. `add-table` upserts `/dev/dataModel` ETag-safely and calls `applyCurrentDatamodel`; the table becomes queryable only after `ingestions create --wait`, since edits take effect on the next ingestion. See [`references/data-model.md`](references/data-model.md) for the recipe and Tags/Due_dates decision table.

2. **Match the template to the data; the rest of the pipeline is identical.** Use `uipath.custom` (“Event log”) for a single denormalized Case/Activity/Timestamp log (+ attributes). Otherwise use the `<process>.<system>` template matching process and source system, and only with that system’s full multi-table extract—not a single exported log. Discover templates with `app-types list` and inspect with `app-types get`. See [`references/app-types.md`](references/app-types.md).

3. **Patch the optional-column `Cases.sql` gotcha only for `uipath.custom`.** Source-system templates ship correct transformations. In `uipath.custom` `models/Cases.sql`, missing `Event_log."Case"`, `"Case_status"`, `"Case_type"`, or `"Case_value"` refs in a minimal Case_ID/Activity/timestamp mapping cause dbt `000904 invalid identifier`. Pull the file, replace missing refs with `cast(null as varchar/float)`, push, then run **`transformations apply`**. `Tags.sql`/`Due_dates.sql` are safe `where 1=0` stubs.

4. **After a transform-only failure, apply; do not re-ingest.** Data is already loaded. Fix SQL with `transformations get` → edit → `transformations update --etag '<the get's ETag>'`, or `create` for a new file (no ETag), then run `transformations apply`. Re-ingest only when raw data or mapping/parse settings change.

5. **Fix a wrong mapping in place; do not recreate the app.** Run `uip pm apps data-mapping get <app> --destination ./mapping.json`, edit, then `uip pm apps data-mapping update <app> --file ./mapping.json --etag '<etag>'`. `--etag` is required; use `Data.ETag` from `get`. On `409 UserError_ETagFileConflict` or a `409`/`412`, re-get the latest document and ETag, re-apply the change, and retry; never pair a stale local file with a fresh ETag. A table-less file is refused rather than wiping stored mapping. Mapping changes affect parsing on the next ingestion: if source columns changed, rerun `files upload`, then `ingestions create`. Only `dev` is writable; `published` is read-only. See [`references/pre-flight.md`](references/pre-flight.md) and [`references/uip-pm-cli.md`](references/uip-pm-cli.md).

6. **Use `--wait` on async commands.** Run `ingestions create --wait` and `transformations apply --wait` to block to a terminal state; failures print the dbt/loader error and exit non-zero. Do not hand-roll an `apps list` poll loop.

7. **Get query field ids from `query info`, not column names.** `query run`/`percentile` bodies require hashed `F__<Table>__<Col>__<hash>` ids. Prefer `query run <app> --group-by <col> --metric <col>:<fn>` to resolve human names; `fn` ∈ `average|count|sum|min|max`. Do not hand-write the aggregate AST.

8. **Develop on `dev` with a subset; publish the full dataset.** Iterate with a small representative subset and `--stage dev`; publish when the model is right so `published` carries the full dataset for dashboards and sharing. Consumers use published dashboards. `query --stage published` works after completed ingestion there; if `apps publish` reports `IngestionNeeded: true`, run `ingestions create <app> --stage published --wait`. Published querying is optional ([`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md)).

9. **RBAC is platform folder/role-based, not app-level.** Configure Orchestrator/Identity roles and folder assignments with [`uipath-admin`](/uipath:uipath-admin) (roles, role assignments, effective-access) and [`uipath-platform`](/uipath:uipath-platform) (folders). `uip pm` does not grant access. See [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md).

10. **Edit data kinds/calculated fields with `apps model fields`; mismatches can lock the app open.** Run `uip pm apps model fields set <app> <field> [--kind|--display-name|--expression]` to change kind, rename a field, or add a calculated field. This is a dev-only semantic-model edit with no `--etag`; it merges into the version just read, so fix a lost race by rerunning. Whole-document `apps model update` requires `--etag`. Relational/arithmetic operators require operands of the same data kind. If a field changes to `duration` while a metric/calculated field/dashboard filter compares it to a `numeric` constant, the invalid model can throw on dashboard open (“Must be duration, not numeric, for the 'lt' input”), leaving only the data-upload module reachable. `fields set`/`update` validate and refuse such edits with a hint; fix an already-broken app by making the comparison consistent (re-type the field or constant). See [`references/model-editing.md`](references/model-editing.md).

## Quick Start

The end-to-end CSV → queryable-app command sequence (discover template → create → upload → ingest → patch transform / fix mapping → query) is in [`references/uip-pm-cli.md`](references/uip-pm-cli.md#quick-start--csv--queryable-process-app).

## Extending the model with custom analysis

Create analytical dbt models with `transformations create <path> --file` (use `update` for existing files; intermediates may be inline CTEs). Register every queryable output as a Case-linked data-model table, then re-ingest (Rule 1). See [`references/data-model.md`](references/data-model.md) for the recipe, DataModelDto (`type`/`name`/`primaryKey`/`foreignKeys`), and Tags/Due_dates decision table; [`references/transformations.md`](references/transformations.md) for the dbt dev loop and dbt/pm_utils notes; and [`references/querying.md`](references/querying.md) for query AST and sugar.

## Reference Navigation

Use domain references for decisions and the CLI reference for mechanics:

- [`references/uip-pm-cli.md`](references/uip-pm-cli.md): CLI groups; `Result`/`Code`/`Data`, exit codes, ETag get-modify-put, `--wait`, `--stage`, `IngestionNeeded`, field-id discovery, CSV Quick Start.
- [`references/app-types.md`](references/app-types.md): template choice/targeting; custom vs source-system pipeline and required mapping/extract.
- [`references/pre-flight.md`](references/pre-flight.md): before any upload — encoding, delimiter, date-format, empty-row checks, minimal `mapping.json`, mapping fixes/failures.
- [`references/transformations.md`](references/transformations.md): dbt authoring/fixes, `Cases.sql` patch, apply-vs-run, pm_utils, Snowflake identifier quoting.
- [`references/data-model.md`](references/data-model.md): Case-linked custom tables, DataModelDto, re-ingest, Tags/Due_dates decision table.
- [`references/model-editing.md`](references/model-editing.md): semantic `apps model` vs structural `apps data-model`; data kinds, calculated fields, comparison lockout.
- [`references/querying.md`](references/querying.md): aggregate body AST, `--group-by`/`--metric` sugar, `AggregationFunction` enum, event-table restriction.
- [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md): `dev`/`published`, publishing, process-app RBAC.

## Anti-patterns — what NOT to do

- Do not repurpose `Tags.sql`/`Due_dates.sql` to smuggle an *unrelated* analytics table (e.g. a weekly aggregate in `Due_dates` to dodge add-table) — it corrupts those features and fights their primary key. Populating them with their real semantics (per-case labels; per-case SLAs) is intended. Do not add an unlinked table, or omit re-ingestion after `add-table` (Rule 1).
- After transform-only failures, do not re-upload/re-ingest; after mapping changes, do not use `transformations apply` (Rules 4–5).
- Do not delete/recreate an app for a mapping mistake or pair a stale file with a fresh ETag; on `409`/`412`, re-get, re-apply, and write with that ETag (Rule 5). Recreating also throws away the transformations you already patched.
- Do not hand-roll an `apps list` poll loop or put column names in raw `query run` bodies (Rules 6–7).
- Do not patch `Cases.sql` on source-system templates, use a source template for a single flat log, or use `uipath.custom` for a full multi-table extract (Rules 2–3).
- Do not iterate on the full dataset; use a small `dev` subset and publish the full data. Do not change a field’s data kind while a comparison still uses the old kind; reconcile the field or constant first (Rules 8, 10).