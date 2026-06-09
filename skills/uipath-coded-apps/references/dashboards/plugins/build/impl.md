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

**If user says "create one":** Run this single command:

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173" \
  --user-scope "OR.Assets,OR.Jobs,OR.Folders,OR.Buckets,OR.Execution,OR.Tasks,OR.Queues,OR.Users,Insights,Insights.RealTimeData" \
  --output json
```

Read `ClientId` from the JSON response and write it to intent.json. Tell the user: "OAuth app created — building now."

**If the command fails** (invalid scopes for this environment): retry with the minimal set:

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173" \
  --user-scope "OR.Assets,OR.Jobs,OR.Folders,OR.Buckets,OR.Execution,OR.Tasks,OR.Queues,OR.Users" \
  --output json
```

If both fail: direct the user to `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps` to create one manually and paste back the client ID. Do not proceed without `clientId`.

---

## Phase 3.5 — Verify SDK types (0–N parallel Reads)

After the user confirms, before writing intent.json to disk, verify field names for T2 and T3-SDK metrics using the Read tool directly on the `.d.ts` files.

**Do NOT use a bash check command.** Path escaping on Windows is unreliable in `node -e` inline scripts. Instead, attempt the Read directly — if the file doesn't exist the Read simply fails and you skip.

**Path pattern:**
```
<ROUTING_NAME>'s project: ~/dashboards/<ROUTING_NAME>/node_modules/@uipath/uipath-typescript/dist/<service>/index.d.ts
```

Note: the `agents` service (Insights SDK, PR #438) may not be in the installed version yet. Only read services that actually exist — `jobs`, `queues`, `tasks`, `processes`, `assets` are available in the current release.

**When to read:**
- **T2 metrics**: Read `dist/<service>/index.d.ts` for the metric's service. Verify `filterField` exists on the response type.
- **T3-SDK metrics**: Read `dist/<service>/index.d.ts` for each service the `fnBody` imports. Verify field names match the response type.
- **T1 metrics using Insights** (`agent-errors`, `agent-latency`, etc.): Skip — the `agents` service isn't in the current SDK release. `tsc --noEmit` catches any errors.
- **T1 metrics using Jobs** (`job-failures`, `job-completion-trend`): Read `dist/jobs/index.d.ts` to verify field names.

**Fire all relevant reads in ONE parallel message.** If any Read fails (file not found), skip that service — pre-warm may still be running or the service isn't in this SDK version.

**Example — verifying `jobs-by-state` T2 metric:**

Read `~/dashboards/<ROUTING_NAME>/node_modules/@uipath/uipath-typescript/dist/jobs/index.d.ts`

Verify `JobGetResponse` has a `state` field. If read fails → skip.

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

### What to show during build

Show a minimal, clean progress experience. Most events are silent.

**Silent (never show to user):**
- `PREWARM_START`, `PREWARM_DONE` — pre-warm is background, user doesn't need to know
- `SCAFFOLD_READY`, `ENV_WRITTEN` — internal setup steps
- `PARTIAL_BUILD_DETECTED` — resume silently

**Show as a single tick line:**
- `WIDGET_READY:{"name":"X","index":N,"total":M}` → `  ✓ X`

**Show as status line:**
- `TSC_PASS` → `  ✓ All code validated`
- `SERVER_READY:{"url":"..."}` → `Opening your dashboard…`

**Show and act on:**
- `T3_RETRY:{"widget":"X","errors":[...]}` → `  ↻ X — fixing a type error, one moment…` then update fnBody and re-run
- `AUTH_MISSING` → pause, complete Phase 3 first
- `PREWARM_FAILED:{"stderr":"..."}` → `Dependency install failed. Try running npm ci in [projectDir].`
- `BUILD_RESULT:{"success":true,...}` → open previewUrl in browser, show success message

**Progress template — this is ALL the user should see during a build:**

```
Building **[Dashboard Name]**…

  ✓ [Widget 1]
  ✓ [Widget 2]
  ✓ [Widget 3]
  ✓ All code validated

Opening your dashboard at http://localhost:57173
```

Never show: raw JSON, event name strings, bash command output, tsc output, npm output.

If `T3_RETRY` fires and a second attempt still fails (exit code 2 again): tell the user "I couldn't get that widget to compile. I've removed it from the dashboard — the rest built cleanly. You can re-add it once we figure out the right query."

### Success message

After `BUILD_RESULT`, open the URL and respond:

```
Your **[Dashboard Name]** is live at http://localhost:57173 🎉

The dashboard has [N] widgets: [comma-separated names].
Tell me what to change — I can add widgets, adjust time ranges, swap chart types, or deploy it to your team.
```

Keep it warm and action-oriented. The user just got something real — meet that moment.
