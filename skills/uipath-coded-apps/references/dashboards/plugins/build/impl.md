# Dashboard Build Plugin

By the time you read this you have already loaded all docs, checked state, and fired pre-warm **and** `uip login status` in the background (per CAPABILITY.md). Login status is NOT needed for the plan — read its background result only when you build (Phase 1). The user is waiting for the plan.

## Rules

1. **Zero tool calls between user request and plan.** Everything internal runs in the parallel blast. The first thing the user sees is the plan.
2. **Zero tool calls between plan and build confirmation. Pure text HALT.** The build plan gate is deliberately text-only: do NOT use the question/option tool here — it reproducibly suppresses the plan rendering (the user gets options with no plan). The plan text ends with the confirm/change affordances; OAuth details are asked AFTER approval (Phase 3).
3. **The build runs in a subagent when one is available, else inline (Phase 4).** After confirmation, the main thread prints one "Building…" line. **Best effort: if the host agent already provides a sub-task/subagent mechanism (the `Task` tool in Claude Code; the equivalent in Codex/Gemini/others), use it automatically** — spawn a build subagent so the build command, events, tsc/npm output, and retries stay hidden, then relay its returned milestone block. **If no such mechanism exists, fall back to running the same build steps inline in the main thread** — the build and its output are identical; only the noise-hiding is lost. Subagent use is an optimization, never a hard requirement.
4. Never read `build-dashboard.mjs` — this file documents everything.
5. Never run directory exploration via any shell — `ls`, `find`, `dir`, `Get-ChildItem`, `tree`.

---

## Phase 1 — Preflight (read the background login-status result now)

`uip login status --output json` was fired in the background during plan presentation; by build time its result is ready. Read it now and extract:

- `orgName` ← `Data.Organization`
- `tenantName` ← `Data.Tenant`
- `cloudUrl` ← `Data.BaseUrl`

Verify `Data.Status === "Logged in"` — if not, stop and tell the user to run `uip login`. (This check is deferred to build time on purpose: login is only required to create the OAuth client and build, not to present the plan.)

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
- **For a chart or drill-down KPI, name what clicking it reveals** — a short `click → …` clause (the record grain behind the chart: "click → the individual faulted runs", "click → each policy evaluation"). Use the registry entry's `detailRecipe` for the wording. Omit the clause for a `noDetail` chart (no drill-down) and for plain KPIs/tables
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
- 🔢 **KPI card** — "as a single headline number". Add "with a vs-previous-period change badge" ONLY if the metric module returns `{ value, previous }` — value over the dashboard window, previous over the equal-length prior window via `priorWindow(start, end)` (works for any time range). A plain KPI returns `{ value }` and shows no badge — don't promise a badge you won't compute. **Cataloged KPIs with a feasible record query default to a drill-down** (active-agents, success-rate, agent-units, governance-violations) — name what clicking reveals ("click → the active agents") and write the `fetchDetail` the registry `detailRecipe` describes. For a T3 KPI, set `detail: true` + export `fetchDetail` to make it clickable; set `detail: false` to suppress a defaulted-on one.
- 📈 **Line or area chart** — "as an area/line trend over time, with a headline [total/latest/average] and a vs-previous change". Add the `click → …` record-grain clause unless it's a `noDetail` chart.
- 📈 **Rate chart** — "as a percentage line over time with an overall headline" (a ratio: numerator ÷ denominator per period)
- 📊 **Bar or donut chart** — "as a bar chart" / "as a donut split by category". Add the `click → …` clause (the records behind the split) unless `noDetail`.
- 📋 **Table or ranked list** — "as a sortable table with columns [A, B, C]", or "ranked worst/highest-first". To make rows clickable (drill into the clicked entity), set `rowLink: { key: "<rowField>" }` and export `fetchDetailByKey(sdk, key, getToken)` — generates a `/<widget>/:key` detail page.
- 🔷 **Multi-line chart** — "as multiple lines over time (e.g. P50/P95)". Add the `click → …` clause unless `noDetail`.

> **Governance violations are GATED.** Only propose the runtime-compliance widgets (violations by
> standard/rule/hook, agents-by-violations, recent-violations, per-agent compliance report, rule-evaluation
> views) when the prompt signals runtime-governance intent — "governance/policy violation(s)", "compliance",
> a standard/pack reference (`ISO 42001`, `A.8.4`, "standard", "pack"), or runtime-governance terms. Then read
> `sdk/governance-traces.md` and build the modules on `AgentTraces.getGovernanceDecisions` /
> `getGovernanceSummary` (SDK ≥ 1.5.1). NEVER add them to a plain agent-health/ops dashboard. They need an
> **org-admin** caller — a 403 means the user's account lacks governance access (say so; the rest of the
> dashboard still builds). Widgets honor the dashboard time range like any other metric.

> **Promise only what the scaffold can render.** The bullets above are the complete set of buildable affordances. Before writing a feature into the plan, confirm it maps to one of them: KPI delta → `{value, previous}`; row drill-down → `rowLink` + `fetchDetailByKey`. If a prompt needs something not listed (a bespoke interaction, a custom layout), say so in the plan ("this needs a template extension") rather than promising it and silently dropping it during the build.

**Example plan:**

```
Here's your **Agent Operations Dashboard** — 4 widgets ready to build.

🔢 **Active Agents** — agents that ran at least once in the last 30 days, so you can see fleet utilisation at a glance, shown as a single headline number
📋 **Agent Health** (30 days) — where to focus your attention, shown as a sortable table ranked worst-first, with columns for agent, health score, and last incident
📈 **Memory Calls** (7 days) — agent memory access volume so you can spot unusual activity early, shown as an area-chart trend over time with a running total and a vs-previous-week change
📊 **Governance Verdicts** (7 days) — how policy enforcement is splitting across your agents, shown as a donut split by allow / deny / no-op; click → each individual policy evaluation (agent, result, hook, time)

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

Optional `"template": true` — build straight into the **ejected** regime (full-source, agent-edited; no compiler regen). Use only when authoring a distributable template from scratch; a normal dashboard omits it and stays `compiler-managed`. Pair with the deploy plugin's `--pack-template` step (Step 6b) to ship source + `dist` as one artifact. See [primitives/customization.md](../../primitives/customization.md#regimes-compiler-managed-vs-ejected).

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

**Detail views** — the drill-down must show records, not the chart's buckets:
- **Every chart module MUST `export const fetchDetail: MetricFn`** — the record-grain query (individual rows behind the chart). The build infers the drill-down from this export (no `detail` flag on charts) and **hard-fails with `CHART_DETAIL_MISSING`** if it's missing. For cataloged charts, the registry entry's `detailRecipe` is the exact SDK call — copy it. The only exception is a registry `"noDetail": true` chart (endpoint has no record data): no `fetchDetail`, no drill-down, non-clickable card.
- **KPI drill-down:** set `"detail": true` on the kpi-card metric + export `fetchDetail` → clickable card + record view. Use for event-counting KPIs (errors/failures/violations/denials); a scalar KPI (rate %, total) needs none.
- `detailColumns` — array of `{ key, label, align?, format?, color? }`. `format`: `number` | `percent` | `duration` | `timeAgo` | `text`. `color`: `goodHigh` | `goodLow` (threshold colouring). Cataloged metrics ship these in the registry; set them yourself for T3. The build compiles them into formatted/coloured cells.
- `detailSortKey` — raw field to sort on (e.g. an ISO `startTime`), so chronological order is correct even when a column renders a friendly label.

Full detail-view contract (record grain, toRows, anti-patterns): `references/dashboards/primitives/detail-views.md`.

**Rich drill-downs (`detailView`)** — a metric with `rowLink.key` or `detail: true` can declare `detailView: { widgets: [...] }` to render multiple sub-widgets (charts + tables) on the detail page. Each widget specifies `displayAs`, `title`, `source` (key into the named-source map), and chart `xKey`/`yKey` or table `columns`. When `detailView` is present, the module's `fetchDetailByKey` / `fetchDetail` must return a named-source map (`{ rows, byHook, byRule, … }`) instead of a bare array.

> **Rich drill-downs are opt-in.** Add a `detailView` only when the user asks to click an entity and *see charts/insights* about it (e.g. 'let me click an agent and see its violation breakdown'). Default detail views stay a single records table. When you add one, the module's detail fetch must return a named-source map whose keys match each sub-widget's `source`.

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
  const rows = (await new Jobs(sdk).getAll({ filter: "State eq 'Faulted'" }))?.items ?? []
  const byDate: Record<string, number> = {}
  for (const j of rows) { const d = String(j.createdTime).slice(0, 10); byDate[d] = (byDate[d] ?? 0) + 1 }
  return Object.entries(byDate).sort().map(([date, count]) => ({ date, count }))
}

export const fetchDetail: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  return ((await new Jobs(sdk).getAll({ filter: "State eq 'Faulted'", orderby: 'CreationTime desc' }))?.items ?? []).map(x => ({ ...x }))
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
- Otherwise → ask ONE short structured-choice question (SKILL.md Rule 18 — this is a short turn, safe for the question tool):

  *"How should I set up the OAuth app this dashboard signs in with?"*

  | Option | Meaning |
  |--------|---------|
  | **Create one for me (Recommended)** | Run the external-app create command, then build |
  | **I'll paste an existing client ID** | Wait for the ID, write it into intent.json, then build |

  A free-text reply (including a pasted ID, or a late change request) always remains valid and takes precedence.

Never re-ask for anything the user already provided. The same pattern applies to deploy (see `plugins/deploy/impl.md`): present the deploy plan as text → free-text confirm → then the pin question only if the confirmation didn't already settle it.

**Creating the OAuth app:** Run this single command. `--redirect-uri` takes **comma-separated** values — register BOTH the local dev server and the org portal base, so login works in dev and after deploy:

- `http://localhost:25173` — local dev server
- `<CLOUD_URL>/<ORG>/portal_` — deployed app base; `<CLOUD_URL>` and `<ORG>` are the `cloudUrl` (`Data.BaseUrl`) and `orgName` (`Data.Organization`) extracted in Phase 1, so they track the logged-in environment (e.g. `https://alpha.uipath.com/acme/portal_`)

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:25173,<CLOUD_URL>/<ORG>/portal_" \
  --user-scope "OR.Assets,OR.Jobs,OR.Folders,OR.Buckets,OR.Execution,OR.Tasks,OR.Queues,OR.Users,Insights,Insights.RealTimeData,Traces.Api,PIMS" \
  --output json
```

The runtime-governance metrics (`AgentTraces.getGovernanceDecisions`/`getGovernanceSummary`) need only the Insights scopes; `Traces.Api` stays registered for span-level drill-downs (`Traces.getById` in fetchDetail recipes). Read `ClientId` from the JSON response and carry it as the plan's `clientId` (the build subagent writes it into intent.json). Tell the user: "OAuth app created — building now."

**If the command fails** (invalid scopes for this environment): retry with the minimal set:

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:25173,<CLOUD_URL>/<ORG>/portal_" \
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
return ((await new Jobs(sdk).getAll({ filter: "SourceType eq 'Agent'" }))?.items ?? []).map(x => ({ ...x }))

// ✓ Correct — OData filter uses the raw field name ProcessType
return ((await new Jobs(sdk).getAll({ filter: "ProcessType eq 'Agent'" }))?.items ?? []).map(x => ({ ...x }))
// (client-side, the mapped field is packageType: j.packageType === 'Agent')
```

If a metric's correctness depends on data you genuinely can't determine from the references, prefer a simpler, well-documented query over a guess — and tell the user what you simplified.

**After cross-checking:** the build subagent writes the verified `metrics/<name>.ts` modules and `intent.json` itself (Phase 4). No metric files or `intent.json` are written in the main thread — so none of those file edits surface to the user.

---

## Offer-on-detect upgrade

If a build or edit against an existing project emits `UPGRADE_AVAILABLE:{from,to}`, the dashboard was built on an older scaffold than the one now shipped. Tell the user a newer dashboard scaffold is available and offer to upgrade — same plan→confirm ethos, **never automatic**. On confirm, run a lone `UPGRADE` edit-intent (`{ projectDir, op: "UPGRADE" }`) — it preserves their metrics (`intent.json` + `src/metrics`) and regenerates the app against the current scaffold. See `primitives/incremental-editor.md`.

---

## The starter-kit archive

The skill ships ONE artifact — `assets/fixtures/governance-dashboard-starter-kit.tar.gz` — and no scaffold source. The archive bundles the React scaffold (at its root) plus the widget generator templates under `_gen/widgets/` and a version pointer `_gen/starter-kit.json`. The build reads templates from `_gen/widgets` and never ships them into the final app.

> **Extracting the kit (the agent does this).** Before building, extract the archive into the project dir with the OS `tar` — built into Windows 10+, macOS, and Linux (one command, no per-OS variants). **Pass the archive on stdin (`-f -`), not as a path argument:**
> ```
> mkdir -p "<PROJECT_DIR>" && tar -xz -C "<PROJECT_DIR>" -f - < "<ARCHIVE>"
> ```
> `build-dashboard.mjs` verifies the kit landed and fails loud with the exact command if not. `<ARCHIVE>` is `<SKILL_BASE_DIR>/assets/fixtures/governance-dashboard-starter-kit.tar.gz`.
>
> **Why stdin, not `tar -xzf "<ARCHIVE>"`:** GNU tar (the `tar` on PATH in Git Bash / MSYS on Windows) reads an archive path containing a drive colon — `C:\…` — as a remote `host:path` and dies with `tar: Cannot connect to C: resolve failed`. `--force-local` fixes GNU tar but is rejected by bsdtar (Windows `System32\tar.exe`, macOS), so it isn't portable. Feeding the archive on stdin sidesteps the colon entirely and works on GNU tar **and** bsdtar. Do not "simplify" this back to `-f "<ARCHIVE>"`.

**Source of truth:** the scaffold + widget templates + packer live in the `apps-dev-tools` repo (`uipath-dashboard-starter-kit/`). Maintainers edit there and run `node publish.mjs` to re-pack and copy the refreshed `.tar.gz` into this skill (the version ships inside the archive at `_gen/starter-kit.json` — no separate version file). The skill is a pure consumer.

---

## Phase 4 — Build (subagent if available, else inline)

To keep the experience seamless, Phase 4 **prefers** to execute inside a **build subagent** — a sub-task spawned via the host agent's mechanism (the `Task` tool in Claude Code; the equivalent sub-agent feature in Codex, Gemini, and others). When that mechanism is available, use it automatically: the subagent **authors `intent.json` and the metric modules**, runs the build script, handles the type-error retry loop, and returns one short milestone block. Every file write, the bash command, the raw event stream, tsc/npm output, and retries stay inside the subagent — none surface in the main thread. **The user then sees only your one-line "Building…" and the final milestone — never the `intent.json` or `metrics/*.ts` writes.**

**Inline fallback (no sub-task mechanism):** if the host has no subagent/sub-task feature, perform the exact same steps yourself in the main thread — author the inputs and run the build per §§ "Build subagent — execution"/"returns". The build is identical; the only difference is that the file writes and build output are visible. This is the worst-case path, not a failure — do NOT abort or ask the user to enable subagents.

`SKILL_BASE_DIR` is the directory shown in "Base directory for this skill:" from your activation message — it contains `SKILL.md` and ends in `/skills/uipath-coded-apps`. `INTENT_DIR` is the directory the subagent writes `intent.json` + `metrics/` into; `INTENT_JSON_PATH` is `<INTENT_DIR>/intent.json`.

**Step 1 — Show one line, then build.** Print only:

```
Building **[Dashboard Name]**…
```

**If a sub-task mechanism is available (preferred):** do NOT write `intent.json` or any `metrics/*.ts` in the main thread — the subagent writes them, so those edits stay hidden. Spawn the build subagent with the prompt below (use your host agent's sub-task mechanism — e.g. the `Task` tool in Claude Code), pasting the APPROVED PLAN (it is the subagent's authoring spec — give it everything needed to write the files).

**If no sub-task mechanism is available (inline fallback):** skip the spawn and do the subagent's job yourself — follow §§ "Build subagent — execution" and "returns" directly in the main thread (author `intent.json` + `metrics/*.ts`, extract the kit, run the build script, handle the retry loop), then continue to Step 3. The file writes and build output will be visible; that is acceptable.

The build subagent prompt:

> You are the dashboard build executor. You NEVER surface raw output or file edits — your final message is the only thing shown.
> 1. Read `<SKILL_BASE_DIR>/references/dashboards/plugins/build/impl.md` §§ "Phase 3.5" and "Build subagent — execution" and follow them exactly.
> 2. Author `<INTENT_DIR>/intent.json` (pure metadata — `schemaVersion: 2`, no `fnBody`) and one `<INTENT_DIR>/metrics/<name>.ts` per metric (`export const fetchData: MetricFn`), writing each module from the SDK references and applying the Phase 3.5 cross-check. Implement exactly this approved plan:
>    - Project: dashboardName=`<NAME>`, routingName=`<ROUTING>`, projectDir=`<PROJECT_DIR>`, orgName=`<ORG>`, tenantName=`<TENANT>`, cloudUrl=`<CLOUD_URL>`, apiUrl=`<API_URL>`, timeRange=`<RANGE>`, clientId=`<CLIENT_ID or empty>`
>    - Widgets (one metric each): [per widget — name, tier, title, displayAs, presentation hints, and the SDK service/method it resolves to]
> 3. Extract the starter kit into `<PROJECT_DIR>` with the OS `tar`, feeding the archive on stdin (`tar -xz -C "<PROJECT_DIR>" -f - < "<ARCHIVE>"`; see § "The starter-kit archive" for why stdin), then run: `node "<SKILL_BASE_DIR>/assets/scripts/dashboards/build-dashboard.mjs" "<INTENT_JSON_PATH>"` (it verifies the kit and prints the exact extract command if missing)
> 4. On `METRICS_RETRY`, fix the named `src/metrics/*.ts` files using the SDK references + the reported errors, then re-run — at most 2 attempts, then drop the metric.
> 5. Return ONLY the milestone block defined in § "Build subagent — returns".

**Step 2 — Relay the subagent's returned block verbatim.** Add nothing else — no commentary about the subagent, no raw output, no mention of the files it wrote.

**Step 3 — Start the dev server as a background job in the MAIN thread** (the build script deliberately does not start it — a server spawned inside the script outlives the session and leaks). Run with the background option on the shell tool call (same mechanism as pre-warm):

```bash
cd "<PROJECT_DIR>" && npm run dev -- --port 25173
```

- If a dev-server background job from THIS session is already running for this project (e.g. after an incremental edit): do NOT start another — Vite hot-reloads; just open the URL.
- If the start fails with a port-in-use error: a stale server from an earlier session is still holding 25173 — tell the user and ask before killing anything (Windows: `netstat -ano | findstr :25173` then `taskkill /PID <pid> /F`; macOS/Linux: `lsof -ti:25173 | xargs kill`).

**Step 4 — Open `http://localhost:25173` in the browser.**

If the subagent reports `AUTH_MISSING` or a failure it couldn't recover, surface its message and stop (no server start).

---

## Build subagent — execution

> Everything in this section and the next is what the **build subagent** does. The main thread never runs these steps; it only spawns the subagent and relays its result.

**Step A — Author the inputs** (these writes stay inside you — they never reach the main thread):
- Write `<INTENT_DIR>/intent.json` — pure metadata: `schemaVersion: 2`, `dashboardName`, `routingName`, `projectDir`, `orgName`, `tenantName`, `cloudUrl`, `apiUrl`, `timeRange`, `clientId`, and a `metrics` array of metadata entries (NO `fnBody`).
- Write one `<INTENT_DIR>/metrics/<name>.ts` per metric — `export const fetchData: MetricFn = async (sdk) => { … }` written from the SDK references; import time windows from `@/lib/time` and `fetchAll` from `@/lib/paginate`; read-only methods only. Cross-check each against its documented example response (§ "Phase 3.5"). For a chart record-grain drill-down, also export `fetchDetail` and set `"detail": true`. For a **table row-click** drill-down, set `rowLink: { key: "<rowField>" }` on the metric and export `fetchDetailByKey(sdk, key, getToken)` (the clicked row's `<rowField>` arrives as `key`). For a KPI with a change badge, return `[{ value, previous }]` (two windows).

**Step B — Extract the kit, then run the build script once.** First extract `<SKILL_BASE_DIR>/assets/fixtures/governance-dashboard-starter-kit.tar.gz` into `<PROJECT_DIR>` with the OS `tar`, feeding the archive on stdin (`tar -xz -C … -f - < "<ARCHIVE>"`; § "The starter-kit archive"). Then run the build script. Most events are silent — translate the rest to milestones for the return block.

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

Your **[Dashboard Name]** is live at http://localhost:25173 🎉

The dashboard has [N] widgets: [comma-separated names].
Tell me what to change — I can add widgets, adjust time ranges, swap chart types, or deploy it to your team.
```

If some widgets were dropped after retries, add one line before the success line:
`  ⚠ Couldn't compile [names] — built the rest; re-add once we refine the query.`

On unrecoverable failure, return a one-line reason (e.g. `Dependency install failed — run npm ci in [projectDir]`) and nothing else.

The main thread relays this block verbatim, starts the dev server as a background job (Step 4), and opens the URL. Keep it warm — the user just got something real.
