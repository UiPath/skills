# Dashboard Build Plugin

Translates a natural language request into a running dashboard. By the time you read this, you have already loaded all reference docs and run the login + state check in parallel (per CAPABILITY.md). Do not re-read anything.

## Rules

1. Never read `build-dashboard.mjs` — the event protocol below is complete.
2. Never run `ls`, `find`, or directory exploration — paths are given explicitly.
3. Fire pre-warm silently the moment you know the project directory — user reads the plan while npm installs.
4. Show the plan in plain English — no API names, no tier labels, no metric IDs.
5. HALT after the plan — do not build until the user explicitly confirms.
6. Resolve `clientId` before building — without it the dashboard cannot log in.
7. Parse build script stdout line-by-line — missing a `T3_RETRY` exits with code 2.
8. On `BUILD_RESULT`: open `previewUrl` in the browser.

---

## Phase 1 — Preflight

You already have the `uip login status` response from the parallel blast. Extract from it:

- `orgName` ← `Data.Organization`
- `tenantName` ← `Data.Tenant`
- `cloudUrl` ← `Data.BaseUrl`

Derive `apiUrl` and read `tenantId` following `auth-context.md`.

Choose a project directory (e.g. `~/dashboards/<routing-name>`) and start pre-warm **now**:

```bash
mkdir -p <PROJECT_DIR> && cd <PROJECT_DIR> && npm ci --prefer-offline &
```

---

## Phase 2 — Plan

For each metric the user mentioned:

1. Check the hard-refuse list in `tier-resolution.md`. If matched: refuse that metric only and offer an alternative.
2. Classify the tier (T1 / T2 / T3) using the decision tree in `tier-resolution.md` and the catalog in `capability-registry.json`.
3. Build the complete `intent.json` (schema in `build-plan.md`).

Present the plan:

```
Here's your **[Dashboard Name]** — N widgets. Confirm to build, or tell me what to change.

• **[Widget name] ([time range])** — one sentence on what it shows and why it's useful
• ...

What you can do: "make it 7 days", "add a KPI for total errors", "remove the queue widget"
```

---

## Phase 3 — Approval gate

**HALT.** Do not proceed until the user confirms.

- User confirms → continue to Phase 4
- User requests a change → update `intent.json`, re-render the plan, HALT again
- User cancels → discard `intent.json`

---

## Phase 4 — External OAuth client

Every dashboard needs a UiPath external app for browser authentication (PKCE). Without a `clientId` the dashboard loads but shows an auth error immediately.

### Check if clientId is already set

```bash
node -e "
const intent = JSON.parse(require('fs').readFileSync('<INTENT_JSON_PATH>', 'utf8'))
process.exit(intent.clientId ? 0 : 1)
" && echo HAS_CLIENT || echo NEEDS_CLIENT
```

**HAS_CLIENT** → skip to Phase 5.

**NEEDS_CLIENT** → ask the user:

> "Your dashboard needs a UiPath OAuth app for authentication. Do you have an existing client ID, or should I create one?"

**If the user provides their own client ID:** write it into `intent.json`, continue to Phase 5.

**If the user wants one created:**

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:5173" \
  --redirect-uri "http://localhost:5174" \
  --redirect-uri "http://localhost:5175" \
  --user-scope "OR.Assets.Read,OR.Jobs,OR.Folders.Read,OR.Buckets.Read,OR.Execution.Read,OR.Tasks,OR.Queues.Read,OR.Users.Read,Insights,Insights.RealTimeData" \
  --output json
```

Read `ClientId` from the JSON response and write it into `intent.json`. Tell the user: "OAuth app created — building now."

**If the command fails:** direct the user to `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps` to create one manually. Do not proceed without a `clientId`.

---

## Phase 5 — Build

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" "<INTENT_JSON_PATH>"
```

Parse each line as it arrives:

| Event | Action |
|-------|--------|
| `PREWARM_START` | npm ci starting — no action |
| `PREWARM_DONE` | Dependencies ready |
| `PREWARM_FAILED:{"exitCode":N,"stderr":"..."}` | Surface error to user, stop |
| `SCAFFOLD_READY` | Scaffold copied |
| `ENV_WRITTEN` | Environment config written |
| `AUTH_MISSING:{"var":"clientId",...}` | Warn user — go back to Phase 4 |
| `WIDGET_READY:{"name":"X","index":N,"total":M}` | Print `✓ X ready (N/M)` |
| `T3_RETRY:{"widget":"X","errors":[...],"intentPath":"..."}` | Fix `fnBody` in `intent.json`, re-run (exit code 2) |
| `TSC_PASS` | Print `✓ TypeScript clean` |
| `PARTIAL_BUILD_DETECTED` | Prior build was interrupted — continuing |
| `SERVER_READY:{"port":N,"url":"..."}` | Save the URL |
| `BUILD_RESULT:{"success":true,...}` | Open `previewUrl` in browser |

On success:

> "Your dashboard is live at [url]. Tell me what to change — I can add widgets, adjust time ranges, or deploy it."
