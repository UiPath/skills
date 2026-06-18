# Detail Views

A chart widget drills down to a detail view at `/<foo>`. The view shows **individual records** — the rows *behind* the chart — not the chart's aggregated buckets. It uses `DetailViewShell` + `RecordsTable`.

## What gets generated

For each chart widget `Foo`, the build generates `src/dashboard/views/FooView.tsx` and registers its route in `App.tsx`.

Detail views are generated for **chart widgets** (`line-chart`, `area-chart`, `bar-chart`, `donut-chart`, `multi-line-chart`, `rate-chart`) — any tier — at `/<foo>`, and for **tables with a `rowLink`** (see below). KPI cards and plain tables (no `rowLink`) link nowhere and show their value/rows in place.

> **Contract:** every widget that emits a navigation link must have a generated view + route. Never emit `navigate()` / `ViewAllLink` / `onRowClick` without the build generating the matching view.

## Row-click drill-down (tables)

A `data-table`/`ranked-table` metric with `rowLink: { key: "<rowField>" }` becomes clickable: clicking a row navigates to `/<widget>/:key` (the clicked row's `<rowField>` is the `:key`). The build generates `views/<Widget>DetailView.tsx`, which reads the route param and calls the module's **`fetchDetailByKey(sdk, key, getToken)`** (type `MetricDetailByKeyFn`). Use it to show the entity behind the row — e.g. click an agent → that agent's most-recent trace's spans (recipe in `sdk/orchestrator.md`).

- The module exports BOTH `fetchData` (the table rows) and `fetchDetailByKey` (the per-key drill-down).
- `detailColumns` (optional) styles the detail table; without it columns auto-detect.
- The detail page has a back link via `DetailViewShell`.

## Record grain — the detail must add information

The chart's `fnBody` returns **aggregated buckets** (e.g. `{ date, count }`). A detail view that re-tables those buckets adds nothing. So a metric supplies a separate record-grain query:

- **`detailFnBody`** — fetches the individual records (e.g. each faulted job: `{ processName, state, createdTime, ... }`). The view runs this, not the chart's aggregate. If omitted, it falls back to the chart's `fnBody` — which only restates the buckets, so **always provide `detailFnBody` for charts**.
- **`detailColumns`** — `{ key, label, align?, format?, color? }[]`. `format`: `number` | `percent` | `duration` | `timeAgo` | `text`; `color`: `goodHigh` | `goodLow`. The build compiles these into formatted/coloured `render` functions. If omitted, columns are auto-detected from the first row at runtime (`autoColumns`) — workable but generic.
- **`detailSortKey`** — the raw field to sort on (e.g. ISO `createdTime`). Render a friendly label in the column but sort on the raw value so chronological order is correct.

## toRows() — safe array extraction

The generated view calls `toRows(data)` before `RecordsTable`, handling `{ items: [...] }`, `{ data: [...] }`, a nested `data` object, or a top-level array. Defined inside every view file — no import needed.

## Anti-patterns

- **Never** ship a chart detail view backed by the chart's aggregate `fnBody` — supply `detailFnBody` so the drill-down shows records.
- **Never** sort a time column on its rendered label — key the sort on the raw ISO field via `detailSortKey`.
- **Never** emit `navigate()` / `ViewAllLink` from a widget the build won't generate a view for.
