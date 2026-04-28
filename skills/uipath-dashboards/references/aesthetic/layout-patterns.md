# Layout patterns for dashboards

Rules the generator follows when composing `Dashboard.tsx`. These encode "beautiful and informative" as reproducible code patterns.

## 10 rules

1. **Dashboard header** with title AND description. "Agent Health / Agent invocation volume, error rates, and performance metrics." Never just a title. Description is a one-sentence declaration of scope. The `Header` primitive accepts `title` + `description` props.
2. **KPI row at top.** 1–4 tiles, equal-width: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`. NEVER more than 4 KPIs; if more are wanted, promote overflow into a ranked-table below. **Entire KPI card is a `<a href={detailHref}>`** — whole tile clickable, not just a corner link.
3. **Chart row: 2-up grid.** `grid-cols-1 lg:grid-cols-2 gap-4`. Two chart cards side-by-side. If >2 charts, wrap to a second 2-up row below. Flat 2-up grids compose more consistently than mixed primary-full-width + secondary layouts.
4. **Tables full-width last.** Densest content; bottom placement. Spans the full container width. Rows are `cursor-pointer hover:bg-muted/50` with drill-down navigation on click.
5. **Gutters uniform.** `gap-4` (16px) between cards in rows. Card padding `p-5` for chart/KPI tiles, `p-0` for tables (the Table component controls its own padding). Page padding `p-8` lg / `p-4` sm.
7. **Every widget in a Card AND wrapped in `<WidgetBoundary>`.** No free-floating JSX. `<WidgetBoundary label="<widget title>">` isolates failures — a throw in one widget renders a compact inline error card in that tile only; the rest of the dashboard keeps rendering. Without per-widget boundaries, one SDK shape drift or missing scope takes the whole dashboard dark. See `assets/templates/scaffold/src/dashboard/chrome/WidgetBoundary.tsx.template`.
8. **Every widget obeys [widget-anatomy.md](widget-anatomy.md).** Six parts — icon (KPIs), title, description, headline-with-delta (metric widgets), body, optional info-tooltip, view-all-link (charts + tables). Missing any required part = generator bug; halt and fix.
9. **Every widget routes to a real detail view.** Clickable affordances navigate to `/<kebab-slug>` (HashRouter) where a `<WidgetName>View.tsx` renders the widget's underlying records without aggregation. No placeholder hashes. The generator produces a view AND a list-style query hook for every widget it emits — see [detail-views.md](detail-views.md).
10. **`chrome/Header.tsx` at top** — humanized `state.app.name` + description + an optional right-side Refresh button when polling is wired. No theme toggle.
11. **Light mode only (no toggle in v1).** `<body>` is rendered with `class="light"` and stays there. No `ThemeToggle` component, no body-class-swapping script, no localStorage-backed theme state. Dark-mode CSS variables remain defined in `index.css` as dormant infrastructure for a future revision; nothing in chrome activates them today. See [design-system.md § Light mode only](design-system.md).
12. **Density "comfortable".** Table rows `py-3` not `py-1`. Breathing room matters more than density on first load.
13. **No auto-generated dashboard title.** Humanize `state.app.name` (`agent-health-dashboard` → `Agent Health Dashboard`). Widget titles come from user intent, not SDK method name.

## `Dashboard.tsx` skeleton (what the generator writes)

```tsx
import { Header } from './chrome/Header';
// + imports per widget
import { ActiveAgentsKPI } from './widgets/ActiveAgentsKPI';
import { InvocationsTodayKPI } from './widgets/InvocationsTodayKPI';
import { AvgResponseTimeKPI } from './widgets/AvgResponseTimeKPI';
import { ErrorRateKPI } from './widgets/ErrorRateKPI';
import { InvocationVolume } from './widgets/InvocationVolume';
import { ErrorRateTrend } from './widgets/ErrorRateTrend';
import { TopAgentsTable } from './widgets/TopAgentsTable';
import type { UiPath } from '@uipath/uipath-typescript/core';

export function Dashboard({ sdk }: { sdk: UiPath }) {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 lg:p-8">
      <Header
        title="Agent Health"
        description="Agent invocation volume, error rates, and performance metrics."
      />

      {/* Row 1: KPI row — each widget wrapped in <WidgetBoundary> so one
          widget's failure stays local. */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <WidgetBoundary label="Active agents"><ActiveAgentsKPI sdk={sdk} /></WidgetBoundary>
        <WidgetBoundary label="Invocations today"><InvocationsTodayKPI sdk={sdk} /></WidgetBoundary>
        <WidgetBoundary label="Avg response time"><AvgResponseTimeKPI sdk={sdk} /></WidgetBoundary>
        <WidgetBoundary label="Error rate"><ErrorRateKPI sdk={sdk} /></WidgetBoundary>
      </div>

      {/* Row 2: chart row — 2-up grid */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WidgetBoundary label="Invocation volume"><InvocationVolume sdk={sdk} /></WidgetBoundary>
        <WidgetBoundary label="Error rate trend"><ErrorRateTrend sdk={sdk} /></WidgetBoundary>
      </div>

      {/* Row 3: full-width table (tables always last) */}
      <div className="mt-6">
        <WidgetBoundary label="Top agents"><TopAgentsTable sdk={sdk} /></WidgetBoundary>
      </div>
    </div>
  );
}
```

## States per widget (loading / empty / error / degraded)

Every widget handles four states via the scaffold's `chrome/` primitives:

| State | Trigger | Widget renders |
|---|---|---|
| **Loading** | query `isLoading === true` | `<LoadingState>` with widget's natural dimensions |
| **Empty** | `data.length === 0` | `<EmptyState message="<specific>" />` — message must be specific ("No agent invocations in last 24h"), not generic ("No data") |
| **Error** | query throws | `<ErrorBoundary>` catches; shows retry button; `console.warn` (not error) |
| **Degraded** | partial data (all-zero buckets, incomplete pagination) | Renders normally with inline `<Badge variant="outline">partial data</Badge>` + tooltip explaining |

## Anti-patterns

- **Pie chart with > 5 slices.** Degrade to sorted horizontal bar.
- **Line chart with < 6 data points.** Use bars — lines imply continuity.
- **Stacked categories that aren't parts-of-whole.** If errors + warnings don't sum to total, don't stack.
- **Sparkline without a primary number.** Sparkline = KPI context, never standalone.
- **Dual-axis where scales compete for attention.** Prefer small-multiples (two charts side-by-side).
- **Widgets outside Cards.** Every widget wraps in shadcn `<Card>` (from `@/components/ui/card`).
- **Hardcoded hex colors.** Always tokens.
- **Generic empty state message.** "No data" is banned; always widget-specific.
