# Design system for dashboards

Generated dashboards use **shadcn/ui** components on top of Tailwind, themed with an explicit **UiPath-flavored palette** declared in `src/index.css`. Poppins (UiPath's product font) is loaded via `<link>` tags in `index.html` from Google Fonts. No third-party design-system stylesheet at runtime — keeps the cascade simple and deterministic.

## How the visual identity composes

1. **Poppins font** loaded by `<link>` tags in `index.html` (Google Fonts CDN with `preconnect` for fast first paint).
2. **Explicit shadcn HSL palette** in `src/index.css`'s `@layer base { :root { ... } }` block. Every shadcn variable (`--background`, `--foreground`, `--card`, `--primary`, `--muted`, `--border`, `--destructive`, …) is declared with a UiPath-flavored HSL value:
   - `--primary: 14 96% 53%` (UiPath orange `#FA4616`)
   - `--chart-2: 213 100% 44%` (UiPath blue)
   - Neutrals tuned to match Apps/Orchestrator/StudioWeb
3. **Dark-mode block** activates on either `.dark` or `body.dark` selector.
4. **shadcn components** import from `@/components/ui/*` — `Card`, `Button`, `Badge`, `Table`, `Chart`, `Separator`, `Skeleton`. They consume the variables above via Tailwind utilities (`bg-card`, `text-muted-foreground`, etc.) and inherit their UiPath-flavored values automatically.

The win of writing the palette ourselves: dashboards are deterministic across SDK and component-library upgrades, with zero cascade fights from imported design-system stylesheets.

## Components IN (the dashboards kit)

Installed on first scaffold via `npx shadcn@latest add --yes`:

| Component | Purpose |
|---|---|
| `Card` (+ `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`) | Every widget wraps in a Card. The primitive. |
| `Badge` (default / secondary / destructive / outline) | Status labels inside tables; **prefer `DeltaBadge` for deltas, `SeverityBadge` for severity, `StateBadge` for service-mapped state fields**. |
| `Table` (+ `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`) | Ranked-table widget |
| `Chart` (shadcn's Recharts wrapper — `ChartContainer`, `ChartTooltip`, `ChartLegend`) | Every chart widget |
| `Separator` | Visual dividers between layout sections |
| `Skeleton` | Loading state placeholders |
| `Button` (outline / icon variants) | Refresh, optional Customize. No primary buttons (dashboards are read-only). |

### Chrome primitives (skill-owned, live in `src/dashboard/chrome/`)

These wrap shadcn + lucide into dashboard-specific affordances. Every widget composes them rather than rolling its own.

| Primitive | Purpose | Canonical usage |
|---|---|---|
| `DeltaBadge` | Semantic delta pill with arrow + text. Direction conveys *good vs bad*, not just sign. | `<DeltaBadge direction="up-good" text="+8% vs yesterday" />` |
| `SeverityBadge` | Colored pill for severity / status in tables. | `<SeverityBadge severity="high" />` |
| `StateBadge` | Service-aware state pill for Job/Task/Case/etc. fields — applied automatically by detail views per [../sdk/service-semantics.md § Semantic column renderers](../sdk/service-semantics.md). | `<StateBadge service="Jobs" value={row.state} />` |
| `ViewAllLink` | Standard drill-down link (`View all →`). Required on chart + table cards. | `<ViewAllLink to="/active-agents" />` |
| `InfoTooltip` | ⓘ icon with tooltip (CSS-only Tailwind hover/focus pattern). | `<InfoTooltip message="Percentage points — not to be confused with percent." />` |
| `Header` | Title + description + optional Refresh button. No theme toggle (light mode only). | `<Header title="Agent Health" description="..." />` |
| `RecordsTable` | Detail-view table with sort, click-to-row, semantic column alignment. Auto-applies `StateBadge` etc. for known field names per service-semantics.md. | `<RecordsTable rows={...} columns={[...]} />` |
| `WidgetBoundary` | Per-widget error boundary. Wrap every widget in `Dashboard.tsx`. | `<WidgetBoundary label="Active agents">…</WidgetBoundary>` |
| `EmptyState`, `ErrorBoundary`, `LoadingState` | Widget state primitives. | Rendered by each widget when data is unavailable. |

## Icon catalog (lucide-react)

Every KPI gets an icon. Every chart/table icon is optional but encouraged. The generator picks from this intent-map; if no clear match, omit the icon rather than force a wrong one.

| Intent / metric | lucide-react icon |
|---|---|
| Active agents / running count | `Briefcase` |
| Invocations / throughput / calls | `Zap` |
| Response time / latency / duration | `Clock` |
| Error rate / faults / failures | `AlertTriangle` |
| Cost / spend / budget | `DollarSign` |
| Target / budget line / goal | `Target` |
| Compliance / policy pass rate | `Shield` |
| Active policies / rule sets | `ClipboardList` |
| Open violations / alerts | `AlertCircle` |
| Pending review / backlog | `AlertOctagon` |
| Tasks / actions / assignments | `CheckSquare` |
| Queues / workflow items | `LineChart` / `ListOrdered` |
| Users / assignees / principals | `Users` |
| Models / ML configurations | `Cpu` |
| Buckets / files / storage | `Database` |
| Cases / pipeline stages | `FolderOpen` |
| Trend up (when metric is a trend KPI) | `TrendingUp` / `TrendingDown` |
| Bar chart / distribution | `BarChart3` |

Icons render in a `rounded-md bg-muted p-2` square with `w-4 h-4 text-muted-foreground` — muted, never color-tinted to the metric's palette.

## Components OUT (skip in v1)

Reaching for any of these = feature creep:

- `Dialog`, `Sheet`, `Popover`, `Command`, `DropdownMenu` — interactive surfaces not needed for read-only dashboards
- `Form`, `Input`, `Textarea`, `Select`, `Checkbox`, `RadioGroup` — no forms (the auto-refresh interval picker is the canonical anti-example: shipped as default, removed because dashboards are not ops-room TVs)
- `Accordion`, `Tabs`, `Collapsible` — dashboards should fit on one scroll plane; tabs hide data

If a user request genuinely needs one of these, it's probably the wrong shape for the skill — redirect.

## Tailwind token wiring

`tailwind.config.ts.template` declares the standard utility-class color mapping:

```ts
colors: {
  border: 'hsl(var(--border))',
  background: 'hsl(var(--background))',
  foreground: 'hsl(var(--foreground))',
  primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
  card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
  muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
  destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
  // ...
  chart: {
    1: 'hsl(var(--chart-1))',  // UiPath orange
    2: 'hsl(var(--chart-2))',  // UiPath blue
    3: 'hsl(var(--chart-3))',  // success green
    4: 'hsl(var(--chart-4))',  // amber warning
    5: 'hsl(var(--chart-5))',  // red error
  },
}
```

Variables are declared in `index.css` as bare HSL tuples — Tailwind's alpha-modifier syntax works (`bg-chart-3/10`, `text-destructive/40`).

## Color rules

- **Primary brand / "main thing":** `chart-1` or `primary` — UiPath orange `#FA4616`.
- **Success / positive delta / "up is good":** `chart-3` (success green).
- **Error / destructive / "down is good":** `chart-5` or `destructive` (red).
- **Warning / mid-risk (2–10% error, SLA nearing):** `chart-4` (amber).
- **Secondary data series:** `chart-2` (UiPath blue).
- **Never hardcoded hex** — always `hsl(var(--chart-N))` tokens. Hex breaks dark mode; tokens don't.

## Typography + spacing defaults

- **Font: Poppins** — loaded via `<link>` in `index.html` (Google Fonts CDN), with `system-ui` fallback. UiPath products use Poppins everywhere; matching it is the single biggest "feels like UiPath" win.
- Page padding: `p-8` at `lg`, `p-4` at `sm`.
- Card padding: `p-6` (shadcn default).
- Grid gutters: `gap-6` (24px). Uniform; no per-card overrides.
- Headings: shadcn's `CardTitle` default (`text-lg font-semibold`).
- Numbers: `tabular-nums` for all numeric columns / KPI values.

## Light mode only (no theme toggle in v1)

Dashboards ship in **light mode** with no user-facing theme switcher. `<body>` is rendered with `class="light"` and stays there for the session. There is no `ThemeToggle` component in chrome, no `theme.ts` helper, no body-class-swapping script in `index.html`.

### Why no toggle

Theme toggles add UI surface area, persistence logic, and accessibility concerns (keyboard shortcuts, contrast pairing) for a feature most dashboard users don't reach for. Keeping light mode hardcoded in v1 reduces the surface to maintain and removes a control nobody asked for.

### Dormant dark-mode infrastructure

The dark-mode CSS variables are still declared in `index.css` under `.dark, body.dark` selectors. They're inert — no element gets those classes by default — but they remain in place so that:

1. A future revision can re-introduce a toggle by re-adding `ThemeToggle.tsx` + `theme.ts` and changing `<body class="light">` to a dynamic class.
2. The Apps host (v2+) could dictate dark mode by adding `class="dark"` to the body via postMessage with no CSS changes required.

### Rules the generator follows

1. **No `ThemeToggle` import or use.** Header chrome no longer ships one.
2. **No `prefers-color-scheme` auto-detection.** Light is the deterministic choice.
3. **No auto-refresh.** Dashboards are triage pages, not ops-room TVs. The Header carries a manual Refresh button only; auto-refresh interval pickers are explicitly excluded.
4. **Body class stays `light` forever** unless future host integration changes it.
