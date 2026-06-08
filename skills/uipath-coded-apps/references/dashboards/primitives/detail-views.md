# Detail Views

Every widget automatically gets a detail view file generated at build time. Detail views use `DetailViewShell` + `RecordsTable` to show all rows from the same API call as the parent widget.

## What gets generated

For each widget with component name `Foo`, the build script generates `src/dashboard/views/FooView.tsx` and registers a route at `/<foo>` in `App.tsx`.

Detail views are generated automatically for **T1 widgets only**.

- **T2 widgets**: already show tabular data — no separate detail view needed
- **T3-SDK widgets**: the `fnBody` returns a custom shape that the build script has no schema for — columns can't be inferred reliably at build time. The widget itself shows the full data. Add a detail view by hand in the generated project if needed.

## Column mapping rules

The columns for a detail view come from the same registry entry as its parent widget. The key rules:

| Response shape | What to use as columns |
|----------------|------------------------|
| `{ data: Array<{ name, count }> }` | `name` + `count` — never `value` |
| `{ data: Array<{ timeSlice, aguConsumption }> }` | `timeSlice` + `aguConsumption` |
| `{ data: Array<{ name, P50, P95, date }> }` (after pivot) | `date` + `P50` + `P95` |
| `{ data: { agents: [...] } }` | `toRows()` unwraps the nested array automatically |

**Rule: column `key` must match the exact field name in the API response — never substitute `value` as a generic stand-in.**

## toRows() — safe array extraction

The generated view always calls `toRows(raw)` before passing data to `RecordsTable`. This handles the three response shapes Insights RTM returns:

```typescript
// Shape 1: direct array  { data: [...] }
// Shape 2: nested object  { data: { agents: [...] } }
// Shape 3: raw array at top level
```

`toRows` is defined inside every generated view file — no import needed.

## Detail view per widget type

| Parent widget template | Detail view shows |
|-----------------------|-------------------|
| `kpi-card` | Table of all data points |
| `kpi-with-sparkline` | Table of all data points |
| `line-chart` | Table of date + value columns |
| `area-chart` | Table of date + value columns |
| `multi-line-chart` | Table of date + P50 + P95 columns |
| `ranked-table` | Already full-detail — view shows same data |
| `data-table` | Already full-detail |
| `donut-chart` | Table of name + value/count |
| `bar-chart` | Table of name + value |

## Anti-patterns

- **Never** use `key: "value"` in columns if the API response field is named something else (`count`, `aguConsumption`, etc.)
- **Never** call `dataSelector` directly without wrapping in `toRows()` — some responses are objects, not arrays
- **Never** generate a detail view for T2 widgets — they are already tabular
