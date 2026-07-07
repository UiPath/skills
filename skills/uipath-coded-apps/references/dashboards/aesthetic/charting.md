# Charting Guide

How to pick chart types, configure colors, and avoid common mistakes.

---

## Chart Type Selection

Valid `displayAs` values (the build accepts only these): `kpi-card`, `ranked-table`, `data-table`, `area-chart`, `line-chart`, `bar-chart`, `donut-chart`, `multi-line-chart`, `rate-chart`.

| User's metric | Use this | Why |
|---|---|---|
| Single number at a point in time | `kpi-card` | No trend needed |
| One metric over time (count, sum) | `area-chart` | Shows volume and trend |
| One metric over time (already a value series) | `line-chart` | Trend without fill weight |
| Ratio/percentage over time (numerator ÷ denominator) | `rate-chart` | Computes per-bucket %, % axis, pp delta |
| Comparing categories (bars) | `bar-chart` | Items to compare |
| Ranked list with a score | `ranked-table` | 5+ items, sortable |
| Part-of-whole proportions (≤5 categories) | `donut-chart` | Parts sum to 100% |
| Part-of-whole proportions (5+ categories) | `bar-chart` | Donut with 5+ slices is unreadable |
| Two metrics on the same time axis | `multi-line-chart` | Comparison over time |
| Raw records, drill-down detail | `data-table` | Operational view |

---

## Color Rules

### Always use CSS variable tokens

```tsx
// Correct
fill="hsl(var(--chart-1))"
stroke="hsl(var(--chart-2))"

// Wrong — hardcoded hex
fill="#FA4616"
stroke="#0066CC"
```

### Chart color series meaning

| Token | Color | Semantic use |
|---|---|---|
| `--chart-1` | UiPath orange | Primary data series, main metric |
| `--chart-2` | UiPath blue | Secondary series (e.g., P95 alongside P50) |
| `--chart-3` | Success green | "Up is good" deltas, completion rates |
| `--chart-4` | Warning amber | Approaching threshold, mid-risk |
| `--chart-5` | Error red | Errors, failures, "down is good" |

For multi-line charts (P50/P95):
- P50 → `--chart-1` (orange, primary)
- P95 → `--chart-2` (blue, secondary)

---

## Area vs Line

- **Area chart** (`area-chart`) → for volume metrics (count, invocations, AGU consumed)
  - Always use `fillOpacity={0.2}` to keep the area subtle
  - Fill and stroke use `--chart-1`

- **Line chart** (`line-chart`) → for rate/percentage metrics (error rate %, P95 latency)
  - No fill area — rates don't accumulate visually
  - `dot={false}` for smooth trend reading
  - `strokeWidth={2}` minimum

---

## Delta polarity guide

Deltas are **computed at runtime** — never hand-write delta text. You set one intent field per chart metric, `deltaPolarity`, which answers: is an increase good for this metric?

| Metric | `deltaPolarity` |
|---|---|
| Success rate, health score | `up-good` |
| Error count, failure rate | `up-bad` |
| AGU consumed (cost) | `up-bad` |
| Run volume (activity proxy) | `up-good` |
| Agent count (fleet growing) | `up-good` |
| Incidents, denials | `up-bad` |
| Memory counts (no inherent good direction) | `neutral` |

The build computes the % change (or `pp` for `rate-chart`) between the last two buckets and colours the badge from the polarity. The badge is hidden automatically when there's not enough data.

---

## Recharts Configuration Standards

```tsx
// XAxis — always small font
<XAxis dataKey="date" tick={{ fontSize: 11 }} />

// YAxis — always small font, no label
<YAxis tick={{ fontSize: 11 }} />

// Tooltip — default, no custom content unless specific need
<Tooltip />

// ResponsiveContainer — standard heights
// KPI sparkline: height={48}
// Chart row widget: height={180}
// Full-width chart: height={240}
```

---

## Anti-patterns

- Donut chart with >5 slices → use `bar-chart` instead
- Line chart with <4 data points → use `bar-chart` instead (clearer)
- Stacked bar unless values are genuinely parts-of-whole
- Sparkline without a primary number above it
- Hardcoded hex colors anywhere in chart config
- `fillOpacity={1}` on area charts — too heavy
- `dot={true}` on line charts with >30 data points — too noisy
- XAxis with long date strings — format with `tickFormatter`

---

## Axis Date Formatting

When x-axis is a date/time:

```tsx
// For hourly data (24h):
<XAxis
  dataKey="timeSlice"
  tick={{ fontSize: 11 }}
  tickFormatter={(v: string) => new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
/>

// For daily data (7d, 30d):
<XAxis
  dataKey="date"
  tick={{ fontSize: 11 }}
  tickFormatter={(v: string) => new Date(v).toLocaleDateString([], { month: 'short', day: 'numeric' })}
/>
```
