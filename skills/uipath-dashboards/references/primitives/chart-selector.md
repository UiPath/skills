# chart-selector

## Purpose
Given a data shape returned by the data-router's SDK call spec, pick the right widget template from `assets/templates/widgets/` and emit the `ChartConfig` object it needs (consumed by the local `ChartContainer` wrapper at `src/components/ui/chart.tsx`).

## Inputs
```ts
{
  kind: 'scalar' | 'time-series' | 'categorical' | 'ranked' | 'distribution' | 'two-series' | 'parts-of-whole' | 'funnel' | 'heatmap',
  cardinality: number,
  bucket?: 'hourly' | 'daily' | 'weekly' | 'monthly',
  hasDelta?: boolean,
  hasSparkline?: boolean
}
```

## Outputs
```ts
{
  chartType: string,               // e.g., 'bar-chart', 'kpi-with-delta'
  widgetTemplate: string,          // e.g., 'bar-chart.tsx.template'
  chartConfig: Record<string, {label: string, color: string}>,
  dataMapping: {xKey: string, yKeys: string[]}
}
```

## Rules
1. **Follow the taxonomy in [../aesthetic/charting.md](../aesthetic/charting.md)** — that's the canonical data-shape → chart-type matrix.
2. **Never pie with > 5 slices.** Degrade to `horizontal-bar`.
3. **Dual-axis is last resort.** Prefer small-multiples (two widgets side by side) when series compete.
4. **Time-bucketed outputs always `zeroFill: true`** — enforced in widget templates.
5. **Color semantic, never decorative.** Map to `chart-1..5` Tailwind tokens per [../aesthetic/design-system.md](../aesthetic/design-system.md).

## Selection table

| `kind` | `cardinality` | Additional signal | → `chartType` | Template |
|---|---|---|---|---|
| scalar | 1 | `!hasDelta && !hasSparkline` | `kpi-tile` | `kpi-tile.tsx.template` |
| scalar | 1 | `hasDelta` | `kpi-with-delta` | `kpi-with-delta.tsx.template` |
| scalar | 1 | `hasSparkline` | `kpi-with-sparkline` | `kpi-with-sparkline.tsx.template` |
| time-series | any | `bucket==='hourly'\|'daily'` | `bar-chart` | `bar-chart.tsx.template` |
| time-series | any | long window (monthly+) | `line-chart` | `line-chart.tsx.template` |
| time-series | any | cumulative | `area-chart` | `area-chart.tsx.template` |
| categorical | ≤6 | — | `bar-chart` (vertical) | `bar-chart.tsx.template` |
| categorical | >6 | — | `horizontal-bar` (sorted desc) | `horizontal-bar.tsx.template` |
| ranked | any | multi-column | `ranked-table` | `ranked-table.tsx.template` |
| two-series | 2 | volume + rate | `dual-axis-chart` | `dual-axis-chart.tsx.template` |
| parts-of-whole | ≤5 | — | `donut-chart` | `donut-chart.tsx.template` |
| parts-of-whole | >5 | — | degrade to `progress-bar-list` | `progress-bar-list.tsx.template` |
| share-of-total | any | "X by Y with %" | `progress-bar-list` | `progress-bar-list.tsx.template` |
| funnel | stages | — | `funnel` | `funnel.tsx.template` |
| heatmap | 7×24 | day × hour | `heatmap` | `heatmap.tsx.template` |

### ChartConfig derivation
Series names come from the SDK call result shape; colors from the token rule:
- Primary series → `hsl(var(--chart-1))`
- Error/destructive → `hsl(var(--chart-5))`
- Success/positive → `hsl(var(--chart-3))`
- Warning → `hsl(var(--chart-4))`
- Secondary → `hsl(var(--chart-2))`

Example:
```ts
const chartConfig = {
  invocations: { label: "Invocations", color: "hsl(var(--chart-1))" },
  errors: { label: "Errors", color: "hsl(var(--chart-5))" }
} satisfies ChartConfig;
```

### Error paths
| Condition | Action |
|---|---|
| No table entry matches | Halt; surface the `kind`/`cardinality` combo and ask user to clarify. |
| User explicitly requests a chart type that violates rules (e.g., "pie with 20 slices") | Warn + degrade; document the decision in the narration. |
