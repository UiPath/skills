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

You have the `uip login status` response. Extract:

- `orgName` ← `Data.Organization`
- `tenantName` ← `Data.Tenant`
- `cloudUrl` ← `Data.BaseUrl`

Derive `apiUrl` and read `tenantId` per `auth-context.md`.

Pre-warm is already running at `~/dashboards/<ROUTING_NAME>`. Do not re-fire it.

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
→ "make the error chart 7 days"
→ "add a KPI showing total runs today"
→ "swap the table for a bar chart"
→ "remove the latency widget"
```

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
```

---

## Phase 3 — Approval gate (zero tool calls)

**HALT.** Output only text. No tool calls.

- User confirms → write intent.json, continue to Phase 4
- User requests a change → update the plan in your response, HALT again
- User cancels → discard

---

## Phase 4 — External OAuth client (0–1 tool call)

Every dashboard needs a `clientId` for PKCE auth. Without it the browser shows an auth error.

### Check intent.json for existing clientId

If the user has given a client ID previously (stored in your context) → write it directly into intent.json. Skip the bash check.

If unknown, run once:

```bash
node -e "
const intent = JSON.parse(require('fs').readFileSync('<INTENT_JSON_PATH>', 'utf8'))
process.exit(intent.clientId ? 0 : 1)
" && echo HAS_CLIENT || echo NEEDS_CLIENT
```

**HAS_CLIENT** → skip to Phase 5.

**NEEDS_CLIENT** → ask concisely:

> "One quick thing — your dashboard needs a UiPath OAuth app for authentication. Do you have an existing client ID, or should I create one for you?"

**If user provides their client ID:** write it into intent.json, go to Phase 5.

**If user says create one:**

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:57173" \
  --user-scope "OR.Assets.Read,OR.Jobs,OR.Folders.Read,OR.Buckets.Read,OR.Execution.Read,OR.Tasks,OR.Queues.Read,OR.Users.Read,Insights,Insights.RealTimeData" \
  --output json
```

Read `ClientId` from the JSON response. Write it into intent.json. Respond: "Done — building now."

**If command fails:** direct user to `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps`. Do not proceed without `clientId`.

---

## Phase 5 — Build (one tool call)

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

| Event | Show to user |
|-------|-------------|
| `PREWARM_DONE` | (silent — already running) |
| `SCAFFOLD_READY` | (silent) |
| `ENV_WRITTEN` | (silent) |
| `WIDGET_READY:{"name":"X",...}` | `  ✓ X` (one line per widget) |
| `T3_RETRY:{...}` | `  ↻ [Name] — refining query…` then retry |
| `TSC_PASS` | `  ✓ TypeScript clean` |
| `AUTH_MISSING:{...}` | Pause, tell user to complete Phase 4 |
| `PARTIAL_BUILD_DETECTED` | `  ↻ Resuming previous build…` |
| `SERVER_READY:{...}` | `Opening your dashboard at [url]` |
| `BUILD_RESULT:{...}` | Open previewUrl in browser |
| `PREWARM_FAILED:{...}` | "Dependency install failed — [stderr excerpt]. Try running `npm ci` manually in [dir]." |

### Success message

After `BUILD_RESULT`, open the URL and respond:

```
Your **[Dashboard Name]** is live at http://localhost:57173 🎉

The dashboard has [N] widgets: [comma-separated names].
Tell me what to change — I can add widgets, adjust time ranges, swap chart types, or deploy it to your team.
```

Keep it warm and action-oriented. The user just got something real — meet that moment.
