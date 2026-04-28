# Charting inference for UiPath data

Given a piece of UiPath data, pick the chart type that answers the user's question clearly. Rules below are ordered: **answer the question first, minimize ink second, add decoration last.**

## Data shape → chart type

| Data shape | Primary chart | When to reach for a different one |
|---|---|---|
| Single number ("42 active agents") | KPI tile | Pair with a sparkline if a trend is meaningful |
| Single number + period-over-period delta | KPI tile with delta chip (↗ green / ↘ red) | — |
| Count over time, fine-grained (hourly / daily) | Vertical bar chart | Line chart if the count is large and trend-smoothness matters |
| Count over time, long window (months) | Line chart or area chart | Bars if discrete periods matter |
| Count by category, ≤ 6 categories | Vertical bar chart | Donut chart if the question is "what fraction?" not "what counts?" |
| Count by category, > 6 categories | Horizontal bar chart (sorted desc) | Avoid pie/donut — unreadable past ~5 slices |
| Rate / percentage | KPI tile (`X.X%`) with colored tone (green < 2%, amber < 10%, red ≥ 10%) + trend line for context | — |
| Ranked list with multiple columns (agent, count, error count, latency) | Data table, sortable | — |
| Two related time series (volume + errors) | Dual-axis line, OR stacked bar of success / fail | Small multiples if more than 2 series |
| Distribution of values (e.g., job durations) | Histogram | Box plot if you need outliers visible |
| Relationships or flows (case stages, Maestro process paths) | Sankey or funnel | Gantt if timing matters |
| Heat by day-of-week × hour-of-day | Heatmap | — |
| Location-based data | Map | — |

## Per-service defaults

| Service / data | Typical user question | Chart |
|---|---|---|
| Jobs by state | "What's the breakdown of my jobs?" | Bar (states on x-axis, count on y) |
| Jobs over time | "Volume today" / "hourly activity" | Hourly bar chart (24 bars, zero-filled) |
| Jobs by process (top N) | "Which agents ran most?" | Table with cols: process, invocations, errors, avg latency |
| Error rate trend | "Are we failing more?" | Daily bar chart (7 bars, zero-filled, red fill) |
| Process list | "What automations exist?" | Table |
| Queue list | "Which queues are defined?" | Table |
| Task by status | "What's pending action?" | Horizontal bar or table; show SLA risk inline with color |
| Task SLA | "What's about to breach?" | Table sorted by due date ascending, colored rows |
| Bucket file list | "What's in this bucket?" | Table with size, modified date |
| Entity records | "Data records matching filter X" | Data table with sort/filter |
| Maestro instance state | "What's the status of long-running processes?" | Stacked bar (by state) over time, OR Sankey of stage transitions |
| Maestro incidents | "Where are the bottlenecks?" | Horizontal bar by incident type, colored by severity |
| Case instances by status | "Case pipeline health" | Funnel (Open → Paused → Closed) |
| Agent conversations | "Conversation volume" | Line chart of conversations over time |
| Agent errors | "Agent reliability" | Pairs well with error-rate style KPI + daily bar trend |

## Zero-fill rule

For any **time-bucketed chart**, always zero-fill missing buckets. A missing hour or day rendered as a gap misleads the eye into interpreting it as "less than a spike" when it actually means "no data". Pre-generate the full bucket array (e.g., 24 hourly slots, 7 daily slots), then assign counts from your data. Use `zeroFill()` from the scaffold's `src/lib/utils.ts`.

## Axis-label rule

Use `Intl.DateTimeFormat` for all axis labels — it respects locale + TZ. The scaffold's `src/lib/format.ts` ships `fmtHour`, `fmtDay`, `fmtNumber`, `fmtPercent`, `fmtDuration` helpers. Hardcoded `"HH:00"` formats break for non-en users and for tenants in non-UTC local regions.

## Color rule

- **Success / "up is good" deltas**: `chart-3` (emerald).
- **Error / "down is good" deltas**: `chart-5` (red).
- **Neutral / informational**: `chart-1` (blue).
- **Amber/yellow**: `chart-4` (mid-risk state — error rate 2–10%, SLA nearing breach).
- Always pick Tailwind CSS-var tokens (`hsl(var(--chart-N))`) that have dark-mode variants. Hardcoded hex colors break in dark mode.

## ChartContainer setup (canonical)

```tsx
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

const chartConfig = {
  invocations: { label: "Invocations", color: "hsl(var(--chart-1))" },
} satisfies ChartConfig;

export function InvocationVolume({ data }: { data: {hour: string; invocations: number}[] }) {
  return (
    <ChartContainer config={chartConfig} className="h-60 w-full">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="invocations" fill="var(--color-invocations)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
```

Note: `var(--color-invocations)` is synthesized by `ChartContainer` from the `ChartConfig` key — no manual CSS-var plumbing.

## `ChartConfig` encoding

Each widget template derives its `ChartConfig` from the series names the data hook returns:

```ts
const chartConfig = {
  <seriesName>: {
    label: "<Human-readable>",
    color: "hsl(var(--chart-N))"   // semantic, per design-system.md
  },
  ...
} satisfies ChartConfig;
```

Rules:
1. **Series names come from the query hook's return shape**, not from user prompts or SDK method names.
2. **Colors come from the semantic token rule** in [design-system.md](design-system.md), not picked freely.
3. **One ChartConfig per widget**, exported alongside the widget JSX.
4. **ChartContainer's `className` sets height**; `h-60` for primary charts, `h-48` for secondaries, `h-20` for KPI sparklines.

## Anti-patterns

- Pie chart with > 5 slices. (Unreadable; use a sorted horizontal bar.)
- Line chart with fewer than ~6 data points. (Use bars — lines imply continuity.)
- Stacking categories that aren't parts-of-a-whole. (If "errors + warnings" don't add up to total jobs, don't stack.)
- Sparkline without a clear primary number. (Sparkline = context for a KPI; alone it's noise.)
- Dual-axis charts where the axes' scales compete for attention. (Prefer small multiples.)
- Widgets outside Cards. Every widget wraps in shadcn `<Card>`.
- Hardcoded hex colors. Always tokens.
- Generic empty state message. "No data" is banned; always widget-specific.
