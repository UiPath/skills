# Build — mode impl

End-to-end workflow for Build mode. Dispatched from SKILL.md when the user's intent is scaffold-or-edit a dashboard. **Read this file only when Build is the chosen mode; never preload alongside `deploy/impl.md`.**

## Preamble (every Build invocation)

### Step 0 — Preflight
Read [../../primitives/auth-context.md](../../primitives/auth-context.md). Run `uip login status --output json`. Halt if not logged in.

### Step 1 — Classify invocation
Check `<cwd>/.uipath-dashboards/state.json`:
- Absent → **first-run Build** (go to [First-run branch](#first-run-branch))
- Present → **incremental Build** (go to [Incremental branch](#incremental-branch))

---

## First-run branch

Pipeline: `Scaffold → Configure → Generate → Preview`

### Scaffold
Delegate to [../../primitives/scaffold.md](../../primitives/scaffold.md). This:
1. Renders `assets/templates/scaffold/*.template` into `./<kebab-name>/`.
2. Runs `npm install`.
3. Runs `npx shadcn@latest init --defaults` (WILL overwrite `src/index.css` — we restore in step 6).
4. Runs `npx shadcn@latest add card badge table chart tooltip separator skeleton`.
5. Writes `.gitignore` (see scaffold.md for the exact list).
6. **RESTORES** `src/index.css` from our template (mandatory — shadcn's v4-style grayscale defaults break chart colors and Card styling if left in place).
7. Pins `tailwindcss: ^3.4.13` in devDependencies (prevents v4 upgrade conflict with our v3-style config).
8. Runs end-to-end sanity checks (chart-1 HSL value present, no leftover oklch, tailwindcss v3 installed, chart.tsx exists). Halts on any check failure — do NOT hand a broken CSS pipeline to the dev server.

### Configure
Delegate to [../../primitives/intent-capture.md](../../primitives/intent-capture.md). This:
1. Derives `app.name` / `routingName` as kebab-case from the prompt.
2. Reads `auth-context` for env / orgName / tenantName.
3. Fetches folder list via SDK, presents numbered picker, user selects → `folderKey`.
4. Writes initial `<project>/.uipath-dashboards/state.json` per [state-file.md](../../primitives/state-file.md).

### Generate
For each widget implied by the user's prompt:
1. **Route intent** per [../../primitives/data-router.md](../../primitives/data-router.md) → SDK call spec `{service, method, filter, fieldsProjected, scope, aggregation}`.
2. **Pick chart** per [../../primitives/chart-selector.md](../../primitives/chart-selector.md) → `{chartType, widgetTemplate, chartConfig, dataMapping}`.
3. **Render widget** — copy `assets/templates/widgets/<chartType>.tsx.template` → `<project>/src/dashboard/widgets/<PascalCaseName>.tsx` with substitutions for series names, colors, data-hook name.
4. **Render query hook** — write `<project>/src/lib/queries/<kebab-name>.ts` calling the routed SDK method.
5. **Compose `Dashboard.tsx`** per [../../aesthetic/layout-patterns.md](../../aesthetic/layout-patterns.md) — KPI row on top, primary chart next, secondaries in 2-up grid, tables last.
6. **Render auth wiring** — `<project>/src/lib/auth-strategy.ts` per [../../primitives/auth-strategy.md](../../primitives/auth-strategy.md).
7. **Render SECURITY.md** — warn about full-session-token scope per [../../primitives/security.md](../../primitives/security.md).

### Preview
Delegate to [../../primitives/dev-server.md](../../primitives/dev-server.md). This:
1. Prompts user for `VITE_UIPATH_PAT` → writes to `<project>/.env.local`.
2. Runs `npm run dev` in `<project>`.
3. Captures Vite's chosen port (auto-bumps from 5173 if busy).
4. Prints the localhost URL; leaves dev server in foreground.

---

## Incremental branch

Pipeline: `Read → Plan → Diff → Apply → Reload`

### Read
Load existing `<project>/src/dashboard/Dashboard.tsx`, every `<project>/src/dashboard/widgets/*.tsx`, every `<project>/src/lib/queries/*.ts`. Build an in-memory model of widgets + queries.

### Plan
Interpret the user's new prompt as **diffs** against the current dashboard:
- "add a chart of queue throughput" → ADD widget + query + insert into `Dashboard.tsx`.
- "change the error-rate threshold to 5%" → EDIT constant in error-rate widget.
- "remove the active-agents KPI" → DELETE widget file + remove import/JSX from `Dashboard.tsx` + remove orphaned query.

### Diff (Critical Rule 8)
For every file you plan to write:
1. Read current file content.
2. Compute diff.
3. If diff touches lines that appear user-edited (renamed variables, added comments, restructured layout, formatting changes), **stop and show the diff + ask for confirmation before writing**.

### Apply
Write approved edits. Recompute scope allowlist via [../../sdk/scope-map.md](../../sdk/scope-map.md); update `state.json.scopes` (informational in secret-mode).

### Reload
If `npm run dev` is already running, Vite HMR picks up changes. If not, instruct user to re-run.

---

## Narration

Narrate each stage back to the user as it runs. This is how "dashboards-as-code" feels alive:

```
✶ Building: "<prompt excerpt>"

→ Scaffolding Vite+React+shadcn/ui in ./<kebab>/ ... done
→ Configuring: env=<env>, org=<org>, tenant=<tenant>, folder=<folder>
→ Intent parsing:
    • <Widget 1 intent> → <chart type>
    • <Widget 2 intent> → <chart type>
    ...
→ Chart selection:
    • <Widget> → <template>
    ...
→ Generating:
    • src/dashboard/widgets/<File>.tsx
    ...
→ Paste your UiPath PAT into .env.local as VITE_UIPATH_PAT=... (see <env>.uipath.com/<org>/<tenant>/portal_/accessTokens)
→ Starting dev server ...
→ Dashboard preview: http://localhost:<port>/ — Ctrl+C to stop.
```

## Error paths

| Condition | Action |
|---|---|
| Not logged into `uip` | Halt at Step 0; instruct `uip login`. |
| Prompt too vague ("a dashboard") | Ask specifics (what data? what time window?) before scaffolding. |
| Data-router can't map intent to an SDK call | Ask user to rephrase; link to [../../sdk/intent-map.md](../../sdk/intent-map.md). |
| Folder list empty | Report permissions issue; do NOT write a broken state.json. |
| `npm install` fails | Surface stderr; suggest common fixes (`unset GH_NPM_REGISTRY_TOKEN`, Node version, etc.). |
| `shadcn init` fails | Surface stderr; halt — unfinished scaffold is worse than loud failure. |
| Port 5173 busy | Vite auto-bumps; report chosen port. |
| Hand-edited widget + rebuild change to it | Surface diff; ask confirmation before writing. |
