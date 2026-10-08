# Querying a process app (`uip pm query`)

Use `info` for metadata, `run` for aggregate group-by + metrics, `details` for raw rows, `percentile`, `rca` for root-cause, `insights` for process insights, and `layout`. All take `--stage dev|published` (default `dev`); iterate on `dev`. After `apps publish`, run `ingestions create <app> --stage published --wait`. A `published` query requires a completed ingestion on that stage or returns 400 `UserError_InvalidOrNoIngestion` (see [`lifecycle-and-rbac.md`](lifecycle-and-rbac.md)).

## Start with `query info`

`query info <app>` returns queryable entities (`Cases`, `Event_log`, `Tags`, `Due_dates`, `__Process_Events`, process internals, and tables added to the data model) and fields with ids. Query bodies require field ids, not column names; otherwise they return `UserError_FieldNotFound`. IDs are usually hashed (e.g. `F__Cases__Service_Component__f0f7…`); some standard fields retain plain ids (`Case_ID`, `Event_count`).

## Prefer the sugar over hand-writing the AST

```bash
uip pm query run <app> --group-by Open_year --metric Event_count:average --metric Case_ID:count --output table
```

`--group-by <cols>` accepts comma-separated names or ids. Repeatable `--metric <col:fn[:alias]>` resolves names to ids via `query info`, builds the body, and transposes the columnar response into rows (useful with `--output table`). `fn` ∈ `average | count | sum | min | max`. Sugar and raw `--body`/`--body-json` are mutually exclusive.

## The raw aggregate body (`AggregateDataRequestDto`)

```json
{ "groupBy": ["<fieldId>", "..."],
  "aggregates": [ { "id": "<yourName>", "argument": "<fieldId>", "aggregation": "<fn>" } ] }
```

- `aggregation` must be an `AggregationFunction` enum: `average`, `count`, `sum`, `min`, `max`. Invalid values (e.g. `maximum`) return 400 with a raw .NET enum-convert error.
- `Data` is columnar: each group field and aggregate has an entry keyed by its id, shaped `{ "values": [...per group...], "ungrouped": <grand total>, "stackValues": null }`; arrays are index-aligned. Raw keys are camelCase (`values`/`ungrouped`); CLI `--output json/table` may present them PascalCase.
- With `"groupBy": []`, the total is in `ungrouped`, or `values[0]` if the engine emits a single-row column.

## Restrictions & other subcommands

- Grouping by an `Event_log` (event-table) field returns 400 `UserError_EventTableUsedInQuery`; `run` aggregates case-level entities only. For event/activity breakdowns, use `insights` (`processId` + 1..10 numeric `metrics` from `query info`) or `layout`; alternatively, precompute event-log activity counts in a dbt model, register it as a data-model table ([`data-model.md`](data-model.md)), then query it with `query run`.
- `percentile --field <id> --values 0.5,0.9,0.95 [--filters <json>]` accepts points in 0..1.
- `rca` requires a non-empty `selectedSet`; `insights` requires a `processId` and 1..10 numeric `metrics`.
- `details` returns raw rows (`DetailsDataRequestDto`); server-side, `--limit` is clamped to 1..1000.

## Getting custom analytics out

Register a custom dbt model as a data-model table before querying it (see [`data-model.md`](data-model.md)); registered tables support the sugar, aggregate AST, and percentiles above.