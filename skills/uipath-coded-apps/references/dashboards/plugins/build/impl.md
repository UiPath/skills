# Dashboard Build Plugin

By the time you read this you have already loaded all docs, run login, checked state, and fired pre-warm in the background (per CAPABILITY.md). The user is waiting for the plan.

## Rules

1. **Zero tool calls between user request and plan.** Everything internal runs in the parallel blast. The first thing the user sees is the plan.
2. **Zero tool calls between plan and build confirmation. Pure text HALT.** The build plan gate is deliberately text-only: do NOT use the question/option tool here — it reproducibly suppresses the plan rendering (the user gets options with no plan). The plan text ends with the confirm/change affordances; OAuth details are asked AFTER approval (Phase 3).
3. **The build runs in a subagent (Phase 4).** After confirmation, the main thread prints one "Building…" line, spawns the build subagent via the `Task` tool, and relays its returned milestone block. The build command, events, tsc/npm output, and retries stay inside the subagent.
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

**SDK validation (do this before writing the plan):** For every requested metric, apply the three-step check in `tier-resolution.md § SDK validation`. Every metric in the plan must be backed by a method in the SDK service reference. Metrics with no SDK path are refused inline (strikethrough + alternative). Write `intent.json` in memory (do not save it yet). Then output the plan.

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
→ "add a KPI for faulted jobs"
→ "remove the consumption widget"
```

The plan message ends there — no OAuth talk in the plan, no tool calls in the plan response. Setup details (client ID) are collected AFTER the user approves the plan, in Phase 3.

> **The plan response is text-only by design.** Never put a question/option tool call in the same response as the plan — live runs showed it reliably replaces the plan with a bare options list (the user approves widgets they never saw). Structured-choice questions fire only on later, short turns: the post-approval OAuth question (Phase 3), intent disambiguation, and the deploy pin choice.

**Widget type icons:**
- 🔢 KPI card
- 📈 Line or area chart
- 📊 Bar or donut chart
- 📋 Table or ranked list
- 🔷 Multi-line chart (e.g. P50/P95)

**Example plan:**

```
Here's your **Agent Operations Dashboard** — 4 widgets ready to build.

🔢 **Active Agents** — count of agents that ran at least once in the last 30 days, so you can see fleet utilisation at a glance
📋 **Agent Health** (30 days) — agents ranked by health score, worst first, so you know where to investigate
📈 **Memory Calls** (7 days) — agent memory access volume as a trend, to spot unusual activity early
📊 **Governance Verdicts** (7 days) — allow/deny breakdown of policy enforcement across your agents

Confirm to build, or tell me what to change:
→ "make all charts 7 days"
→ "add agent consumption"
→ "remove the governance donut"
→ "show memory calls as a table instead"
```

> If the user asks for agent error/latency **trends**: those have no SDK endpoint — refuse inline per `tier-resolution.md § T0` and offer `agent-health` or a Jobs-based trend instead.

### intent.json schema (write to disk in Phase 4 after confirmation)

```json
{
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
      "fnBody": "...", "valueField": "count", "valueLabel": "items"
    }
  ]
}
```

Routing name: `<kebab-name>-<4-char-random>`. Set once at plan time. Never changes.

### Presentation fields — make widgets read like a real dashboard

Charts and tables render shallow without these. Set them on each metric (registry fills defaults for cataloged metrics; you set them for T3). All optional except where noted.

**Chart metrics** (`line-chart`, `area-chart`, `bar-chart`, `donut-chart`):
- `headlineMode` — how the big number is computed from the series: `sum` (totals — default), `avg` (rates/latency), `latest`, `max`, `min`, `count`. **Never leave a count-trend on the implicit last-point value.**
- `deltaPolarity` — whether an increase is good or bad, drives the badge colour: `up-good` (e.g. completions), `up-bad` (e.g. errors), `neutral`. The build computes the actual % change.
- `subtitle` — one line of context (e.g. `"Agent runs — last 24h"`). Omit to auto-fill the time window.
- `yKey` / `xKey` — the value and axis fields in your `fnBody` rows.

**Rate / percentage metric** (`displayAs: "rate-chart"`): for ratios like error rate = faulted ÷ total.
- `fnBody` returns rows carrying **both** a numerator and denominator per bucket, e.g. `[{ date, faulted, total }]`.
- `rateNum` / `rateDen` (**required**) — those field names (`"faulted"`, `"total"`). The build plots num/den % per bucket, headline = overall %, delta in `pp`.

**Detail views** (any chart) — the drill-down must show records, not the chart's buckets:
- `detailFnBody` — a **record-grain** query (the individual rows behind the chart, e.g. each faulted job). Falls back to the chart's `fnBody` if omitted (shows buckets — avoid).
- `detailColumns` — array of `{ key, label, align?, format?, color? }`. `format`: `number` | `percent` | `duration` | `timeAgo` | `text`. `color`: `goodHigh` | `goodLow` (threshold colouring). The build compiles these into formatted/coloured cells.
- `detailSortKey` — raw field to sort on (e.g. an ISO `startTime`), so chronological order is correct even when a column renders a friendly label.

Full detail-view contract (record grain, toRows, anti-patterns): `references/dashboards/primitives/detail-views.md`.

Example T3 chart with full presentation:

```json
{
  "name": "faulted-jobs-trend", "tier": "T3", "title": "Faulted Jobs",
  "displayAs": "area-chart", "xKey": "date", "yKey": "count",
  "headlineMode": "sum", "deltaPolarity": "up-bad", "subtitle": "Faulted jobs — last 7 days",
  "fnBody": "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst rows = (await new Jobs(sdk as never).getAll({ filter: \"State eq 'Faulted'\" }))?.items ?? []\nconst byDate: Record<string, number> = {}\nfor (const j of rows) { const d = String(j.createdTime).slice(0,10); byDate[d] = (byDate[d] ?? 0) + 1 }\nreturn Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))",
  "detailFnBody": "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nreturn (await new Jobs(sdk as never).getAll({ filter: \"State eq 'Faulted'\", orderby: 'CreationTime desc' }))?.items ?? []",
  "detailColumns": [
    { "key": "processName", "label": "Process" },
    { "key": "state", "label": "State" },
    { "key": "createdTime", "label": "Started", "format": "timeAgo" }
  ],
  "detailSortKey": "createdTime"
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
- Confirmation already contains a client ID → write it into intent.json, continue to Phase 4
- Confirmation already says to create one (e.g. "build it, create the app") → create the OAuth app (below), continue to Phase 4
- `clientId` already in intent.json from a prior session → continue to Phase 4, ask nothing
- Otherwise → ask ONE short structured-choice question (SKILL.md Rule 17 — this is a short turn, safe for the question tool):

  *"How should I set up the OAuth app this dashboard signs in with?"*

  | Option | Meaning |
  |--------|---------|
  | **Create one for me (Recommended)** | Run the external-app create command, then build |
  | **I'll paste an existing client ID** | Wait for the ID, write it into intent.json, then build |

  A free-text reply (including a pasted ID, or a late change request) always remains valid and takes precedence.

Never re-ask for anything the user already provided. The same pattern applies to deploy (see `plugins/deploy/impl.md`): present the deploy plan as text → free-text confirm → then the pin question only if the confirmation didn't already settle it.

**Creating the OAuth app:** Run this single command:

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

## Phase 3.5 — Cross-check each fnBody against the documented response

`tsc` validates the *shape* of a query (do the fields exist?) but never its *meaning* (does this filter actually match the rows the user wants?). A query can compile green and return zero rows — the most common way a dashboard ships empty, because the agent filtered on a plausible-but-wrong field.

You wrote each `fnBody` from the SDK references. Before committing, cross-check every one against the **Example response** and **semantics notes** in the relevant `references/sdk/*.md` file (already loaded in the parallel blast). For each metric, confirm:

1. **The field you filter or read on appears in the example response** — with the value you expect. Not just "the field exists in the type" (both `sourceType` and `packageType` exist) — the example shows the real *value*.
2. **No semantics note warns against your choice.** The references flag the traps types can't express.
3. **Your return shape matches the example** — `.items` vs `.data` vs a top-level array, and the exact field names you map to `xKey`/`yKey`/columns.

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

**After cross-checking:** the verified `fnBody` strings go into intent.json in Phase 4.

---

## Phase 4 — Build (runs in a build subagent)

To keep the experience seamless, Phase 4 executes inside a **build subagent** (the `Task` tool). The subagent runs the build script, handles the type-error retry loop, and returns one short milestone block. The bash command, raw event stream, tsc/npm output, and retries all stay inside the subagent — they never surface in the main thread.

`SKILL_BASE_DIR` is the directory shown in "Base directory for this skill:" from your activation message — it contains `SKILL.md` and ends in `/skills/uipath-coded-apps`.

**Step 1 — Write `intent.json` to disk** (the verified version from Phase 3.5).

**Step 2 — Show one line, then spawn the build subagent.** Print only:

```
Building **[Dashboard Name]**…
```

Then call the `Task` tool with this prompt (substitute the two paths):

> You are the dashboard build executor. You NEVER surface raw output — your final message is the only thing shown.
> 1. Read `<SKILL_BASE_DIR>/references/dashboards/plugins/build/impl.md` § "Build subagent — execution" and follow it exactly.
> 2. Run: `node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" "<INTENT_JSON_PATH>"`
> 3. On `T3_RETRY`, fix the named widgets' `fnBody` in `<INTENT_JSON_PATH>` using the SDK references, then re-run — at most 2 attempts, then drop the widget.
> 4. Return ONLY the milestone block defined in § "Build subagent — returns".

**Step 3 — Relay the subagent's returned block verbatim**, then open the preview URL in the browser. Add nothing else — no commentary about the subagent, no raw output.

If the subagent reports `AUTH_MISSING` or a failure it couldn't recover, surface its message and stop.

---

## Build subagent — execution

> Everything in this section and the next is what the **build subagent** does. The main thread never runs these steps; it only spawns the subagent and relays its result.

Run the build script once. Most events are silent — translate the rest to milestones for the return block.

**Silent (never report):** `PREWARM_START`, `PREWARM_DONE`, `SCAFFOLD_READY`, `ENV_WRITTEN`, `PARTIAL_BUILD_DETECTED`.

**Collect into milestones:**
- `WIDGET_READY:{"name":"X",...}` → a `✓ X` line
- `TSC_PASS` → `✓ All code validated`
- `SERVER_READY:{"url":"..."}` → capture the URL

**Act on:**
- `T3_RETRY:{"widgets":[...],"errors":[...]}` → fix each widget's `fnBody` in intent.json (use the SDK references + the tsc errors), re-run. Max 2 attempts; if a widget still fails, remove it from intent.json, re-run, and note it as dropped.
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

The main thread relays this block verbatim and opens the URL. Keep it warm — the user just got something real.
