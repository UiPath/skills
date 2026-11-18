# Querying a process app (`uip pm query`)

Pull numbers out of a built app. Subcommands: `info` (metadata), `run`
(aggregate group-by + metrics), `details` (raw rows), `percentile`, `rca`
(root-cause), `insights` (process insights), `layout`. All take `--stage
dev|published` (default `dev`). Iterate on **`dev`**; `--stage published` needs a
completed ingestion **on that stage** — run
`ingestions create <app> --stage published --wait` after `apps publish`. Until that
ingestion completes the query 400s `UserError_InvalidOrNoIngestion` (see
[`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)).

## Start with `query info`

`query info <app>` returns the queryable model: entities (`Cases`, `Event_log`,
`Tags`, `Due_dates`, `__Process_Events`, process internals, **plus any table you
added to the data model**) and, per entity, the **fields** with their ids. Field
ids are hashed, e.g. `F__Cases__Service_Component__f0f7…`; a few standard fields
keep plain ids (`Case_ID`, `Event_count`). Raw query bodies reference **ids**, not
column names (`UserError_FieldNotFound` otherwise). Per-process measures are listed
under `InternalFields.Processes[]`: `Cases.CaseThroughputTime` (a `PF__…` id),
`Events.Activity`, `Events.TableId` and so on.

## Prefer the sugar over hand-writing the AST

```bash
uip pm query run <app> --group-by Open_year --metric Event_count:average --metric Case_ID:count --output table
```

`--group-by <cols>` (comma-separated names or ids) and `--metric <col:fn[:alias]>`
(repeatable) resolve human column names to ids via `query info`, build the body,
and **transpose the engine's columnar response into rows** (great with `--output
table`). `fn` is one of the `aggregation` values of the raw body below. The sugar and a raw `--body`/`--body-json` are
mutually exclusive. A name is matched against each field's column, case-insensitively,
and the first table in `query info` that has it wins (`Cases` first).

## The raw aggregate body (`AggregateDataRequestDto`)

```json
{ "groupBy": ["<fieldId>", "..."],
  "aggregates": [ { "id": "<yourName>", "argument": "<fieldId>", "aggregation": "<fn>" } ] }
```

- `aggregation` is the **`AggregationFunction` enum**, read case-insensitively:
  `any`, `average`, `count`, `distinct_count`, `forall`, `forany`, `max`, `median`,
  `min`, `percentage`, `sum`. These are the values the `{ id, argument, aggregation }`
  aggregate form takes; for a percentile use `query percentile`. Invalid values (e.g.
  `maximum`) 400 with a raw .NET enum-convert error.
- The response `Data` is **columnar**: one entry per group field and per
  aggregate, keyed by the id, each `{ "values": [...per group...], "ungrouped":
  <grand total>, "stackValues": null }`. Group and aggregate arrays are
  **index-aligned**. (Note: the raw object is camelCase `values`/`ungrouped`; the
  CLI's `--output json/table` formatter may present them PascalCase.)
- Ungrouped-only queries (`"groupBy": []`) return the total in `ungrouped`, or in
  `values[0]` when the engine emits it as a single-row column.

## Restrictions & other subcommands

- **A field of the raw event-log input table (`Event_log`) 400s**
  `UserError_EventTableUsedInQuery`. The same events, mined, are queryable on each
  process's events table (`InternalFields.Processes[].Events.TableId`, usually
  `__Process_Events`). There, event-log columns you mapped keep their names (a `Team`
  column is `F__Process_Events__Team`), but the standard ones are
  `__InternalField_<name>` columns. A plain `--group-by Activity` therefore lands on
  `Event_log` and fails. Use the process's `Events.Activity` id instead:
  ```bash
  uip pm query run <app> --group-by PF__Process_Events___InternalField_Activity --metric Case_ID:distinct_count
  ```
  The CLI's error names that id for the app. For anything the events table does not
  carry, precompute it in a dbt model, register that as a data-model table
  ([`data-model.md`](data-model.md)), re-ingest, and `query run` it.
- `percentile --field <column-or-id> --values 0.5,0.9,0.95 [--filters <json>]`, with
  points in 0..1. A column name is resolved like the sugar's. Case throughput time is
  a process measure: pass its `PF__…` id (`InternalFields.Processes[].Cases.CaseThroughputTime`).
- `rca` needs a non-empty `selectedSet`.
- `details` returns raw rows; `--limit` is clamped 1..1000 server-side. The body
  (`DetailsDataRequestDto`) is `{ "columns": [<fieldId>…] }`, with optional `filters`
  and `sort`; an empty body is `UserError_EmptyQuery`. The response is columnar,
  `{ Data: { <fieldId>: [...] }, Pagination }`.
  ```bash
  uip pm query details <app> --limit 50 --body-json '{"columns":["Case_ID","Event_count"]}'
  ```
- `insights` needs the `processId` (from `InternalFields.Processes[]`) and 1..10 numeric
  `metrics`, each shaped like a `query run` aggregate. Unknown keys are rejected with a
  model-binding error (`Could not find member 'metric'…`).
  ```bash
  uip pm query insights <app> --body-json '{"processId":"Process","metrics":[{"id":"events","argument":"Event_count","aggregation":"sum"}]}'
  ```
  `uip pm query details --help` and `uip pm query insights --help` show the same
  example bodies.

## Getting custom analytics out

If your numbers live in a custom dbt model, you must first register it as a
data-model table so `query` can see it — see [`data-model.md`](data-model.md).
Once registered, everything above (sugar, aggregate AST, percentiles) works on it.
