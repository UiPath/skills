---
name: uipath-process-mining
description: "UiPath Process Mining via `uip pm` — build and operate a process app end-to-end from a CSV / event log: templates, data mapping, upload, ingest, the dbt (Snowflake) transformation layer, publish, and query it (metrics, percentiles, RCA). Covers `uipath.custom`, the `Cases.sql` optional-column gotcha, Case-linked data-model tables (add-table + re-ingest), the apply-not-reingest fix loop, fixing a wrong mapping in place via `apps data-mapping get|update` (no app rebuild), and editing the app model via `apps model fields` — a field's data kind / calculated fields, including the numeric→duration mismatch that locks dashboards open (DNA-46960). For Orchestrator/Data Fabric/Integration Service→uipath-platform. For `.flow`/Maestro→uipath-maestro-flow. For IXP→uipath-ixp."
when_to_use: "User mentions process mining, a process app, an event log, `uip pm`, mining a CSV/log, ingesting data into one, dbt/SQL transformations, steps-to-resolution / throughput / variant / rework analysis, or querying one. Also 'build a process app from this data', 'ingest this log', 'fix my Cases.sql', 'why can't I query my custom table', 'add a table to the data model', 'group by X average Y', 'fix/change/read my data mapping', 'wrong date format in the mapping', 'change a field's data kind', 'set a field to duration', 'add a calculated field/metric', 'my dashboards won't open', 'Must be duration not numeric (DNA-46960)'. For Orchestrator/Data Fabric→uipath-platform; `.flow`→uipath-maestro-flow; IXP→uipath-ixp."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Process Mining — `uip pm` Assistant

Build and operate a UiPath Process Mining process app end-to-end from the terminal with `uip pm`: from a raw CSV to a queryable process model. The whole loop — templates, data mapping, upload, ingest, the dbt/Snowflake transformation layer, and querying — is scriptable; **use the CLI, don't hand-roll the Process Mining REST API.**

**This works for every app type**, not just `uipath.custom`: the pipeline (mapping → upload → ingest → transform → data model → query) is identical across the `uipath.custom` event-log template and the source-system templates (P2P / O2C / IM / AP / … on SAP, Oracle, NetSuite, ServiceNow, Salesforce, …). Only **what the data mapping / extract must contain** differs. See [`references/app-types.md`](references/app-types.md).

This skill is the **process-mining domain layer** — *what* to build and *why*. The
low-level mechanics of driving the tool — the command-group map, the `Result`/`Code`/`Data`
output envelope, the ETag get-modify-put pattern, `--wait`, `--stage`, and field-id
discovery — are one layer down in [`references/uip-pm-cli.md`](references/uip-pm-cli.md).
The rules below carry the headline command and link down to it and to the domain
references for the full detail.

## When to Use This Skill

- **Build a process app from data** — you have a CSV / event log and want a mined process (throughput, variants, rework, steps-to-resolution).
- **Author the transformation layer** — edit the dbt (Snowflake) SQL models that produce the process model, then re-run.
- **Query a process app** — pull numbers out: aggregate group-by + metrics, raw detail rows, percentiles, root-cause analysis, process insights.
- **Expose custom analysis** — surface your own analytical table (a weekly aggregate, an impact study) as a queryable entity.
- **Edit the app model** — change a field's data kind, add calculated fields, or fix a data-kind mismatch that locks dashboards open (DNA-46960).
- **Manage the app lifecycle** — stages (dev → published), RBAC, deletion.

## App lifecycle

An app moves through: **create** (from a template + data mapping) → **load** (upload + ingest) → **transform** on the **dev** stage (the ELT/dbt layer) → **publish** to the **published** stage → **query** / build dashboards. Develop against a small subset on `dev`, then publish the full dataset for real analysis ([`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md)). The **ELT editor** is the `transformations` command group over the dbt (Snowflake) model tree that turns loaded source tables into the process model — its command surface and the apply-vs-run distinction are in [`references/transformations.md`](references/transformations.md).

## Critical Rules

1. **To make a custom analytical table queryable, register it as a Case-linked data-model table, then RE-INGEST.** Process Mining is **case-centric**: a queryable table must be the `Cases` root or reach `Cases` via a foreign key — an unlinked table is rejected at query time (`UserError_TableIsDeleted`). First check the built-in Case-child slots: **`Tags`** (multi-valued per-case labels: `Tag`/`Tag_type`) and **`Due_dates`** (per-case SLA/deadline: `Expected_date`/`Actual_date`/`On_time`/`Cost`) — populate their dbt models rather than adding a table when your data fits. Otherwise register a custom table with **`uip pm apps data-model add-table <app> --file <table.json>`**, where the file is a DataModelDto entry `{ name, primaryKey, foreignKeys:[{table:"Cases",column:"Case_ID"}] }` (loose-link a standalone aggregate with a surrogate PK + nullable `Case_ID`). `add-table` edits `/dev/dataModel` (upsert, ETag-safe) then `applyCurrentDatamodel`; the table only becomes queryable after **`ingestions create --wait`** (a data-model edit takes effect only on the next ingestion). Full recipe + Tags/Due_dates decision table in [`references/data-model.md`](references/data-model.md).

2. **Match the template to the data — the rest of the pipeline is identical for all app types.** A single denormalized log (Case, Activity, Timestamp [+ attributes]) ⇒ `uipath.custom` ("Event log"). Otherwise pick the `<process>.<system>` template matching your source system AND process (Purchase-to-Pay on SAP ⇒ `uipath.p2p.sap`; incidents from ServiceNow ⇒ `uipath.im.servicenow`) — but only when you actually have that system's **full multi-table extract**, not a single log you exported from it. Every template shares the same model shape and the same mapping→ingest→transform→query machinery; only the expected input tables differ. Discover with `app-types list`, inspect a template with `app-types get`. See [`references/app-types.md`](references/app-types.md).

3. **Patch the `uipath.custom` `Cases.sql` optional-column gotcha (custom-only).** Source-system templates ship their own correct transformations — this gotcha is specific to the `uipath.custom` event-log template. The template's `models/Cases.sql` references `Event_log."Case"`, `"Case_status"`, `"Case_type"`, `"Case_value"`. A minimal mapping (Case_ID/Activity/timestamp only) doesn't produce those ⇒ dbt `000904 invalid identifier`. Fix: pull the file, replace the missing refs with `cast(null as varchar/float)`, push, and **`transformations apply`**. `Tags.sql`/`Due_dates.sql` are safe `where 1=0` stubs.

4. **After a transform-only failure, `apply` — don't re-ingest.** The data is already loaded. Fix SQL (`transformations get` → edit → `transformations update --etag '<the get's ETag>'`, or `create` for a new file, which needs none) then `transformations apply` (re-transforms loaded data). Re-ingest only when the raw data or the mapping/parse settings change.

5. **A wrong data mapping does NOT mean recreating the app — fix it in place with `apps data-mapping`.** The mapping is not create-only: `uip pm apps data-mapping get <app> --destination ./mapping.json` → edit → `uip pm apps data-mapping update <app> --file ./mapping.json --etag '<etag>'` replaces it on an existing app. **`--etag` is required** — pass the `Data.ETag` that *your* `get` returned, which is what proves the edit was based on the version you read; a lost race is refused `409 UserError_ETagFileConflict` (re-`get` for the new version **and** ETag, re-apply, retry), and a table-less file is refused rather than wiping the stored mapping. Unlike a SQL fix (Rule 4), a **mapping** change is a parse-setting change, so it takes effect only on the **next ingestion** — re-`files upload` if the source columns changed, then `ingestions create`. Only `dev` is writable (`published` is read-only). Facts + failure modes in [`references/pre-flight.md`](references/pre-flight.md).

6. **Use `--wait` on async commands.** `ingestions create --wait` and `transformations apply --wait` block to a terminal state, print the dbt/loader error on failure, and exit non-zero — no hand-rolled `apps list` poll loop.

7. **Query field ids come from `query info`, not column names.** `query run`/`percentile` bodies take the hashed `F__<Table>__<Col>__<hash>` ids. Prefer the sugar: `query run <app> --group-by <col> --metric <col>:<fn>` resolves human names for you (fn ∈ `average|count|sum|min|max`).

8. **Develop on `dev` with a data subset; publish the full dataset.** The `dev` stage is for iterating on the mapping and transformations — keep it fast by loading a **small representative subset** of the data. Once the model is right, **publish** so the **published** stage carries the **full** dataset for the dashboards and sharing. Iterate with `--stage dev`; consumers read the **published dashboards**. `query --stage published` works once that stage has a completed ingestion — after `apps publish` reports `IngestionNeeded: true`, run `ingestions create <app> --stage published --wait`. Querying published is optional, not a required step ([`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md)).

9. **RBAC is folder/role-based at the platform layer, not the process app itself.** A process app lives in a folder; who can view vs. edit vs. publish is governed by Orchestrator/Identity roles and folder assignments — configure it with [`uipath-admin`](/uipath:uipath-admin) (roles, role assignments, effective-access) and [`uipath-platform`](/uipath:uipath-platform) (folders). See [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md). `uip pm` itself does not grant access.

10. **Edit a field's data kind / calculated fields with `apps model fields` — and a data-kind mismatch can lock the app open.** Change a field's kind (e.g. numeric→duration), rename it, or add a calculated field with `uip pm apps model fields set <app> <field> [--kind|--display-name|--expression]` (the **semantic** model; dev-only, and **no `--etag`** — it merges into the version it just read, so a lost race is fixed by re-running it; a whole-document `apps model update` does require `--etag`). Relational/arithmetic operators require both operands to share a data kind, so flipping a field to `duration` while a metric / calculated field / dashboard filter still compares it to a `numeric` constant persists an invalid model that throws at dashboard open — the *"Must be duration, not numeric, for the 'lt' input"* lockout (DNA-46960), which leaves only the data-upload module reachable. `fields set`/`update` validate and refuse such an edit with a hint; fix an already-broken app by making the comparison consistent (re-type the field or the constant). Full surface + the data-kind rule in [`references/model-editing.md`](references/model-editing.md).

## Quick Start

The end-to-end CSV → queryable-app command sequence (discover template → create →
upload → ingest → patch transform / fix mapping → query) is in
[`references/uip-pm-cli.md`](references/uip-pm-cli.md#quick-start--csv--queryable-process-app).

## Extending the model with custom analysis

The killer use case is your own SQL. Add analytical dbt models with `transformations create <path> --file` (use `update` for existing files; inline intermediates as CTEs if you prefer fewer files), then **register each queryable output as a Case-linked data-model table + re-ingest (Rule 1)** so `query` can read it. Full recipe + the DataModelDto entry shape (`type`/`name`/`primaryKey`/`foreignKeys`) and the Tags/Due_dates decision table in [`references/data-model.md`](references/data-model.md); the transformation dev loop and dbt/pm_utils notes in [`references/transformations.md`](references/transformations.md); the query AST and sugar in [`references/querying.md`](references/querying.md).

## Reference Navigation

Two layers: the **`uip pm` CLI** reference (how to drive the tool) and the
**process-mining domain** references (what to build and why). Start with a domain
reference for the decision; drop into the CLI reference for the mechanics it uses.

| File | Read when |
|------|-----------|
| [`references/uip-pm-cli.md`](references/uip-pm-cli.md) | **CLI mechanics (low-level)** — the command-group map, the `Result`/`Code`/`Data` envelope + exit codes, the ETag get-modify-put pattern, `--wait`, `--stage`, `IngestionNeeded`, field-id discovery, and the CSV→queryable-app Quick Start |
| [`references/app-types.md`](references/app-types.md) | choosing/targeting a template — custom vs source-system, why the pipeline is the same for all, what the mapping/extract must contain per family |
| [`references/pre-flight.md`](references/pre-flight.md) | before any upload — encoding/delimiter/date-format/empty-row checks and the minimal `mapping.json` recipe; **also** the post-create mapping fix loop (`apps data-mapping get`/`update`) and its failure modes |
| [`references/transformations.md`](references/transformations.md) | authoring/fixing dbt models — the `Cases.sql` patch, apply-vs-run, pm_utils macros, Snowflake identifier quoting |
| [`references/data-model.md`](references/data-model.md) | exposing a custom table to `query`/dashboards — the case-centric add-table pattern (DataModelDto + re-ingest) and the Tags/Due_dates decision table |
| [`references/model-editing.md`](references/model-editing.md) | editing the app model — a field's **data kind** (e.g. numeric→duration), calculated fields, the two models (semantic `apps model` vs structural `apps data-model`), and the data-kind comparison rule that locks an app open (DNA-46960) |
| [`references/querying.md`](references/querying.md) | pulling numbers out — the aggregate body AST, the `--group-by/--metric` sugar, the `AggregationFunction` enum, and the event-table restriction |
| [`references/lifecycle-and-rbac.md`](references/lifecycle-and-rbac.md) | dev vs published stages, publishing, and where process-app RBAC is configured |

## Anti-patterns — what NOT to do

- **Repurposing `Tags.sql`/`Due_dates.sql`** to smuggle an *unrelated* analytics table through a pre-registered entity. Fine — intended, even — to populate them with their real semantics (per-case labels; per-case SLAs); wrong to jam a weekly aggregate into `Due_dates` to dodge add-table. It corrupts those features and fights their primary key. Register a real Case-linked table instead (Rule 1).
- **Adding a data-model table with no link to `Cases`** — it registers but every query fails `UserError_TableIsDeleted`. Give a standalone table a surrogate PK + nullable `Case_ID` FK to `Cases` (Rule 1).
- **Forgetting to re-ingest after `add-table`.** The data-model edit is inert until the next `ingestions create` re-materializes the tables (Rule 1).
- **Re-uploading + re-ingesting after a transform-only failure.** The data is loaded; fix the SQL and `transformations apply`. Re-ingest only when raw data or parse settings change (Rule 4).
- **Deleting and recreating an app to fix a mapping mistake** (or telling the user that's the only option). The mapping is editable after creation — `apps data-mapping get`/`update` (Rule 5). Recreating also throws away the transformations you already patched.
- **`transformations apply` after a mapping change.** `apply` only re-runs SQL over *already-parsed* data; a new mapping changes how the raw file is parsed, so it needs `ingestions create` (Rule 5). This is the mirror of Rule 4 — get the direction wrong and the edit silently appears to do nothing.
- **Re-`get`ting a resource just to harvest a fresh `--etag` for a rejected write.** That defeats the `If-Match` guard — it makes the precondition pass no matter who wrote in between, silently overwriting them. A 409/412 means the resource moved: re-`get` the latest **document**, re-apply your change on top of *that*, then write with the ETag that read returned. Never pair a stale local file with a freshly fetched ETag ([`references/uip-pm-cli.md`](references/uip-pm-cli.md)).
- **Hand-rolling an `apps list` poll loop.** Use `--wait` on `ingestions create` / `transformations apply` (Rule 6).
- **Passing column names in a raw `query run` body**, or hand-writing the aggregate AST. Bodies take hashed field ids from `query info`; use the `--group-by/--metric` sugar (Rule 7).
- **Patching `Cases.sql` on a source-system template.** That gotcha is `uipath.custom`-only; source templates ship correct transformations — feed the expected extract and extend, don't rewrite (Rule 3).
- **Using a source template for a single flat log** (or `uipath.custom` for a full multi-table extract). Match the template to the data shape (Rule 2).
- **Iterating on the full dataset.** Develop on `dev` with a small subset; publish the full data (Rule 8).
- **Changing a field's data kind while a comparison still uses the old kind.** Flipping a field to `duration` (or any kind) while a metric / calculated field / dashboard filter compares it to a constant of the old kind persists an invalid model that locks the app open (Rule 10). Reconcile the comparison first — re-type the field or the constant.
