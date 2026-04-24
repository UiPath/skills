# Layout patterns for dashboards

Rules the generator follows when composing `Dashboard.tsx`. These encode "beautiful and informative" as reproducible code patterns.

## 10 rules

1. **KPI row at top.** 1–4 tiles, equal-width: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6`. NEVER more than 4 KPIs; if more are wanted, promote overflow into a ranked-table below.
2. **Primary chart full-width next.** The headline trend the prompt implied. `className="w-full"`.
3. **Secondary charts in 2-up grid.** `grid-cols-1 lg:grid-cols-2 gap-6`. Max 4 tiles in this grid; further widgets wrap to a third row.
4. **Tables last.** Densest content; bottom placement.
5. **Gutters uniform.** `gap-6` (24px). Card padding `p-6`. Page padding `p-8` lg / `p-4` sm. No per-card tuning.
6. **Every widget in a Card.** No free-floating JSX.
7. **`chrome/Header.tsx` at top** — humanized `state.app.name` + last-refreshed timestamp + a right-side cluster containing `<ThemeToggle />` and (optionally) a Refresh button, both in a `flex items-center gap-2` wrapper.
8. **Light mode default, dark mode toggleable.** `<html>` starts with no class; an inline script in `index.html` applies `.dark` if `localStorage["uipath-dashboard-theme"] === 'dark'` BEFORE React mounts. The `<ThemeToggle>` (Sun / Moon icon button) lives in the Header and is MANDATORY — not optional. Every widget template uses `dark:` Tailwind variants so both modes look correct. Never hardcode `class="dark"` on `<html>`. See [design-system.md § Light + dark mode](design-system.md).
9. **Density "comfortable".** Table rows `py-3` not `py-1`. Breathing room matters more than density on first load.
10. **No auto-generated dashboard title.** Humanize `state.app.name` (`agent-health-dashboard` → `Agent Health Dashboard`). Widget titles come from user intent, not SDK method name.

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
      <Header title="Agent Health Dashboard" />

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
        <ActiveAgentsKPI sdk={sdk} />
        <InvocationsTodayKPI sdk={sdk} />
        <AvgResponseTimeKPI sdk={sdk} />
        <ErrorRateKPI sdk={sdk} />
      </div>

      {/* Primary chart */}
      <div className="mt-6">
        <InvocationVolume sdk={sdk} />
      </div>

      {/* 2-up grid for secondaries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <ErrorRateTrend sdk={sdk} />
        <TopAgentsTable sdk={sdk} />
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
- **Widgets outside Cards.** Every widget wraps in shadcn `<Card>`.
- **Hardcoded hex colors.** Always tokens.
- **Generic empty state message.** "No data" is banned; always widget-specific.
