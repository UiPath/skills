# Querying a process app (`uip pm query`)

Pull numbers out of a built app. Subcommands: `info` (metadata), `run`
(aggregate group-by + metrics), `details` (raw rows), `percentile`, `rca`
(root-cause), `insights` (process insights), `layout`. All take `--stage
dev|published` (default `dev`).

## Start with `query info`

`query info <app>` returns the queryable model: entities (`Cases`, `Event_log`,
`Tags`, `Due_dates`, `__Process_Events`, process internals, **plus any table you
added to the data model**) and, per entity, the **fields** with their ids. Field
ids are hashed, e.g. `F__Cases__Service_Component__f0f7…`; a few standard fields
keep plain ids (`Case_ID`, `Event_count`). Query bodies reference **ids**, not
column names (`UserError_FieldNotFound` otherwise).

## Prefer the sugar over hand-writing the AST

```bash
uip pm query run <app> --group-by Open_year --metric Event_count:average --metric Case_ID:count --output table
```

`--group-by <cols>` (comma-separated names or ids) and `--metric <col:fn[:alias]>`
(repeatable) resolve human column names to ids via `query info`, build the body,
and **transpose the engine's columnar response into rows** (great with `--output
table`). `fn` ∈ `average | count | sum | min | max`. The sugar and a raw
`--body`/`--body-json` are mutually exclusive.

## The raw aggregate body (`AggregateDataRequestDto`)

```json
{ "groupBy": ["<fieldId>", "..."],
  "aggregates": [ { "id": "<yourName>", "argument": "<fieldId>", "aggregation": "<fn>" } ] }
```

- `aggregation` is the **`AggregationFunction` enum**: `average`, `count`, `sum`,
  `min`, `max`. Invalid values (e.g. `maximum`) 400 with a raw .NET enum-convert
  error.
- The response `Data` is **columnar**: one entry per group field and per
  aggregate, keyed by the id, each `{ "values": [...per group...], "ungrouped":
  <grand total>, "stackValues": null }`. Group and aggregate arrays are
  **index-aligned**. (Note: the raw object is camelCase `values`/`ungrouped`; the
  CLI's `--output json/table` formatter may present them PascalCase.)
- Ungrouped-only queries (`"groupBy": []`) return the total in `ungrouped`, or in
  `values[0]` when the engine emits it as a single-row column.

## Restrictions & other subcommands

- **`groupBy` on an `Event_log` (event-table) field 400s** `UserError_EventTableUsedInQuery`.
  Event-level frequencies come from the process model / `insights`, not `run`.
- `percentile --field <id> --values 0.5,0.9,0.95 [--filters <json>]` — points in 0..1.
- `rca` needs a non-empty `selectedSet`; `insights` needs a `processId` and 1..10 numeric `metrics`.
- `details` returns raw rows (`DetailsDataRequestDto`); `--limit` is clamped 1..1000 server-side.

## Getting custom analytics out

If your numbers live in a custom dbt model, you must first register it as a
data-model table so `query` can see it — see [`data-model.md`](data-model.md).
Once registered, everything above (sugar, aggregate AST, percentiles) works on it.
