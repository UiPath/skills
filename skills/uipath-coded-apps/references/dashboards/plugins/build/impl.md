# Dashboard Build Plugin

By the time you read this you have already loaded all docs, run login, checked state, and fired pre-warm in the background (per CAPABILITY.md). The user is waiting for the plan.

## Rules

1. **Zero tool calls between user request and plan.** Everything internal runs in the parallel blast. The first thing the user sees is the plan.
2. **Zero tool calls between plan and build confirmation.** Pure text HALT.
3. **One tool call for the build.** A single bash command runs the build script and streams progress.
4. Never read `build-dashboard.mjs` — this file documents everything.
5. Never run `ls`, `find`, or directory exploration.

---

## Phase 1 — Preflight (already done in background)

You already have the `uip login status` response from the parallel blast. Extract:

- `orgName` ← `Data.Organization`
- `tenantName` ← `Data.Tenant`
- `cloudUrl` ← `Data.BaseUrl`

Verify `Data.Status === "Logged in"` — if not, stop and tell the user to run `uip login`.

### Derive apiUrl from cloudUrl

| cloudUrl | apiUrl |
|----------|--------|
| `https://alpha.uipath.com` | `https://alpha.api.uipath.com` |
| `https://staging.uipath.com` | `https://staging.api.uipath.com` |
| `https://cloud.uipath.com` | `https://api.uipath.com` |

Rule: insert `api.` before `uipath.com`. Exception: `cloud.uipath.com` → `api.uipath.com`.

### Read tenantId from auth file

```bash
node -e "
const fs   = require('fs')
const path = require('path')
const home     = process.env.HOME || process.env.USERPROFILE
const authPath = path.join(home, '.uipath', '.auth')
const content  = fs.readFileSync(authPath, 'utf8')
const envMatch = content.match(/^UIPATH_TENANT_ID=(.+)$/m)
if (envMatch) { console.log(envMatch[1].trim()); process.exit(0) }
const parsed = JSON.parse(content)
console.log(parsed.UIPATH_TENANT_ID || parsed.tenantId || '')
"
```

Pre-warm is already running at `<PROJECT_DIR>`. Do not re-fire it.

---

## Phase 2 — Plan (output this now, zero tool calls)

Classify each metric using `tier-resolution.md` and `capability-registry.json`. Write `intent.json` in memory (do not save it yet). Then output the plan.

### Plan format

The plan must feel like a thoughtful product recommendation, not a technical specification. Rules:

- Lead with a name and widget count on one line
- One bullet per widget — widget name in bold, time range in parentheses, then one sentence on what it shows and why it matters
- Close with 3–4 concrete things the user can ask for, phrased as natural language
- If a metric was hard-refused: one sentence inline, strikethrough style, with the alternative offered
- No API names, no tier labels, no metric IDs, no JSON, no code

**Template:**

```
Here's your **[Dashboard Name]** — [N] widgets ready to build.

📊 **[Widget Name]** ([time range]) — [one sentence: what it shows and why it's useful to them specifically]
📈 **[Widget Name]** ([time range]) — ...
🔢 **[Widget Name]** — ...
📋 **[Widget Name]** ([time range]) — ...

Confirm to build, or tell me what to change:
→ "make it 7 days"
→ "add a KPI for total errors"
→ "remove the latency widget"

**One quick thing:** Do you have a UiPath OAuth app client ID for dashboards?
Paste it here, or say **"create one"** and I'll set it up before building.
```

The plan message always ends with the OAuth question unless `clientId` is already in intent.json from a prior session.

If the user's confirmation includes a client ID or "create one", capture it and proceed. If they confirm without addressing it and `clientId` is already set in intent.json, skip silently.

**Widget type icons:**
- 🔢 KPI card or sparkline
- 📈 Line or area chart
- 📊 Bar or donut chart
- 📋 Table or ranked list
- 🔷 Multi-line chart (e.g. P50/P95)

**Example plan:**

```
Here's your **Agent Health Dashboard** — 4 widgets ready to build.

🔢 **Active Agents** — count of agents that ran at least once in the last 30 days, so you can see fleet utilisation at a glance
📈 **Error Rate Trend** (7 days) — daily error counts as a trend line so you can spot spikes before they become incidents
🔷 **Latency P50 / P95** (30 days) — both percentiles on one chart to distinguish typical vs tail latency
📋 **Top Failing Agents** (30 days) — agents ranked by error count so you know where to investigate first

Confirm to build, or tell me what to change:
→ "make all charts 7 days"
→ "add invocation volume"
→ "remove the latency chart"
→ "show as a table instead"

**One quick thing:** Do you have a UiPath OAuth app client ID for dashboards?
Paste it here, or say **"create one"** and I'll set it up before building.
```

### intent.json schema (write to disk in Phase 4 after confirmation)

```json
{
  "dashboardName": "Operations Health",
  "timeRange": "30d",
  "projectDir": "/absolute/path",
  "routingName": "operations-health-x7k2",
  "orgName": "...", "tenantName": "...", "cloudUrl": "...", "apiUrl": "...",
  "tenantId": "<UUID>", "clientId": "",
  "metrics": [
    { "name": "agent-errors", "tier": "T1" },
    { "name": "queue-failure-threshold", "tier": "T2", "params": { "threshold": 20, "direction": "gt" } },
    {
      "name": "custom", "tier": "T3", "title": "...", "displayAs": "ranked-table",
      "fnBody": "...", "valueField": "count", "valueLabel": "items"
    }
  ]
}
```

Routing name: `<kebab-name>-<4-char-random>`. Set once at plan time. Never changes.

---

## Phase 3 — Approval gate (zero tool calls)

**HALT.** Output only text. No tool calls.

- User confirms + provides client ID → write clientId into intent.json, continue to Phase 4
- User confirms + says "create one" → create OAuth app (see below), write clientId, continue to Phase 4
- User confirms (clientId already in intent.json) → continue to Phase 4
- User requests a change → update plan, re-render with OAuth question, HALT again
- User cancels → discard

**If user says "create one":** Run scope discovery + app creation here:

```bash
uip admin scopes list --output json
```

From the JSON response, extract scope names (look for a `Data` array with `Name` or `Scope` fields). Intersect with the desired scopes:

**Desired scopes** (use whichever are available in the environment):
```
OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Read OR.Folders OR.Folders.Read
OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read
OR.Tasks OR.Tasks.Read OR.Queues OR.Queues.Read
OR.Users OR.Users.Read Insights Insights.RealTimeData
```

Build the `--user-scope` argument from the intersection (comma-separated, no spaces). Then:

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173" \
  --user-scope "<INTERSECTION_OF_AVAILABLE_SCOPES>" \
  --output json
```

Read `ClientId` from response, write to intent.json.

> **Note:** If `Insights` and `Insights.RealTimeData` are not available in this environment, T1 Insights widgets will return 401/403 in the browser. Warn the user: "Insights scopes are not available in this environment — Insights-based widgets will not show data. SDK-based widgets (T3-SDK) will still work."

Tell the user: "OAuth app created — building now."

**If command fails:** direct user to `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps`. Do not proceed without `clientId`.

---

## Phase 3.5 — Verify SDK types from scaffold (0–N parallel Reads)

After the user confirms, before writing intent.json to disk, verify field names for any T2 or T3-SDK metrics against the actual TypeScript declaration files in the scaffold.

These files are the exact same source the TypeScript compiler uses — field names are guaranteed correct.

**Path:** `<SCAFFOLD_DIR>/node_modules/@uipath/uipath-typescript/dist/<service>/index.d.ts`

Where `<SCAFFOLD_DIR>` is the project directory + `/../scaffold` relative to SKILL_BASE_DIR:
```
<SKILL_BASE_DIR>/assets/templates/dashboard/scaffold/node_modules/@uipath/uipath-typescript/dist/
```

**When to read:**
- **T2 metrics**: Read the `.d.ts` for the service in the registry entry (e.g. `dist/jobs/index.d.ts` for `jobs-by-state`). Verify the `filterField` exists on the response type.
- **T3-SDK metrics**: Read the `.d.ts` for any service the `fnBody` imports (e.g. if fnBody uses `Jobs`, read `dist/jobs/index.d.ts`). Verify field names used in `.map()` expressions match the response type.
- **T1 metrics**: Skip — field names come from the capability registry and are pre-verified against the SDK response types.

**Fire all relevant reads in ONE parallel message.** If the scaffold's node_modules doesn't exist yet (pre-warm still running), skip this phase and rely on the SDK docs from Turn 2.

**Check: does the scaffold have node_modules?**
```bash
node -e "
const path = require('path')
const sdkDist = path.join('<SKILL_BASE_DIR>', 'assets', 'templates', 'dashboard', 'scaffold', 'node_modules', '@uipath', 'uipath-typescript', 'dist')
process.exit(require('fs').existsSync(sdkDist) ? 0 : 1)
" && echo SDK_TYPES_AVAILABLE || echo SDK_TYPES_NOT_READY
```

**If SDK_TYPES_AVAILABLE:** Read relevant `.d.ts` files in parallel, then adjust intent.json if any field names are wrong.

**If SDK_TYPES_NOT_READY:** Skip — the build script's `tsc --noEmit` will catch type errors.

**Example — verifying `jobs-by-state` T2 metric:**

Read `<SKILL_BASE_DIR>/assets/templates/dashboard/scaffold/node_modules/@uipath/uipath-typescript/dist/jobs/index.d.ts`

Check that `JobGetResponse` has a `state` field. From the `.d.ts`:
```typescript
export interface JobGetResponse {
  key: string
  state: JobState         ← ✓ confirmed
  processName: string
  ...
}
```

**Example — verifying a T3-SDK fnBody:**

If fnBody uses `j.processName` after calling `Jobs.getAll()`, reading `dist/jobs/index.d.ts` confirms `processName` exists on `JobGetResponse`. If the code used `j.name` instead, this phase catches the error before the build script's tsc.

**After verification:** Update intent.json in memory with any corrected field names, then proceed to Phase 4.

---

## Phase 4 — Build (one tool call)

`SKILL_BASE_DIR` is the directory shown in "Base directory for this skill:" from your activation message — the same directory that contains `SKILL.md`. It ends in `/skills/uipath-coded-apps` (or the equivalent Windows path).

The build script is always at:
```
$SKILL_BASE_DIR/assets/scripts/build-dashboard.mjs
```

On Windows:
```
<SKILL_BASE_DIR>\assets\scripts\build-dashboard.mjs
```

Write intent.json to disk, then run:

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" "<INTENT_JSON_PATH>"
```

### What to show the user

Show a clean, minimal build experience. Translate events into one line of progress — no raw JSON, no event names.

**Progress template:**

```
Building **[Dashboard Name]**…

  ✓ [Widget Name]
  ✓ [Widget Name]
  ✓ [Widget Name]
  ✓ TypeScript clean

Opening your dashboard at http://localhost:57173
```

**Event → display mapping:**

| Event | What to show the user |
|-------|----------------------|
| `PREWARM_START` | (silent — installing in background while you read the plan) |
| `PREWARM_DONE` | (silent — dependencies ready) |
| `SCAFFOLD_READY` | (silent) |
| `ENV_WRITTEN` | (silent) |
| `WIDGET_READY:{"name":"X","index":N,"total":M}` | `  ✓ X  (N of M)` |
| `T3_RETRY:{"widget":"X","errors":[...]}` | `  ↻ X — adjusting code, one moment…` — update fnBody and re-run |
| `TSC_PASS` | `  ✓ All code validated` |
| `AUTH_MISSING` | Pause — ask the user for a client ID before continuing |
| `PARTIAL_BUILD_DETECTED` | `  ↻ Picking up from where we left off…` |
| `SERVER_READY:{"url":"..."}` | `Opening your dashboard…` |
| `BUILD_RESULT:{"success":true,...}` | Open previewUrl in browser, then show success message |
| `PREWARM_FAILED` | "Dependency install failed. If this keeps happening, run `npm ci` manually in [projectDir] and try again." |

If `T3_RETRY` fires and a second attempt still fails (exit code 2 again): tell the user "I couldn't get that widget to compile. I've removed it from the dashboard — the rest built cleanly. You can re-add it once we figure out the right query."

### Success message

After `BUILD_RESULT`, open the URL and respond:

```
Your **[Dashboard Name]** is live at http://localhost:57173 🎉

The dashboard has [N] widgets: [comma-separated names].
Tell me what to change — I can add widgets, adjust time ranges, swap chart types, or deploy it to your team.
```

Keep it warm and action-oriented. The user just got something real — meet that moment.
