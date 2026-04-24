# Design system subset for dashboards

Opinionated subset of shadcn/ui + Tailwind we use in generated dashboards. This is NOT a shadcn/ui reference (see https://ui.shadcn.com/docs for that) — it's what the generator picks FROM shadcn, and why.

## Components IN (the dashboards kit)

Installed on first scaffold via `npx shadcn@latest add --yes`:

| Component | Purpose |
|---|---|
| `Card` (+ `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`) | Every widget wraps in a Card. The primitive. |
| `Badge` (default / secondary / destructive / outline) | Delta indicators on KPIs; tone badges on cells |
| `Table` (+ `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`) | Ranked-table widget |
| `Chart` (shadcn's Recharts wrapper — `ChartContainer`, `ChartTooltip`, `ChartLegend`) | Every chart widget |
| `Tooltip` (+ `TooltipProvider`, `TooltipContent`, `TooltipTrigger`) | Inline hover help |
| `Separator` | Visual dividers between layout sections |
| `Skeleton` | Loading state placeholders |
| `Button` (ghost / outline variants only) | Refresh button in Header; no primary buttons (dashboards are read-only) |

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
