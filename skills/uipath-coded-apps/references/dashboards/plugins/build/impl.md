# Dashboard Build Plugin

By the time you read this you have already loaded all docs, run login, checked state, and fired pre-warm in the background (per CAPABILITY.md). The user is waiting for the plan.

## Rules

1. **Zero tool calls between user request and plan.** Everything internal runs in the parallel blast. The first thing the user sees is the plan.
2. **Zero tool calls between plan and build confirmation. Pure text HALT.** The build plan gate is deliberately text-only: do NOT use the question/option tool here — it reproducibly suppresses the plan rendering (the user gets options with no plan). The plan text ends with the confirm/change affordances; OAuth details are asked AFTER approval (Phase 3).
3. **The build runs in a subagent (Phase 4).** After confirmation, the main thread prints one "Building…" line, spawns the build subagent using the host agent's sub-task mechanism (the `Task` tool in Claude Code; the equivalent sub-agent/sub-task feature in other agents), and relays its returned milestone block. The build command, events, tsc/npm output, and retries stay inside the subagent.
4. Never read `build-dashboard.mjs` — this file documents everything.
5. Never run directory exploration via any shell — `ls`, `find`, `dir`, `Get-ChildItem`, `tree`.

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

Pre-warm is already running at `<PROJECT_DIR>`. Do not re-fire it.

---

## Phase 2 — Plan (output this now, zero tool calls)

Classify each metric using `tier-resolution.md` and `capability-registry.json`.

**SDK validation (do this before writing the plan):** For every requested metric, apply the three-step check in `tier-resolution.md § SDK validation`. Every metric in the plan must be backed by a method in the SDK service reference. Metrics with no SDK path are refused inline (strikethrough + alternative). Resolve each metric in memory (which SDK method serves it) so the plan is credible — but do NOT write `intent.json` or any `metrics/*.ts` file yet; the build subagent authors all files in Phase 4. Then output the plan.

### Plan format

The plan must feel like a thoughtful product recommendation, not a technical specification. Rules:

- Lead with a name and widget count on one line
- One bullet per widget — widget name in bold, time range in parentheses, one sentence on what it shows and why it matters, **then a short plain-language clause on how it renders** (the visual form + the key elements they will see: a single number, a sortable table with named columns, an area-chart trend with a headline, a percentage line, a donut split, etc.) so the user can picture the visualization and adjust it
- Close with 3–4 concrete things the user can ask for, phrased as natural language
- If a metric was hard-refused: one sentence inline, strikethrough style, with the alternative offered
- No API names, no tier labels, no metric IDs, no JSON, no code

**Template:**

```
Here's your **[Dashboard Name]** — [N] widgets ready to build.

📊 **[Widget Name]** ([time range]) — [what it shows and why it's useful to them], shown as [the visual form + key elements]
📈 **[Widget Name]** ([time range]) — [what + why], shown as [an area-chart trend with a running headline and a vs-previous change]
🔢 **[Widget Name]** — [what + why], shown as [a single headline number]
📋 **[Widget Name]** ([time range]) — [what + why], shown as [a sortable table with columns A, B, C]

Confirm to build, or tell me what to change:
→ "make it 7 days"
→ "add a KPI for faulted jobs"
→ "remove the consumption widget"
```

The plan message ends there — no OAuth talk in the plan, no tool calls in the plan response. Setup details (client ID) are collected AFTER the user approves the plan, in Phase 3.

> **The plan response is text-only by design.** Never put a question/option tool call in the same response as the plan — live runs showed it reliably replaces the plan with a bare options list (the user approves widgets they never saw). Structured-choice questions fire only on later, short turns: the post-approval OAuth question (Phase 3), intent disambiguation, and the deploy pin choice.

**Widget types — icon + how to describe the rendering** (always state the visual form so the user can adjust it):
- 🔢 **KPI card** — "as a single headline number". Add "with a vs-previous-period change badge" ONLY if the metric module returns `{ value, previous }` — value over the dashboard window, previous over the equal-length prior window via `priorWindow(start, end)` (works for any time range). A plain KPI returns `{ value }` and shows no badge — don't promise a badge you won't compute.
- 📈 **Line or area chart** — "as an area/line trend over time, with a headline [total/latest/average] and a vs-previous change"
- 📈 **Rate chart** — "as a percentage line over time with an overall headline" (a ratio: numerator ÷ denominator per period)
- 📊 **Bar or donut chart** — "as a bar chart" / "as a donut split by category"
- 📋 **Table or ranked list** — "as a sortable table with columns [A, B, C]", or "ranked worst/highest-first". To make rows clickable (drill into the clicked entity), set `rowLink: { key: "<rowField>" }` and export `fetchDetailByKey(sdk, key, getToken)` — generates a `/<widget>/:key` detail page.
- 🔷 **Multi-line chart** — "as multiple lines over time (e.g. P50/P95)"

> **Promise only what the scaffold can render.** The bullets above are the complete set of buildable affordances. Before writing a feature into the plan, confirm it maps to one of them: KPI delta → `{value, previous}`; row drill-down → `rowLink` + `fetchDetailByKey`. If a prompt needs something not listed (a bespoke interaction, a custom layout), say so in the plan ("this needs a template extension") rather than promising it and silently dropping it during the build.

**Example plan:**

```
Here's your **Agent Operations Dashboard** — 4 widgets ready to build.

🔢 **Active Agents** — agents that ran at least once in the last 30 days, so you can see fleet utilisation at a glance, shown as a single headline number
📋 **Agent Health** (30 days) — where to focus your attention, shown as a sortable table ranked worst-first, with columns for agent, health score, and last incident
📈 **Memory Calls** (7 days) — agent memory access volume so you can spot unusual activity early, shown as an area-chart trend over time with a running total and a vs-previous-week change
📊 **Governance Verdicts** (7 days) — how policy enforcement is splitting across your agents, shown as a donut split by allow / deny / no-op

Confirm to build, or tell me what to change:
→ "make all charts 7 days"
→ "add agent consumption"
→ "remove the governance donut"
→ "show memory calls as a table instead"
```

> If the user asks for agent error/latency **trends**: those have no SDK endpoint — refuse inline per `tier-resolution.md § T0` and offer `agent-health` or a Jobs-based trend instead.

### intent.json schema (write to disk in Phase 4 after confirmation)

`intent.json` is **pure metadata** — no `fnBody`, no `detailFnBody`. Data-fetch code lives in `metrics/<name>.ts` modules (sibling folder to `intent.json`).

```json
{
  "schemaVersion": 2,
  "dashboardName": "Operations Health",
  "dashboardDescription": "Job throughput, agent health, and governance posture at a glance.",
  "timeRange": "30d",
  "projectDir": "/absolute/path",
  "routingName": "operations-health-x7k2",
  "orgName": "...", "tenantName": "...", "cloudUrl": "...", "apiUrl": "...",
  "clientId": "",
  "metrics": [
    { "name": "job-failures", "tier": "T1" },
    { "name": "queue-failure-threshold", "tier": "T2", "params": { "threshold": 20, "direction": "gt" } },
    {
      "name": "custom", "tier": "T3", "title": "...", "displayAs": "ranked-table",
      "valueField": "count", "valueLabel": "items"
    }
  ]
}
```

Routing name: `<kebab-name>-<4-char-random>`. Set once at plan time. Never changes.

### Presentation fields — make widgets read like a real dashboard

Charts and tables render shallow without these. Set them on each metric in `intent.json` (registry fills defaults for cataloged metrics; you set them for T3). All optional except where noted.

**Chart metrics** (`line-chart`, `area-chart`, `bar-chart`, `donut-chart`):
- `headlineMode` — how the big number is computed from the series: `sum` (totals — default), `avg` (rates/latency), `latest`, `max`, `min`, `count`. **Never leave a count-trend on the implicit last-point value.**
- `deltaPolarity` — whether an increase is good or bad, drives the badge colour: `up-good` (e.g. completions), `up-bad` (e.g. errors), `neutral`. The build computes the actual % change.
- `subtitle` — one line of context (e.g. `"Agent runs — last 24h"`). Omit to auto-fill the time window.
- `yKey` / `xKey` — the value and axis fields returned by the module's `fetchData`.

**Rate / percentage metric** (`displayAs: "rate-chart"`): for ratios like error rate = faulted ÷ total.
- `fetchData` returns rows carrying **both** a numerator and denominator per bucket, e.g. `[{ date, faulted, total }]`.
- `rateNum` / `rateDen` (**required**) — those field names (`"faulted"`, `"total"`). The build plots num/den % per bucket, headline = overall %, delta in `pp`.

**Detail views** (any chart) — the drill-down must show records, not the chart's buckets:
- `"detail": true` in the intent entry + `export const fetchDetail: MetricFn` in the module — a record-grain query (individual rows behind the chart). Falls back to `fetchData` if absent (shows buckets — avoid for chart metrics).
- `detailColumns` — array of `{ key, label, align?, format?, color? }`. `format`: `number` | `percent` | `duration` | `timeAgo` | `text`. `color`: `goodHigh` | `goodLow` (threshold colouring). The build compiles these into formatted/coloured cells.
- `detailSortKey` — raw field to sort on (e.g. an ISO `startTime`), so chronological order is correct even when a column renders a friendly label.

Full detail-view contract (record grain, toRows, anti-patterns): `references/dashboards/primitives/detail-views.md`.

Example T3 chart with full presentation — intent entry:

```json
{
  "name": "faulted-jobs-trend", "tier": "T3", "title": "Faulted Jobs",
  "displayAs": "area-chart", "xKey": "date", "yKey": "count",
  "headlineMode": "sum", "deltaPolarity": "up-bad", "subtitle": "Faulted jobs — last 7 days",
  "detail": true,
  "detailColumns": [
    { "key": "processName", "label": "Process" },
    { "key": "state", "label": "State" },
    { "key": "createdTime", "label": "Started", "format": "timeAgo" }
  ],
  "detailSortKey": "createdTime"
}
```

Module at `metrics/faulted-jobs-trend.ts`:

```ts
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const rows = (await new Jobs(sdk as never).getAll({ filter: "State eq 'Faulted'" }))?.items ?? []
  const byDate: Record<string, number> = {}
  for (const j of rows) { const d = String(j.createdTime).slice(0, 10); byDate[d] = (byDate[d] ?? 0) + 1 }
  return Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))
}

export const fetchDetail: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  return (await new Jobs(sdk as never).getAll({ filter: "State eq 'Faulted'", orderby: 'CreationTime desc' }))?.items ?? []
}
```

---

## Phase 3 — Approval gate, then setup details

**HALT** after the plan (the Phase 2 response is pure text). Handle the user's reply in two stages:

**Stage 1 — plan approval (free text):**
- Change request / feedback → update the plan, re-present it (pure text again), HALT
- User cancels → discard
- Confirmation → Stage 2

**Stage 2 — setup details (only what the confirmation didn't already answer):**
- Confirmation already contains a client ID → carry it as the plan's `clientId`, continue to Phase 4
- Confirmation already says to create one (e.g. "build it, create the app") → create the OAuth app (below), continue to Phase 4
- `clientId` already known (provided earlier, or in an existing project's `intent.json`) → continue to Phase 4, ask nothing
- Otherwise → ask ONE short structured-choice question (SKILL.md Rule 17 — this is a short turn, safe for the question tool):

  *"How should I set up the OAuth app this dashboard signs in with?"*

  | Option | Meaning |
  |--------|---------|
  | **Create one for me (Recommended)** | Run the external-app create command, then build |
  | **I'll paste an existing client ID** | Wait for the ID, write it into intent.json, then build |

  A free-text reply (including a pasted ID, or a late change request) always remains valid and takes precedence.

Never re-ask for anything the user already provided. The same pattern applies to deploy (see `plugins/deploy/impl.md`): present the deploy plan as text → free-text confirm → then the pin question only if the confirmation didn't already settle it.

**Creating the OAuth app:** Run this single command. `--redirect-uri` takes **comma-separated** values — register BOTH the local dev server and the org portal base, so login works in dev and after deploy:

- `http://localhost:57173` — local dev server
- `<CLOUD_URL>/<ORG>/portal_` — deployed app base; `<CLOUD_URL>` and `<ORG>` are the `cloudUrl` (`Data.BaseUrl`) and `orgName` (`Data.Organization`) extracted in Phase 1, so they track the logged-in environment (e.g. `https://alpha.uipath.com/acme/portal_`)

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173,<CLOUD_URL>/<ORG>/portal_" \
  --user-scope "OR.Assets,OR.Jobs,OR.Folders,OR.Buckets,OR.Execution,OR.Tasks,OR.Queues,OR.Users,Insights,Insights.RealTimeData,PIMS" \
  --output json
```

Read `ClientId` from the JSON response and carry it as the plan's `clientId` (the build subagent writes it into intent.json). Tell the user: "OAuth app created — building now."

**If the command fails** (invalid scopes for this environment): retry with the minimal set:

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173,<CLOUD_URL>/<ORG>/portal_" \
  --user-scope "OR.Assets,OR.Jobs,OR.Folders,OR.Buckets,OR.Execution,OR.Tasks,OR.Queues,OR.Users,PIMS" \
  --output json
```

> **Insights metrics need the Insights scopes.** The minimal fallback drops `Insights,Insights.RealTimeData` — every agent **and** Maestro Insights/SLA metric (`agent-*`, `trace-*`, `case-sla-*`, `top-*`, `*-status-timeline`, `element-latency-stats`) returns 403 under it. `PIMS` is kept in the minimal set so plain Maestro `getAll` metrics (e.g. `cases-running-above`) still work. Use the minimal set only when the environment rejects the Insights scopes; the Insights-based metrics will be unavailable.

If both fail: direct the user to `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps` to create one manually and paste back the client ID. Do not proceed without `clientId`.

---

## Phase 3.5 — Cross-check each metric module against the documented response

`tsc` validates the *shape* of a query (do the fields exist?) but never its *meaning* (does this filter actually match the rows the user wants?). A query can compile green and return zero rows — the most common way a dashboard ships empty, because the agent filtered on a plausible-but-wrong field.

**The build subagent (Phase 4) authors these modules and applies this check — it is NOT done in the main thread.** When the subagent writes each `metrics/<name>.ts` from the SDK references, it cross-checks every one against the **Example response** and **semantics notes** in the relevant `references/sdk/*.md` file (already loaded in the parallel blast). For each metric, confirm:

1. **The field you filter or read on appears in the example response** — with the value you expect. Not just "the field exists in the type" (both `sourceType` and `packageType` exist) — the example shows the real *value*. **Appearing in the response does NOT make a field filterable**: mapped fields like `processName` are read-only and throw `Invalid OData query options` in a `$filter` (see `orchestrator.md § Filterable vs read-only Job fields`). Filter only on documented raw fields and match mapped fields client-side.
2. **No semantics note warns against your choice.** The references flag the traps types can't express.
3. **Your return shape matches the example** — `.items` vs `.data` vs a top-level array, and the exact field names you map to `xKey`/`yKey`/columns.
4. **Table column keys match the return shape.** For a `data-table`/`ranked-table`, every `columns`/`columnDefs` key must be a field your module actually returns per row — a key with no matching field renders an empty `—` column. Tables use `columns`/`columnDefs` (NOT `detailColumns`, which only feeds chart drill-down views); a T3 table with no columns is rejected by the build.

This is a read-only, deterministic check — no live calls. The references encode the domain semantics that types alone don't.

### The canonical trap — agent jobs vs trigger source

An agent job is identified by **`packageType === 'Agent'`** (the SDK renames the raw API field `ProcessType → packageType`). The trap is `sourceType`: it's the *trigger origin* (Manual/Schedule/Queue/Agent/…), not the agent discriminator — and it has a value `'Agent'` that looks right but isn't. The example response in `references/sdk/orchestrator.md § Job classification` shows the fields side by side.

```ts
// ✗ Wrong — sourceType is the trigger origin, not the agent discriminator
return (await new Jobs(sdk as never).getAll({ filter: "SourceType eq 'Agent'" }))?.items ?? []

// ✓ Correct — OData filter uses the raw field name ProcessType
return (await new Jobs(sdk as never).getAll({ filter: "ProcessType eq 'Agent'" }))?.items ?? []
// (client-side, the mapped field is packageType: j.packageType === 'Agent')
```

If a metric's correctness depends on data you genuinely can't determine from the references, prefer a simpler, well-documented query over a guess — and tell the user what you simplified.

**After cross-checking:** the build subagent writes the verified `metrics/<name>.ts` modules and `intent.json` itself (Phase 4). No metric files or `intent.json` are written in the main thread — so none of those file edits surface to the user.

---

## Offer-on-detect upgrade

If a build or edit against an existing project emits `UPGRADE_AVAILABLE:{from,to}`, the dashboard was built on an older scaffold than the one now shipped. Tell the user a newer dashboard scaffold is available and offer to upgrade — same plan→confirm ethos, **never automatic**. On confirm, run a lone `UPGRADE` edit-intent (`{ projectDir, op: "UPGRADE" }`) — it preserves their metrics (`intent.json` + `src/metrics`) and regenerates the app against the current scaffold. See `primitives/incremental-editor.md`.

---

## Maintaining the starter-kit archive

The build extracts a committed, versioned archive (`assets/fixtures/governance-dashboard-starter-kit.zip`) into each new dashboard instead of copying the loose `scaffold/` directory; the loose `templates/dashboard/scaffold/` stays the editable source of truth. After changing the scaffold (or the widget templates), re-pack and commit the refreshed archive: `node assets/scripts/pack-scaffold.mjs --version <x.y.z>`. CI / pre-commit runs `pack-scaffold.mjs --check` to fail if the scaffold changed without re-packing. Extraction uses a dependency-free pure-Node helper (`assets/scripts/lib/zip.mjs`) — no system `unzip`/`tar`/PowerShell — so any coding agent on any OS extracts it identically.

---

## Phase 4 — Build (runs in a build subagent)

To keep the experience seamless, Phase 4 executes inside a **build subagent** — a sub-task spawned via the host agent's mechanism (the `Task` tool in Claude Code; the equivalent sub-agent feature in Codex, Gemini, and others). The subagent **authors `intent.json` and the metric modules**, runs the build script, handles the type-error retry loop, and returns one short milestone block. Every file write, the bash command, the raw event stream, tsc/npm output, and retries stay inside the subagent — none surface in the main thread. **The user sees only your one-line "Building…" and the final milestone — never the `intent.json` or `metrics/*.ts` writes.**

`SKILL_BASE_DIR` is the directory shown in "Base directory for this skill:" from your activation message — it contains `SKILL.md` and ends in `/skills/uipath-coded-apps`. `INTENT_DIR` is the directory the subagent writes `intent.json` + `metrics/` into; `INTENT_JSON_PATH` is `<INTENT_DIR>/intent.json`.

**Step 1 — Show one line, then spawn the build subagent.** Print only:

```
Building **[Dashboard Name]**…
```

Do NOT write `intent.json` or any `metrics/*.ts` in the main thread — the subagent writes them, so those edits stay hidden. Spawn the build subagent with this prompt (use your host agent's sub-task mechanism — e.g. the `Task` tool in Claude Code), pasting the APPROVED PLAN (it is the subagent's authoring spec — give it everything needed to write the files):

> You are the dashboard build executor. You NEVER surface raw output or file edits — your final message is the only thing shown.
> 1. Read `<SKILL_BASE_DIR>/references/dashboards/plugins/build/impl.md` §§ "Phase 3.5" and "Build subagent — execution" and follow them exactly.
> 2. Author `<INTENT_DIR>/intent.json` (pure metadata — `schemaVersion: 2`, no `fnBody`) and one `<INTENT_DIR>/metrics/<name>.ts` per metric (`export const fetchData: MetricFn`), writing each module from the SDK references and applying the Phase 3.5 cross-check. Implement exactly this approved plan:
>    - Project: dashboardName=`<NAME>`, routingName=`<ROUTING>`, projectDir=`<PROJECT_DIR>`, orgName=`<ORG>`, tenantName=`<TENANT>`, cloudUrl=`<CLOUD_URL>`, apiUrl=`<API_URL>`, timeRange=`<RANGE>`, clientId=`<CLIENT_ID or empty>`
>    - Widgets (one metric each): [per widget — name, tier, title, displayAs, presentation hints, and the SDK service/method it resolves to]
> 3. Run: `node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" "<INTENT_JSON_PATH>"`
> 4. On `METRICS_RETRY`, fix the named `src/metrics/*.ts` files using the SDK references + the reported errors, then re-run — at most 2 attempts, then drop the metric.
> 5. Return ONLY the milestone block defined in § "Build subagent — returns".

**Step 2 — Relay the subagent's returned block verbatim.** Add nothing else — no commentary about the subagent, no raw output, no mention of the files it wrote.

**Step 3 — Start the dev server as a background job in the MAIN thread** (the build script deliberately does not start it — a server spawned inside the script outlives the session and leaks). Run with the background option on the shell tool call (same mechanism as pre-warm):

```bash
cd "<PROJECT_DIR>" && npm run dev -- --port 57173
```

- If a dev-server background job from THIS session is already running for this project (e.g. after an incremental edit): do NOT start another — Vite hot-reloads; just open the URL.
- If the start fails with a port-in-use error: a stale server from an earlier session is still holding 57173 — tell the user and ask before killing anything (Windows: `netstat -ano | findstr :57173` then `taskkill /PID <pid> /F`; macOS/Linux: `lsof -ti:57173 | xargs kill`).

**Step 4 — Open `http://localhost:57173` in the browser.**

If the subagent reports `AUTH_MISSING` or a failure it couldn't recover, surface its message and stop (no server start).

---

## Build subagent — execution

> Everything in this section and the next is what the **build subagent** does. The main thread never runs these steps; it only spawns the subagent and relays its result.

**Step A — Author the inputs** (these writes stay inside you — they never reach the main thread):
- Write `<INTENT_DIR>/intent.json` — pure metadata: `schemaVersion: 2`, `dashboardName`, `routingName`, `projectDir`, `orgName`, `tenantName`, `cloudUrl`, `apiUrl`, `timeRange`, `clientId`, and a `metrics` array of metadata entries (NO `fnBody`).
- Write one `<INTENT_DIR>/metrics/<name>.ts` per metric — `export const fetchData: MetricFn = async (sdk) => { … }` written from the SDK references; import time windows from `@/lib/time` and `fetchAll` from `@/lib/paginate`; read-only methods only. Cross-check each against its documented example response (§ "Phase 3.5"). For a chart record-grain drill-down, also export `fetchDetail` and set `"detail": true`. For a **table row-click** drill-down, set `rowLink: { key: "<rowField>" }` on the metric and export `fetchDetailByKey(sdk, key, getToken)` (the clicked row's `<rowField>` arrives as `key`). For a KPI with a change badge, return `[{ value, previous }]` (two windows).

**Step B — Run the build script once.** Most events are silent — translate the rest to milestones for the return block.

**Silent (never report):** `PREWARM_START`, `PREWARM_DONE`, `SCAFFOLD_READY`, `ENV_WRITTEN`, `PARTIAL_BUILD_DETECTED`.

**Collect into milestones:**
- `WIDGET_READY:{"name":"X",...}` → a `✓ X` line
- `METRICS_PASS` → silent; build continues (no milestone needed)
- `TSC_PASS` → `✓ All code validated`
- `BUILD_RESULT.previewUrl` → the URL for the return block (the script does NOT start the server — the main thread does that after you return)

**Act on:**
- `METRICS_RETRY:{"files":[...],"errors":[...]}` → fix the named `src/metrics/<name>.ts` file(s) using the SDK references + reported errors, re-run. Max 2 attempts; if still failing, remove the metric from `intent.json` and its module file, re-run, and note it as dropped.
- `AUTH_MISSING` → stop; return the auth-missing result so the main thread can complete Phase 3.
- `PREWARM_FAILED:{"stderr":"..."}` → return a failure result noting dependency install failed.
- `BUILD_RESULT:{"success":true,...}` → success; assemble the return block.

Never put raw JSON, event names, bash/tsc/npm output in the return block.

## Build subagent — returns

On success, return exactly this block (nothing before or after):

```
  ✓ [Widget 1]
  ✓ [Widget 2]
  ✓ [Widget 3]
  ✓ All code validated

Your **[Dashboard Name]** is live at http://localhost:57173 🎉

The dashboard has [N] widgets: [comma-separated names].
Tell me what to change — I can add widgets, adjust time ranges, swap chart types, or deploy it to your team.
```

If some widgets were dropped after retries, add one line before the success line:
`  ⚠ Couldn't compile [names] — built the rest; re-add once we refine the query.`

On unrecoverable failure, return a one-line reason (e.g. `Dependency install failed — run npm ci in [projectDir]`) and nothing else.

The main thread relays this block verbatim, starts the dev server as a background job (Step 4), and opens the URL. Keep it warm — the user just got something real.
