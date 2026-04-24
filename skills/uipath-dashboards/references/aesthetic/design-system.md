# Design system subset for dashboards

Opinionated subset of shadcn/ui + Tailwind we use in generated dashboards. This is NOT a shadcn/ui reference (see https://ui.shadcn.com/docs for that) — it's what the generator picks FROM shadcn, and why.

## Components IN (the dashboards kit)

Installed on first scaffold via `npx shadcn@latest add --yes`:

| Component | Purpose |
|---|---|
| `Card` (+ `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`) | Every widget wraps in a Card. The primitive. |
| `Badge` (default / secondary / destructive / outline) | Only for status labels inside tables; **prefer `DeltaBadge` for deltas and `SeverityBadge` for severity**. |
| `Table` (+ `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`) | Ranked-table widget |
| `Chart` (shadcn's Recharts wrapper — `ChartContainer`, `ChartTooltip`, `ChartLegend`) | Every chart widget |
| `Tooltip` (+ `TooltipProvider`, `TooltipContent`, `TooltipTrigger`) | Inline hover help |
| `Separator` | Visual dividers between layout sections |
| `Skeleton` | Loading state placeholders |
| `Button` (ghost / outline / icon variants) | Refresh, ThemeToggle, Customize. No primary buttons (dashboards are read-only) |

### Chrome primitives (skill-owned, live in `src/dashboard/chrome/`)

These wrap shadcn + lucide into dashboard-specific affordances. Every widget composes them rather than rolling its own.

| Primitive | Purpose | Canonical usage |
|---|---|---|
| `DeltaBadge` | Semantic delta pill with arrow + text. Direction conveys *good vs bad*, not just sign. | `<DeltaBadge direction="up-good" text="+8% vs yesterday" />` |
| `SeverityBadge` | Colored pill for severity / status in tables. | `<SeverityBadge severity="high" />` |
| `ViewAllLink` | Standard drill-down link (`View all →`). Required on chart + table cards. | `<ViewAllLink href="#invocation-volume" />` |
| `InfoTooltip` | ⓘ icon with tooltip. Use when the metric needs explanation. | `<InfoTooltip message="Percentage points — not to be confused with percent." />` |
| `ThemeToggle` | Mandatory in Header. Sun / Moon icon button. | `<ThemeToggle />` |
| `Header` | Title + description + right-side action cluster. | `<Header title="Agent Health" description="..." />` |
| `EmptyState`, `ErrorBoundary`, `LoadingState` | Widget state primitives. | Rendered by each widget when data is unavailable. |

## Icon catalog (lucide-react)

Every KPI gets an icon. Every chart/table icon is optional but encouraged. The generator picks from this intent-map; if no clear match, omit the icon rather than force a wrong one.

| Intent / metric | lucide-react icon | Import |
|---|---|---|
| Active agents / running count | `Briefcase` | `import { Briefcase } from 'lucide-react'` |
| Invocations / throughput / calls | `Zap` | — |
| Response time / latency / duration | `Clock` | — |
| Error rate / faults / failures | `AlertTriangle` | — |
| Cost / spend / budget | `DollarSign` | — |
| Target / budget line / goal | `Target` | — |
| Compliance / policy pass rate | `Shield` | — |
| Active policies / rule sets | `ClipboardList` | — |
| Open violations / alerts | `AlertCircle` | — |
| Pending review / backlog | `AlertOctagon` | — |
| Tasks / actions / assignments | `CheckSquare` | — |
| Queues / workflow items | `LineChart` / `ListOrdered` | — |
| Users / assignees / principals | `Users` | — |
| Models / ML configurations | `Cpu` | — |
| Buckets / files / storage | `Database` | — |
| Cases / pipeline stages | `FolderOpen` | — |
| Trend up (when metric is a trend KPI) | `TrendingUp` / `TrendingDown` | — |
| Bar chart / distribution | `BarChart3` | — |

Icons render in a `rounded-md bg-muted p-2` square with `w-4 h-4 text-muted-foreground` — muted, never color-tinted to the metric's palette.

## Components OUT (skip in v1)

Reaching for any of these = feature creep:

- `Dialog`, `Sheet`, `Popover`, `Command`, `DropdownMenu` — interactive surfaces not needed for read-only dashboards
- `Form`, `Input`, `Textarea`, `Select`, `Checkbox`, `RadioGroup` — no forms
- `Accordion`, `Tabs`, `Collapsible` — dashboards should fit on one scroll plane; tabs hide data

If a user request genuinely needs one of these, it's probably the wrong shape for the skill — redirect.

## Tailwind token extensions

`tailwind.config.ts.template` extends shadcn's defaults with five chart color CSS variables:

```ts
extend: {
  colors: {
    chart: {
      1: 'hsl(var(--chart-1))',
      2: 'hsl(var(--chart-2))',
      3: 'hsl(var(--chart-3))',
      4: 'hsl(var(--chart-4))',
      5: 'hsl(var(--chart-5))',
    }
  }
}
```

In `index.css.template`, the CSS variables:
```css
:root {
  --chart-1: 221 83% 53%;   /* blue — primary */
  --chart-2: 212 95% 68%;   /* lighter blue — secondary */
  --chart-3: 142 76% 36%;   /* emerald — success */
  --chart-4: 38 92% 50%;    /* amber — warning */
  --chart-5: 0 84% 60%;     /* red — error */
}
.dark {
  --chart-1: 217 91% 60%;
  --chart-2: 213 94% 68%;
  --chart-3: 142 71% 45%;
  --chart-4: 35 91% 62%;
  --chart-5: 0 91% 71%;
}
```

## Color rules

- **Success / positive delta / "up is good":** `chart-3` (emerald)
- **Error / destructive / "down is good":** `chart-5` (red)
- **Warning / mid-risk (2–10% error, SLA nearing):** `chart-4` (amber)
- **Primary data series:** `chart-1` (blue)
- **Secondary data series:** `chart-2`
- **Never hardcoded hex** — always `hsl(var(--chart-N))`. Hex breaks dark mode; tokens don't.

## Typography + spacing defaults

- Page padding: `p-8` at `lg`, `p-4` at `sm`.
- Card padding: `p-6`.
- Grid gutters: `gap-6` (24px). Uniform; no per-card overrides.
- Headings: `Card.CardTitle` uses shadcn default (`text-lg font-semibold`).
- Numbers: `tabular-nums` for all numeric columns / KPI values.

## Light + dark mode

**Default is light mode.** Users opt in to dark via a toggle in the Header. Every widget template ships `dark:` Tailwind variants so both modes are first-class.

### Mechanics

- `<html>` starts with **no class** in `index.html.template`. An inline `<script>` in the `<head>` reads `localStorage["uipath-dashboard-theme"]` and adds `class="dark"` BEFORE React mounts (prevents flash-of-unthemed-content).
- The toggle lives in `src/dashboard/chrome/ThemeToggle.tsx` — a `<Button variant="outline" size="icon">` with a `<Moon>` icon in light mode (click → go dark) and `<Sun>` icon in dark mode (click → go light).
- State persists in `localStorage["uipath-dashboard-theme"] = 'light' | 'dark'`.
- Logic lives in `src/lib/theme.ts` — `getStoredTheme()` and `setTheme(theme)` helpers.
- Header wires the toggle into a `flex items-center gap-2` cluster alongside Refresh.

### Rules the generator follows

1. **Never hardcode `class="dark"` on `<html>`.** The inline script owns that class.
2. **Always include `<ThemeToggle />` in the Header cluster** — not optional. A dashboard without a theme toggle breaks the "dashboards as code" contract.
3. **No `prefers-color-scheme` auto-detection in v1.** Users pick; we honor. Auto-detect can land in v2 as a 3-state option (light/dark/system).
4. **When the Apps host later dictates theme via postMessage (v2),** the host message will call `setTheme()` — no rewrite of the toggle needed; it becomes one more input to the same state.
