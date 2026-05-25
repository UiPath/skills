# Dashboard Build Plugin

Full pipeline: NLP prompt → plan approval → scaffold → widgets → validate → preview.

## Tool-Use Budget
≤ 12 tool calls for a 6-widget dashboard. Never exceed 18 total.

| Phase | Calls | How |
|---|---|---|
| 0 Incremental check | 1 Bash | `ls .dashboard/state.json` |
| 1 Boot | 1 block | 4 reads issued simultaneously |
| 2 Preflight | 1 Bash | `uip login status` |
| 3–5 Derive + Plan + Approve | 0 | In-context, no tools |
| 3.5 Pre-warm | 1 Bash | scaffold copy + npm ci in background (silent, during plan review) |
| 6 Configure | 1 Bash | check pre-warm status + write .env.local + routing name (~2-5s) |
| 7 Widgets (≤5 widgets) | 1 Bash | Single Node.js heredoc |
| 7 Widgets (6+ widgets) | 2 Bash | Split: widgets + views in separate calls |
| 8 Validate pass 1 | 1 Bash | `tsc --noEmit` |
| 8 Validate pass 2 (if errors) | 1 Bash | Fix + re-run `tsc --noEmit` |
| 8 Dev server | 1 Bash | `npm run dev -- --open` |
| **Total** | **≤ 10–12** | |

## Execution Rules — Non-negotiable

1. **Never spawn subagents.** Do not use `TaskCreate`, `Agent`, or any dispatching tool. Every phase executes in this session.
2. **Never read scaffold source files during Phase 7.** Their APIs are fully documented in this file — reading them wastes a round-trip.
   **Explicitly forbidden (by filename):** `App.tsx`, `package.json`, `vite.config.ts`, `tsconfig.json`, any file under `src/dashboard/chrome/`, any file under `src/components/`, `useInsights.ts`, `insights-client.ts`, `useAuth.ts`.
3. **Never read widget template files.** Use Widget Recipes from `insights-catalog.md` directly.

## Narration Rules — What Users See

This skill serves end users, not developers. They must never see code, file paths, CLI output, or build process details.

### The Blackout Rule

**From the moment the user approves the plan until the final summary, produce ZERO text output.**

No intermediate messages. No "I'm generating widgets now." No "Running tsc." No "Almost done." Nothing.
The user sees only tool call blocks (collapsed by default in Claude Code). That is acceptable.

The only two text outputs in the entire build flow are:

| Moment | Output |
|---|---|
| After Phase 5 (user approves the plan) | One line: `⚙ Building your dashboard…` |
| After tsc passes (Phase 8) | The final summary — see Summary Format below |

Everything in between — Phases 6, 7, 8 validation — is **complete silence on text output**.

> Note: Phase 3.5 (pre-warm) runs BEFORE the plan is shown — npm ci is already in progress
> while the user reads the plan. By approval time it's done. Never mention this to the user.

### Error exceptions (only if unrecoverable)

- tsc fails after 2 fix attempts: `"There was a configuration issue — please run npm install in the project folder and try again."`
- npm ci fails: `"Dependencies are downloading — this may take a minute on first run."` then retry silently.

### After summary

Show summary first (see Summary Format below), then run `npm run dev -- --open`.
The browser opens automatically. Server runs in foreground with HMR.

### Banned phrases (never say these)

`writing files` · `generating code` · `running tsc` · `phase 6` · `scaffold` · `package.json` · `useInsights` · `node_modules` · `npm ci` · `widget files` · `TypeScript` · `heredoc` · `bash` · `building` (except the one allowed line above)

## Phase 0 — Incremental check (1 Bash, before anything else)

Before loading any primitives, check whether this is an edit of an existing dashboard:

```bash
ls .dashboard/state.json 2>/dev/null && echo "INCREMENTAL" || echo "FRESH"
```

**If INCREMENTAL** → Read `../../primitives/incremental-editor.md` and follow that flow instead of this pipeline. Do not continue below.

**If FRESH** → Continue to Phase 1.

## Phase 1 — Boot (**MANDATORY: one parallel block, all 4 reads simultaneously**)

> **This is the single biggest performance lever in the pipeline.**
> Reading files sequentially costs ~8s per file in API round-trips (32s+ total).
> Issuing all 4 in one parallel block costs ~5s total — a 6× speedup.
>
> **Rule:** Issue exactly ONE message containing all four Read tool calls at the same time,
> with NO text output before they complete. Do not read them one at a time.

Issue **EXACTLY** these four Read calls in a **SINGLE** message. All four in one tool-call block — do not send until all four are listed:

☐ 1. `../../primitives/auth-context.md`
☐ 2. `../../primitives/build-plan.md`
☐ 3. `../../primitives/data-router.md`
☐ 4. `../../insights-catalog.md`

**DO NOT send the message until all 4 paths are in the same tool-call block.**
Missing even one causes a sequential read which wastes ~8s per file.

## Phase 2 — Preflight (1 Bash)
```bash
uip login status --output json
```
Check `Data.Status == "Logged in"`. If not → stop, tell user to run `uip login`.

Extract from response (fields are under `Data.`, not top-level):
- `Data.Organization` → ORG
- `Data.Tenant` → TENANT
- `Data.BaseUrl` → DATA_BASE_URL (e.g. `https://alpha.uipath.com`)

**No `tenantId` in this output.** Read PAT and TENANT_ID from `~/.uipath/.auth`
as described in `../../primitives/auth-context.md` Steps 3–4.

## Phase 3 — Metric Derivation (0 tool calls)
For each metric in the NLP prompt, derive using build-plan.md four-axis decomposition:
- Shape, time frame, aggregation, service (SDK or Insights)
- Route each metric using data-router.md routing table

## Phase 3.5 — Pre-warm scaffold in background (1 Bash, silent)

> **This is how we cut the perceived wait time to near-zero.**
> Start copying the scaffold and running `npm ci` RIGHT NOW, while the user reads the plan.
> npm ci with the lockfile takes 16–25s from cache — it's done before the user even responds.
> Do NOT mention this to the user. Show no output. Proceed immediately to Phase 4.

```bash
SKILL_BASE_DIR="<SKILL_BASE_DIR>"   # from your system context ("Base directory for this skill")
DASHBOARD_SLUG=$(node -e "
  const t='<DASHBOARD_NAME>';
  console.log(t.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-\$)/g,''));
")
PROJECT_DIR="$(pwd)/${DASHBOARD_SLUG}"
# Use project-relative paths — /tmp is not reliably shared between shells on Windows
mkdir -p "${PROJECT_DIR}/.dashboard"
STATUS_FILE="${PROJECT_DIR}/.dashboard/.prewarm-status"
DIR_FILE="${PROJECT_DIR}/.dashboard/.prewarm-dir"

# Background: copy scaffold + install deps (silent)
(
  rm -f "${STATUS_FILE}"
  cp -r "${SKILL_BASE_DIR}/assets/templates/dashboard/scaffold/." "${PROJECT_DIR}/" && \
  node -e "require('fs').rmSync('${PROJECT_DIR}/node_modules',{recursive:true,force:true})" 2>/dev/null || true
  cd "${PROJECT_DIR}" && (npm ci --prefer-offline 2>/dev/null || npm ci 2>/dev/null)
  echo $? > "${STATUS_FILE}"
) &
echo "${PROJECT_DIR}" > "${DIR_FILE}"
echo "PREWARM_STARTED"
```

Remember `PROJECT_DIR` — use it in Phase 6 and beyond.

## Phase 4 — Plan (0 tool calls)
Render the plan using the format in build-plan.md (the grouped bullet format with plain-English descriptions).

**Do NOT show in the plan:**
- `[Insights]` / `[SDK]` labels
- API method names (`getAgents`, `getSummaryV2`, etc.)
- Chart type labels ("KPI card", "area chart")
- Any technical implementation detail

**Do show:**
- Widget name + time range
- One sentence per widget: what it shows + why it matters to the user
- Theme groupings when there are 4+ widgets (Overview / Trends / Detail / etc.)
- A "What you can do" block with 3–4 example edits

Do NOT write any files yet.

## Phase 5 — Approval Gate (0 tool calls)
HALT. Wait for user response.
Follow approval gate rules in build-plan.md exactly.
Do not proceed until explicit approval is received.

## Phase 6 — Configure (1 Bash — writes .env.local, confirms deps ready)

Pre-warm started in Phase 3.5. This phase just reads auth, writes env vars, and confirms
npm ci finished. If still running (rare — user responded very fast), waits briefly.

```bash
# Re-derive slug to find the status file
DASHBOARD_SLUG=$(node -e "
  const t='<DASHBOARD_NAME>';
  console.log(t.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-\$)/g,''));
")
PROJECT_DIR="$(pwd)/${DASHBOARD_SLUG}"
STATUS_FILE="${PROJECT_DIR}/.dashboard/.prewarm-status"

# Read auth
PAT=$(grep -m1 '^UIPATH_ACCESS_TOKEN=' ~/.uipath/.auth | cut -d'=' -f2-)
TENANT_ID=$(grep -m1 '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
if [ -z "$PAT" ]; then
  PAT=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_ACCESS_TOKEN||a.access_token||'')" 2>/dev/null)
  TENANT_ID=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_TENANT_ID||a.tenantId||'')" 2>/dev/null)
fi

# Derive API base URL
if echo "$DATA_BASE_URL" | grep -q "alpha";    then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi

# Primary signal: node_modules/.package-lock.json exists when npm ci finishes successfully
# This is more reliable than /tmp status files which fail across Windows shells
if [ ! -f "${PROJECT_DIR}/node_modules/.package-lock.json" ]; then
  # Pre-warm not done yet — wait up to 60s, then run synchronously if still not ready
  WAITED=0
  while [ ! -f "${PROJECT_DIR}/node_modules/.package-lock.json" ] && [ $WAITED -lt 12 ]; do
    sleep 5
    WAITED=$((WAITED+1))
  done
  if [ ! -f "${PROJECT_DIR}/node_modules/.package-lock.json" ]; then
    cd "${PROJECT_DIR}" && npm ci --prefer-offline 2>/dev/null || npm ci 2>/dev/null
  fi
fi

# Write env config
cd "${PROJECT_DIR}"
cat > .env.local << EOF
VITE_UIPATH_CLOUD_URL=${DATA_BASE_URL}
VITE_UIPATH_BASE_URL=${API_BASE_URL}
VITE_UIPATH_ORG_NAME=<ORG_NAME>
VITE_UIPATH_TENANT_NAME=<TENANT_NAME>
VITE_INSIGHTS_TENANT_ID=${TENANT_ID}
VITE_UIPATH_PAT=${PAT}
EOF

# Derive routing name
ROUTING_NAME=$(node -e "
  const name = '<DASHBOARD_NAME>'.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-\$)/g, '');
  const suffix = Math.random().toString(36).slice(2, 6);
  console.log(name + '-' + suffix);
")
```

No client ID, no scope, no OAuth setup required. The PAT comes from the active `uip login` session.
For production deployment the PAT is stripped before build (failBuildIfPatSet Vite plugin enforces this).

> **Expected Phase 6 time:** ~2–5s (deps already installed by pre-warm, just writing env vars)

## Phase 7 — Widget Generation (1 Bash call, **zero Write calls, zero template reads**)

> **Use Bash + Node.js heredoc to write all files at once.** Single Bash call keeps
> the user's session clean — no code previews. Do NOT use the Write tool for widget files.
> Do NOT read widget template files.

### Files to generate per widget (N widgets → 4N + 2 files total)

For each widget in the approved plan, generate:

| File | Purpose |
|---|---|
| `src/dashboard/widgets/<Name>.tsx` | Widget card with 6-part anatomy (icon, title, desc, headline, delta, chart, ViewAllLink) |
| `src/dashboard/views/<Name>View.tsx` | Detail view with DetailViewShell + RecordsTable |

Plus two shared files (always written once):
| File | Purpose |
|---|---|
| `src/dashboard/Dashboard.tsx` | Composes all widgets with proper layout (KPI row / chart row / table row) |
| `src/dashboard/widgets/index.ts` | Barrel export of all widget components |

**App.tsx route injection (1 Edit call after Bash):** Edit `src/App.tsx` to replace the `GENERATED_IMPORTS_START/END` and `GENERATED_ROUTES_START/END` markers with the actual imports and routes.

### Widget file anatomy (use Widget Recipes from insights-catalog.md)

Each widget file MUST include all 6 parts (from the templates in `assets/templates/dashboard/widgets/`):
1. **Card wrapper** — `cursor-pointer hover:shadow-md transition-shadow` + `onClick={() => navigate('<DETAIL_ROUTE>')}`
2. **CardHeader** — icon (`lucide-react`) + title + description + `<ViewAllLink to="<DETAIL_ROUTE>" />`
3. **Inline headline** — `text-3xl font-semibold tabular-nums` extracted value + `<DeltaBadge direction="..." text="..." />`
4. **Chart/KPI body** — Recharts chart or KPI value
5. **Import chrome** — `import { DeltaBadge, ViewAllLink, LoadingState, EmptyState } from '../dashboard/chrome'`
6. **Import shadcn** — `import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'`

### Detail view anatomy

```tsx
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useInsights } from '../hooks/useInsights'

const COLUMNS: ColumnDef<Record<string, unknown>>[] = [
  { key: '<field1>', label: '<Label 1>' },
  { key: '<field2>', label: '<Label 2>', align: 'right' },
  // ...
]

export function <Name>View() {
  const { data, loading, error } = useInsights('<namespace.method>', { startTime: <CONSTANT> })
  const rows = <DATA_SELECTOR_FOR_ROWS>

  if (loading) return <DetailViewShell title="<TITLE>" description="<DESCRIPTION>"><LoadingState height="h-96" /></DetailViewShell>
  if (error) return <DetailViewShell title="<TITLE>" description="<DESCRIPTION>"><EmptyState message={error.message} /></DetailViewShell>

  return (
    <DetailViewShell title="<TITLE>" description="<DESCRIPTION>">
      <RecordsTable rows={rows} columns={COLUMNS} defaultSortKey="<field1>" />
    </DetailViewShell>
  )
}
```

### Dashboard.tsx layout

```tsx
import { Header } from '@/dashboard/chrome/Header'
import { WidgetBoundary } from '@/dashboard/chrome/WidgetBoundary'
// WIDGET_IMPORTS

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 lg:p-8">
      <Header title="<Dashboard Title>" description="<Dashboard description>" />
      
      {/* KPI row — 1–4 tiles */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI widgets */}
      </div>
      
      {/* Chart row — 2-up grid */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart widgets */}
      </div>
      
      {/* Full-width table */}
      <div className="mt-6">
        {/* Table widgets */}
      </div>
    </div>
  )
}
```

Wrap every widget in `<WidgetBoundary label="<Widget Name>">`.

### Step 1 — Compose all code in memory (0 tool calls)

Use Widget Recipes from `insights-catalog.md`. For each widget derive:
- Component name (PascalCase), detail route (kebab), icon from lucide-react
- `<DATA_HOOK>` — `useInsights<ResponseType>('namespace.method', { startTime })`
- `<DATA_SELECTOR>` — response unwrapping expression
- `<HEADLINE_EXPR>` — extract the main number/value
- `<DELTA_DIR>` / `<DELTA_TEXT>` — direction + vs-yesterday text (use `neutral` if unknown)
- Detail view columns derived from `insights-catalog.md` Key response fields

Response Unwrapping:
| Response shape | DATA_SELECTOR |
|---|---|
| `data[].{field}` (timelines) | `(data as any)?.data ?? []` |
| `{ data: { agents[] } }` | `(data as any)?.data?.agents ?? []` |
| `{ totalErrors, data[] }` | `(data as any)?.data ?? []` |
| `{ data: { errorCount, … } }` | `Object.entries((data as any)?.data ?? {}).map(([n,v])=>({name:n,value:v}))` |
| KPI from `currentPeriodSummary` | `String((data as any)?.data?.currentPeriodSummary?.successRate?.toFixed(1)+'%' ?? '—')` |

### Step 2 — Write all files via Bash (1–2 Bash calls)

**MANDATORY: Check widget count before choosing approach.**

```bash
# Count planned widgets (number of widget names in your Phase 7 list)
WIDGET_COUNT=<N>  # substitute the actual count
```

- **If WIDGET_COUNT < 4** → Use the inline heredoc (safe for small content)
- **If WIDGET_COUNT ≥ 4** → Go directly to temp-script path. **Never attempt inline heredoc.** TSX files with React + TypeScript content hit shell limits well below 6 widgets.

**WIDGET_COUNT < 4 — inline heredoc:**

```bash
node << 'NODESCRIPT'
const fs = require('fs'), path = require('path');
const P = '<PROJECT_DIR>';

const files = {
  [`${P}/src/dashboard/Dashboard.tsx`]: `<full Dashboard.tsx>`,
  [`${P}/src/dashboard/widgets/index.ts`]: `<barrel exports>`,
  [`${P}/src/dashboard/widgets/<Widget1>.tsx`]: `<full widget TSX>`,
  [`${P}/src/dashboard/views/<Widget1>View.tsx`]: `<full view TSX>`,
  // ...one entry per widget...
};

for (const [fp, content] of Object.entries(files)) {
  fs.mkdirSync(path.dirname(fp), { recursive: true });
  fs.writeFileSync(fp, content);
}
console.log('✓ ' + Object.keys(files).length + ' files written');
NODESCRIPT
```

**WIDGET_COUNT ≥ 4 — temp script (mandatory):**

```bash
# Write temp script
cat > $PROJECT_DIR/write-widgets.mjs << 'SCRIPT'
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
// Script lives at <PROJECT_DIR>/write-widgets.mjs — resolve parent directory
// This handles POSIX vs Windows path differences automatically
const P = dirname(fileURLToPath(import.meta.url));
const files = {
  [`${P}/src/dashboard/Dashboard.tsx`]: `<full content>`,
  // ...all files...
};
for (const [fp, content] of Object.entries(files)) {
  mkdirSync(dirname(fp), { recursive: true });
  writeFileSync(fp, content);
}
console.log('✓ ' + Object.keys(files).length + ' files written');
SCRIPT

# Execute and delete
node $PROJECT_DIR/write-widgets.mjs && rm $PROJECT_DIR/write-widgets.mjs
```

> **Escaping in both approaches:** backtick → `` \` ``, `${` → `\${`

### Step 3 — Inject routes into App.tsx (included in Step 2)

Add App.tsx to the `files` object in the same Bash call — do NOT use the Edit tool for this.
The marker replacement logic:

```javascript
// Inside the node script, after building the files object:
const appPath = `${P}/src/app/App.tsx`;
let appContent = require('fs').readFileSync(appPath, 'utf8');
const imports = `import { Dashboard } from '@/dashboard/Dashboard'\n` +
  `import { <Widget1>View } from '@/dashboard/views/<Widget1>View'\n`;
const routes = `<Route path="/" element={<Dashboard />} />\n` +
  `<Route path="/<route1>" element={<<Widget1>View />} />\n`;
appContent = appContent
  .replace(/\/\/ GENERATED_IMPORTS_START[\s\S]*?\/\/ GENERATED_IMPORTS_END/,
    `// GENERATED_IMPORTS_START\n${imports}// GENERATED_IMPORTS_END`)
  .replace(/\{\/\* GENERATED_ROUTES_START \*\/\}[\s\S]*?\{\/\* GENERATED_ROUTES_END \*\/\}/,
    `{/* GENERATED_ROUTES_START */}\n${routes}{/* GENERATED_ROUTES_END */}`);
require('fs').writeFileSync(appPath, appContent);
```

This keeps all file writes in one Bash call — no Edit tool diff shown to the user.

## Phase 8 — Validate (3-pass) + Summary

### Pass 1 — TypeScript (1 Bash)
```bash
cd <PROJECT_DIR> && tsc --noEmit
```
If errors → fix silently (max 2 attempts). Common fixes:
- Missing import → add import at top of file
- Type mismatch on `data` → add `as <ExpectedType>` cast

### Pass 2 — API existence check (0 tool calls, in-context)
For every `useInsights('namespace.method', ...)` call written in Phase 7:
verify that `namespace.method` exists in the routing table in `data-router.md` (already in memory from Phase 1).
If any method is unrecognised → fix the widget to use the correct endpoint before continuing.

### Pass 3 — Dev server (1 Bash)
```bash
# Start the dev server and open browser automatically
# --open launches the browser; server stays running for HMR
cd <PROJECT_DIR> && npm run dev -- --open
```

## Phase 8b — Write state.json (0 tool calls, included in Bash)

After tsc passes, write the state file as part of the validation Bash call:

```bash
node << 'SCRIPT'
const fs = require('fs'), path = require('path');
const stateDir = path.join(process.env.PROJECT_DIR, '.dashboard');
fs.mkdirSync(stateDir, { recursive: true });
const state = {
  app: { name: process.env.DASHBOARD_NAME, routingName: process.env.ROUTING_NAME, semver: '1.0.0' },
  env: process.env.ENV,
  org: process.env.ORG,
  tenant: process.env.TENANT,
  cloudUrl: process.env.CLOUD_URL,
  widgets: process.env.WIDGET_NAMES.split(','),
  deployment: { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null }
};
const tmp = path.join(stateDir, 'state.json.tmp');
fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
fs.renameSync(tmp, path.join(stateDir, 'state.json'));
SCRIPT
```

## Summary Format (shown after tsc passes)

Write the summary as follows — no technical language, no file paths:

```
✨ Your **[Dashboard Title]** is ready.

**Preview:** Run `npm run dev` in the project folder, then open http://localhost:5173

**What's inside:**
[For each widget, write one bullet using this pattern:]
• **[Widget Title]** — [Plain-English description of what this shows and why it matters to the user. Focus on the business insight, not the data source.]

**Example bullets (use as a guide for tone):**
• **Active Agents** — How many agents are currently running in your fleet at a glance
• **Invocation Volume** — How busy your agents were over the past 24 hours, charted by hour
• **Error Rate Trend** — Whether your error rate is improving or worsening this week
• **Top Agents by Performance** — Which agents are handling the most work and how fast they respond

When you're ready to publish to Automation Cloud, say **"deploy this dashboard"**.
```

## Incremental Mode (existing dashboard)
If a `<PROJECT_DIR>/src/widgets/` directory already exists:
1. Read all existing widget files before writing
2. Write ONLY new widget files (do not regenerate existing ones)
3. Update `index.ts` to add the new export
4. Run `tsc --noEmit` after addition

## Error Handling
- `npm ci` fails with "missing package-lock.json" → fall back to `npm install`
- `npm ci` fails with network error → retry once; if still failing check internet connectivity
- `tsc --noEmit` errors → fix; max 2 fix attempts before asking user
- Dev server fails → still report success with `tsc` passing; note server issue
