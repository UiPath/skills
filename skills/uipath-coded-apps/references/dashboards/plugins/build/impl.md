# Dashboard Build Plugin

Full pipeline: NLP prompt → plan approval → scaffold → widgets → validate → preview.

## Tool-Use Budget
≤ 14 tool calls for a 6-widget dashboard. Never exceed 20 total.

## Narration Rules — What Users See

This skill serves end users, not developers. Never show npm output, TypeScript errors, file paths, bash commands, or technical logs.

**Show exactly these messages at these moments:**

| When | Show |
|------|------|
| User approves the plan (before Phase 6) | `⚙ Building your dashboard — this usually takes about 30 seconds…` |
| Phase 6 running | *(silence — do not narrate commands or output)* |
| Phase 7 running | *(silence — do not narrate file writes)* |
| tsc passes (Phase 8) | Show the final summary immediately — see Summary Format below |

**If tsc fails:** Fix errors silently (max 2 attempts). Never mention TypeScript to the user. If you cannot fix after 2 attempts, say: "I ran into a configuration issue — please run `npm install` in your project folder and try again."

**If npm ci fails:** Say: "Dependencies are downloading — this can take a moment on first run." Retry once with `npm install`. Do not show npm output.

**If the dev server fails to start:** Include in the summary: "(Note: run `npm run dev` to start the local preview.)" — do not diagnose it further.

**Never say:** "Writing widget files", "Running tsc --noEmit", "Phase 6", "scaffold", "package.json", "useInsights", or any other implementation detail.

## Phase 1 — Boot (1 tool-use block)
Read ALL the following in a single parallel message:
- `../../primitives/auth-context.md`
- `../../primitives/build-plan.md`
- `../../primitives/data-router.md`
- `../../insights-catalog.md`

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

## Phase 4 — Plan (0 tool calls)
Render the plan in chat using the format in build-plan.md.
Show [SDK] or [Insights] label + method for each widget.
Do NOT write any files yet.

## Phase 5 — Approval Gate (0 tool calls)
HALT. Wait for user response.
Follow approval gate rules in build-plan.md exactly.
Do not proceed until explicit approval is received.

## Phase 6 — Scaffold (1 Bash)
Read PAT and tenantId from `~/.uipath/.auth` (env-file format) as described in `../../primitives/auth-context.md` Step 3. Then copy the scaffold template and write `.env.local`:

```bash
# SKILL_ASSETS: use this skill's base directory (shown in your system context
# as "Base directory for this skill"). The scaffold is at:
#   [SKILL_BASE_DIR]/assets/templates/dashboard/scaffold/
# Replace SKILL_BASE_DIR with the actual path from your system context.
SKILL_BASE_DIR="<SKILL_BASE_DIR>"
SKILL_ASSETS="${SKILL_BASE_DIR}/assets"

# Read auth from ~/.uipath/.auth (env-file format)
PAT=$(grep -m1 '^UIPATH_ACCESS_TOKEN=' ~/.uipath/.auth | cut -d'=' -f2-)
TENANT_ID=$(grep -m1 '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
if [ -z "$PAT" ]; then
  PAT=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_ACCESS_TOKEN||a.access_token||'')" 2>/dev/null)
  TENANT_ID=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_TENANT_ID||a.tenantId||'')" 2>/dev/null)
fi

# Derive base URLs from DATA_BASE_URL
if echo "$DATA_BASE_URL" | grep -q "alpha";    then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi

cp -r "${SKILL_ASSETS}/templates/dashboard/scaffold/." <PROJECT_DIR>/
# Remove any node_modules the template developer may have left — prevents npm ci ENOTEMPTY
node -e "require('fs').rmSync('<PROJECT_DIR>/node_modules', {recursive:true, force:true})" 2>/dev/null || true

cd <PROJECT_DIR>
cat > .env.local << EOF
VITE_UIPATH_CLOUD_URL=${DATA_BASE_URL}
VITE_UIPATH_BASE_URL=${API_BASE_URL}
VITE_UIPATH_ORG_NAME=<ORG_NAME>
VITE_UIPATH_TENANT_NAME=<TENANT_NAME>
VITE_INSIGHTS_TENANT_ID=${TENANT_ID}
VITE_UIPATH_PAT=${PAT}
EOF
npm ci 2>/dev/null
```

No client ID, no scope, no OAuth setup required. The PAT comes from the active `uip login` session. For production deployment the PAT is stripped before build (failBuildIfPatSet Vite plugin enforces this).

> **SKILL_BASE_DIR:** Check your system context for "Base directory for this skill" — it shows the exact path where skill assets are installed. Use that as `SKILL_BASE_DIR`. On a fresh Claude Code session this is always available.

## Phase 7 — Widget Generation (1 parallel Write block)
Read the appropriate widget template files from `../../assets/templates/dashboard/widgets/`.
For each widget in the approved plan, write one file to `<PROJECT_DIR>/src/widgets/`:
- Fill `<COMPONENT_NAME>` → PascalCase name (e.g. `AgentSuccessRate`)
- Fill `<DATA_HOOK>` → `useInsights<ResponseType>('namespace.method', { startTime })` — include a TypeScript interface for the response shape
- Fill `<TITLE>` → human label from the plan
- Fill `<DATA_SELECTOR>` → expression to extract the array from the raw response (see below)
- Fill `<X_KEY>` / `<Y_KEY>` / `<VALUE_EXPRESSION>` / `<COLUMNS>` → field names from `insights-catalog.md` Key response fields

### Response Unwrapping — All Insights responses are wrapped objects
Every Insights endpoint returns a nested object, not a flat array. Use the Key response fields from `insights-catalog.md` to find the correct extraction path:

| Pattern | DATA_SELECTOR example |
|---|---|
| `data[].{field}` (most timelines) | `(data as any)?.data ?? []` |
| `{ data: { agents[] } }` (getAgents) | `(data as any)?.data?.agents ?? []` |
| `{ totalErrors, data[] }` (topErroredAgents) | `(data as any)?.data ?? []` |
| `{ data: { errorCount, escalationCount } }` (incidentDistribution) | `Object.entries((data as any)?.data ?? {}).map(([name,value]) => ({name,value}))` |
| KPI from `currentPeriodSummary` | `String((data as any)?.data?.currentPeriodSummary?.successRate?.toFixed(1) + '%' ?? '—')` |

Write ALL widget files in a single message with parallel Write calls.
Also write `<PROJECT_DIR>/src/widgets/index.ts` exporting all components.
Update `<PROJECT_DIR>/src/App.tsx` to import widgets and pass them as children to `<DashboardShell>`.

## Phase 8 — Validate + Summary (2 Bash)
```bash
cd <PROJECT_DIR> && tsc --noEmit
```
If errors → fix them before proceeding. Common fixes:
- Missing import → add import at top of file
- Type mismatch on `data` → add `as <ExpectedType>` cast

```bash
# Verify Vite can start (dry-run check only — don't actually start server)
cd <PROJECT_DIR> && npx vite --version > /dev/null 2>&1 && echo "VITE_OK"
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
