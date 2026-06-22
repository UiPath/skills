# Layout Patterns

Ten rules for dashboard layout. Follow them every time. Do not improvise.

---

## The 10 Rules

### Rule 1 — Dashboard header is mandatory

Every dashboard starts with a `<Header>` component:
```tsx
<Header
  title="Agent Health Dashboard"
  description="Agent invocation volume, error rates, and performance across your fleet."
/>
```

The description must answer "what does this dashboard help you do?" in one sentence.
Never leave it empty.

### Rule 2 — KPI tiles come first

KPI tiles (1–4 tiles) occupy the first row, always. Use a responsive grid:
```tsx
<div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* KPI widgets */}
</div>
```

- 1 KPI → `lg:grid-cols-1`
- 2 KPIs → `lg:grid-cols-2`
- 3 KPIs → `lg:grid-cols-3`
- 4 KPIs → `lg:grid-cols-4`

Never put a chart in the KPI row.

### Rule 3 — Charts come second, in a 2-up grid

Charts (area, line, bar, donut, multi-line, rate) go in a 2-column grid:
```tsx
<div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
  {/* Chart widgets */}
</div>
```

If there are 3+ charts, they wrap to a second row — still `grid-cols-2`.
If there is only 1 chart, it takes full width: `grid-cols-1`.

### Rule 4 — Tables come last, full width

Tables (data-table, ranked-table) always go at the bottom:
```tsx
<div className="mt-6">
  <WidgetBoundary label="Top Agents">
    <TopAgentsRankedTable />
  </WidgetBoundary>
</div>
```

Tables are `col-span-full` by default. Never put a table in a 2-up grid.

### Rule 5 — Every widget is wrapped in WidgetBoundary

```tsx
<WidgetBoundary label="Active Agents">
  <ActiveAgentsKPI />
</WidgetBoundary>
```

The `label` is the human name of the widget — it shows in the error card if the widget throws.
Never render a widget without WidgetBoundary.

### Rule 6 — Gaps are always gap-4

Use `gap-4` (16px) between ALL widgets on ALL rows. No exceptions, no per-widget overrides.

### Rule 7 — Page padding is responsive

```tsx
<div className="min-h-screen bg-background text-foreground p-4 lg:p-8">
```

- Mobile: `p-4` (16px)
- Desktop (lg+): `p-8` (32px)

### Rule 8 — Rows are separated with mt-6

Each row has `mt-6` (24px) top margin. The header has no margin below it.

### Rule 9 — Never more than 4 widgets in the KPI row

If the user requests 5+ KPIs, split into two rows. Never shrink tiles to fit more than 4.

### Rule 10 — Tables do NOT have `cursor-pointer` on the card

Individual table rows can be clickable, but the Card wrapper on a data-table or ranked-table should NOT be `cursor-pointer` — the row click is enough.
KPI tiles and chart cards ARE `cursor-pointer` because the whole card navigates to the detail view.

---

## Dashboard.tsx Skeleton

```tsx
import { Header } from '@/dashboard/chrome/Header'
import { WidgetBoundary } from '@/dashboard/chrome/WidgetBoundary'
// WIDGET_IMPORTS

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 lg:p-8">
      <Header
        title="<Dashboard Title>"
        description="<One sentence describing what this dashboard helps you do.>"
      />

      {/* Row 1: KPIs (1–4 tiles) */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-<N> gap-4">
        <WidgetBoundary label="<KPI 1 label>"><KPI1 /></WidgetBoundary>
        {/* ... */}
      </div>

      {/* Row 2: Charts (2-up grid, wraps automatically) */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WidgetBoundary label="<Chart 1 label>"><Chart1 /></WidgetBoundary>
        <WidgetBoundary label="<Chart 2 label>"><Chart2 /></WidgetBoundary>
      </div>

      {/* Row 3: Tables (full width) */}
      <div className="mt-6">
        <WidgetBoundary label="<Table label>"><Table1 /></WidgetBoundary>
      </div>
    </div>
  )
}
```

---

## Anti-patterns

- Chart in KPI row
- Table in 2-up grid
- Widget without WidgetBoundary
- `gap-6` or any gap other than `gap-4`
- More than 4 KPIs in one row
- Header with empty description
- `cursor-pointer` on table card wrapper
