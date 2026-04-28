# Widget anatomy

**The canonical structure every generated widget must follow.** If a widget is missing one of these affordances, the generator is producing "basic output" — which the skill explicitly does not ship.

## The six required parts

Every widget on the dashboard MUST include:

```
┌─────────────────────────────────────────────────────────┐
│  ┌──┐                                  ┌──┐  View all → │  ← (1) icon, (2) title+description,
│  │🡕 │  Invocation volume               │ⓘ │             │      (5) info-tooltip, (6) view-all
│  └──┘  Agent calls — last 24 hours                       │
│                                                          │
│  2,847  ↗ +8% vs yesterday                               │  ← (3) inline headline + delta
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                                                  │   │
│  │             ▓▓▓  ▓▓▓  ▓▓▓                       │   │
│  │        ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓                  │   │
│  │   ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓             │   │  ← (4) body (the chart / table / KPI)
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

| # | Part | Required? | Lives in |
|---|---|---|---|
| 1 | **Icon** | Required for KPIs, optional for charts/tables | `CardHeader` left-side, small muted square |
| 2 | **Title + description** | Required | `CardTitle` + `CardDescription` |
| 3 | **Inline headline + DeltaBadge** | Required for metric-backed widgets (KPIs, most charts) | Between `CardHeader` and chart body |
| 4 | **Body** | Required | `CardContent` — the chart, table, or main number |
| 5 | **InfoTooltip** | Optional; required when the metric's meaning isn't self-evident | `CardHeader` right-side |
| 6 | **ViewAllLink** | Required for charts and tables; not needed on pure KPIs | `CardHeader` right-side |

## Component mapping

All six parts are rendered via chrome primitives in `src/dashboard/chrome/`:

| Part | Component |
|---|---|
| Icon | Any lucide-react icon (see `aesthetic/design-system.md § Icon catalog`) |
| Title | shadcn `CardTitle` (from `@/components/ui/card`) |
| Description | shadcn `CardDescription` |
| Headline + delta | `DeltaBadge` next to a large number |
| Body | chart (Recharts via shadcn's `ChartContainer` at `@/components/ui/chart`) / shadcn `Table` / plain text |
| InfoTooltip | `InfoTooltip` (CSS-only Tailwind hover/focus-within pattern + `Info` icon) |
| ViewAllLink | `ViewAllLink` |

## Canonical JSX skeleton

Every chart widget renders this structure. KPI widgets collapse steps 3+4 into a single large-number display.

```tsx
<Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(detailHref)}>
  <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
    <div className="flex items-start gap-3">
      <div className="rounded-md bg-muted p-2">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </div>
    </div>
    <div className="flex items-center gap-2">
      {infoMessage && <InfoTooltip message={infoMessage} />}
      <ViewAllLink href={detailHref} />
    </div>
  </CardHeader>

  {/* Inline headline + delta — above chart body */}
  <div className="px-6 pb-2 flex items-baseline gap-3">
    <span className="text-3xl font-semibold tabular-nums">{fmtNumber(headline)}</span>
    <DeltaBadge direction="up-good" text="+8% vs yesterday" />
  </div>

  <CardContent>
    {/* chart / table / KPI body */}
  </CardContent>
</Card>
```

## Rules

1. **Every widget gets a description.** If the generator can't derive one from the intent, halt and ask the user. Never ship a widget with just a title.
2. **Every chart and table gets a `ViewAllLink` that routes to a real detail view.** `href="/<kebab-slug>"` (HashRouter). A matching `src/dashboard/views/<WidgetName>View.tsx` MUST exist alongside the widget and render the widget's underlying records without aggregation. Placeholder hashes with nothing at the other end are banned — see [detail-views.md](detail-views.md).
3. **Delta badges use semantic direction**, not signed values. Use `up-good` / `up-bad` / `down-good` / `down-bad` / `neutral` / `status` — the direction tells the reader whether the change is good, not just which way it's pointing.
4. **InfoTooltip when the metric needs explanation.** "Error rate trend" doesn't need one; "PP vs %" (percentage points vs percent) usually does.
5. **KPIs with deltas never show sign alone.** Always pair with period context — "+3 this week", "+8% vs yesterday", "-0.6pp this week", "On track".
6. **Cards are clickable when they have detail views.** Use `cursor-pointer` + `hover:shadow-md` + click handler. Non-clickable cards (pure KPIs without drill-down) omit both.
7. **Consistent header padding.** `CardHeader` uses `pb-2` to tighten the gap to the headline row; headline row uses `px-6 pb-2`; `CardContent` uses its default `pt-0` when a headline row is present.
8. **Icons tint.** Icons ride in a `rounded-md bg-muted p-2` square with `w-4 h-4 text-muted-foreground`. Never color-tint the icon to the metric's color — that conflicts with the DeltaBadge's semantic color.

## Anti-patterns

- **Widget with only title, no description.** Banned.
- **KPI with `+8%` and no period context.** Banned — use DeltaBadge with `text="+8% vs yesterday"`.
- **Chart card with no inline headline.** The chart alone doesn't tell the "at a glance" story — the headline does.
- **ViewAllLink pointing at a placeholder hash.** Banned — must navigate to a real detail view with the widget's unaggregated data. See [detail-views.md](detail-views.md).
- **Using shadcn `Badge` directly for deltas.** Use `DeltaBadge` — it has semantic direction (up-good vs up-bad vs neutral).
- **Icon in the title text itself** (e.g., `title="📊 Volume"`). Icons live in the icon slot, not in the string.
- **More than one action in the header right cluster.** Keep to: InfoTooltip + ViewAllLink, max.
