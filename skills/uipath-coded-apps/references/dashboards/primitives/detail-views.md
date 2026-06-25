# Detail Views

A chart widget drills down to a detail view at `/<foo>`. The view shows **individual records** — the rows *behind* the chart — not the chart's aggregated buckets. It uses `DetailViewShell` + `RecordsTable`.

## What gets generated

For each chart widget `Foo`, the build generates `src/dashboard/views/FooView.tsx` and registers its route in `App.tsx`.

Detail views are generated for:

- **Chart widgets** (`line-chart`, `area-chart`, `bar-chart`, `donut-chart`, `multi-line-chart`, `rate-chart`) — any tier — at `/<foo>`. Every chart module **must** export `fetchDetail` (the build hard-fails with `CHART_DETAIL_MISSING` otherwise) **unless** its registry entry sets `"noDetail": true`. A `noDetail` chart (endpoint returns only pre-aggregated data) gets no view and renders a non-clickable card.
- **KPI cards with `detail: true`** — at `/<foo>`. The card becomes clickable (cursor-pointer + a "View all" link) and the module must export `fetchDetail`. A plain KPI (no `detail`) links nowhere.
- **Tables with a `rowLink`** (see below). A plain table (no `rowLink`) links nowhere and shows its rows in place.

> **Contract:** every widget that emits a navigation link must have a generated view + route, and vice-versa — `widgetGetsDetailView()` in the build is the single decision. Never emit `navigate()` / `ViewAllLink` / `onRowClick` without the build generating the matching view.

## Row-click drill-down (tables)

A `data-table`/`ranked-table` metric with `rowLink: { key: "<rowField>" }` becomes clickable: clicking a row navigates to `/<widget>/:key` (the clicked row's `<rowField>` is the `:key`). The build generates `views/<Widget>DetailView.tsx`, which reads the route param and calls the module's **`fetchDetailByKey(sdk, key, getToken)`** (type `MetricDetailByKeyFn`). Use it to show the entity behind the row — e.g. click an agent → that agent's most-recent trace's spans (recipe in `sdk/orchestrator.md`).

- The module exports BOTH `fetchData` (the table rows) and `fetchDetailByKey` (the per-key drill-down).
- `detailColumns` (optional) styles the detail table; without it columns auto-detect.
- The detail page has a back link via `DetailViewShell`.

## Record grain — the detail must add information

The chart's `fetchData` returns **aggregated buckets** (e.g. `{ date, count }`). A detail view that re-tables those buckets adds nothing. So the module supplies a separate record-grain query:

- **`fetchDetail: MetricFn`** (in the same module) — fetches the individual records (e.g. each faulted job: `{ processName, state, createdTime, ... }`). The view runs this, not the chart's aggregate. It is **required** for every chart (and `detail: true` KPI); the build hard-fails with `CHART_DETAIL_MISSING` if it is missing and the registry isn't `noDetail`. For cataloged metrics the registry entry's `detailRecipe` gives the exact SDK call.
- **`detailColumns`** — `{ key, label, align?, format?, color? }[]`. `format`: `number` | `percent` | `duration` | `timeAgo` | `text`; `color`: `goodHigh` | `goodLow`. The build compiles these into formatted/coloured `render` functions. Set on the metric, or inherit the registry entry's `defaults.detailColumns` (cataloged charts ship them). If neither is present, columns are auto-detected from the first row at runtime (`autoColumns`) — workable but generic.
- **`detailSortKey`** — the raw field to sort on (e.g. ISO `createdTime`). Render a friendly label in the column but sort on the raw value so chronological order is correct.

## toRows() — safe array extraction

The generated view calls `toRows(data)` before `RecordsTable`, handling `{ items: [...] }`, `{ data: [...] }`, a nested `data` object, or a top-level array. Defined inside every view file — no import needed.

## Rich detail views (charts)

A detail view can render multiple sub-widgets via an optional `detailView: { widgets: [...] }` on the metric. Each sub-widget declares:

- `displayAs` — `donut-chart` | `bar-chart` | `area-chart` | `line-chart` | `multi-line-chart` | `data-table` | `ranked-table`
- `title` — sub-widget heading
- `source` — key into the named-source map returned by the detail fetch
- Chart sub-widgets: `xKey` + `yKey`; multi-line uses `xKey` + `series[]` (`[{key,color,label?}]`)
- Table sub-widgets: optional `columns` (`{ key, label, align?, format?, color? }[]`)

> Sub-widgets are NOT limited to donuts. `bar-chart`, `area-chart`, `line-chart`, and `multi-line-chart`
> (with `series`) are fully wired — see the `agent-compliance-report` detailView in
> `assets/scripts/dashboards/capability-registry.json` for a `multi-line-chart` (Pass vs Matched by hook) + `donut-chart`
> + `ranked-table` + `data-table` in one view.

The detail fetch (`fetchDetailByKey` for `rowLink`, `fetchDetail` for a `detail: true` chart/KPI) must return a **named-source map** `{ rows, byHook, byRule, … }` whose keys match each sub-widget's `source`. A bare array = legacy single-table behaviour (the view normalizes `array → { rows }`).

Charts render via presentational components in `@/dashboard/charts` (`Donut` / `Bars` / `TrendArea` / `MultiLine`); tables via `RecordsTable`. Each sub-widget renders its own EmptyState when its `source` is empty.

The RICH multi-widget `detailView` is valid only on a metric with `rowLink.key` (table) or `detail: true` (chart/KPI). A **basic** chart drill-down (single records table) needs only `fetchDetail` — no `detailView` and no `detail` flag.

## Anti-patterns

- **Never** ship a chart detail view backed by the chart's aggregate `fetchData` — export `fetchDetail` so the drill-down shows records. The build hard-fails (`CHART_DETAIL_MISSING`) if you forget; the only opt-out is a registry `noDetail` chart.
- **Never** sort a time column on its rendered label — key the sort on the raw ISO field via `detailSortKey`.
- **Never** emit `navigate()` / `ViewAllLink` from a widget the build won't generate a view for.
- **Never** declare the rich `detailView` on a metric without `rowLink.key` or `detail:true` — the build rejects it.
- **Never** return an aggregate-only array when `detailView` declares chart sources — return the named-source map so each sub-widget has data.
