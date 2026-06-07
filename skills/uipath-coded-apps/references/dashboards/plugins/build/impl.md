# Dashboard Build Plugin

Implements the `build` action from `CAPABILITY.md`. Translates a natural language request into a running dashboard.

## Critical Rules

1. Read `primitives/tier-resolution.md` before classifying any metric.
2. Write `intent.json` with compact fields only — never full TypeScript except T3 `fnBody`.
3. Fire pre-warm (`npm ci`) silently BEFORE showing the plan — user reads the plan while npm installs.
4. Show the plan in plain English — no API names, no tier labels, no jargon.
5. HALT after the plan — do not build until the user explicitly confirms.
6. Resolve `clientId` before building — a missing client ID means the dashboard cannot log in.
7. Parse build script stdout line by line — each `WIDGET_READY` event prints one progress tick.
8. On `T3_RETRY`: update `fnBody` in `intent.json` and re-run the build script.
9. On `BUILD_RESULT`: open `previewUrl` in the browser.
10. Never commit generated dashboard files.

---

## Phase 0 — Check for existing dashboard

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

- `INCREMENTAL` → follow `primitives/incremental-editor.md`
- `FRESH` → continue to Phase 1

---

## Phase 1 — Load reference docs

Read all three in **one parallel message block**:

1. `primitives/auth-context.md`
2. `primitives/tier-resolution.md`
3. `aesthetic/layout-patterns.md`

---

## Phase 2 — Preflight

```bash
uip login status --output json
```

From the response, extract `orgName`, `tenantName`, `cloudUrl`. Derive `apiUrl` and read `tenantId` following `auth-context.md`.

Start pre-warm silently (user never sees this):

```bash
cd <PROJECT_DIR> && npm ci --prefer-offline &
```

---

## Phase 3 — Plan

For each metric the user mentioned:

1. Check the hard-refuse list in `tier-resolution.md`. If matched: refuse that metric only (not the whole dashboard) and offer an alternative.
2. Classify the tier (T1 / T2 / T3) using the decision tree in `tier-resolution.md`.
3. Build the complete `intent.json` (schema in `build-plan.md`).

Present the plan to the user:

```
Here's your **[Dashboard Name]** — N widgets. Confirm to build, or tell me what to change.

• **[Widget 1 name] ([time range])** — one sentence on what it shows and why it's useful
• **[Widget 2 name] ([time range])** — ...

What you can do: "make it 7 days", "add a KPI for total errors", "remove the queue widget"
```

---

## Phase 4 — Approval gate

**HALT.** Do not proceed until the user confirms.

- User confirms → continue to Phase 4.5
- User requests a change → update `intent.json`, re-render the plan, HALT again
- User cancels → discard `intent.json`

---

## Phase 4.5 — External OAuth client

Every dashboard needs an external app registered in UiPath to handle browser authentication (PKCE flow). Without a `clientId` the dashboard loads but immediately shows an auth error.

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

### If the user provides their own client ID

Update `clientId` in `intent.json` with the value they gave. Continue to Phase 5.

### If the user wants one created

```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:5173" \
  --redirect-uri "http://localhost:5174" \
  --redirect-uri "http://localhost:5175" \
  --user-scope "OR.Assets.Read,OR.Jobs,OR.Folders.Read,OR.Buckets.Read,OR.Execution.Read,OR.Tasks,OR.Queues.Read,OR.Users.Read,Insights,Insights.RealTimeData" \
  --output json
```

The response contains a `ClientId` field — read it from the JSON output and write it to `intent.json`.

Tell the user: "OAuth app created — client ID saved. Building your dashboard now."

### If the command fails

Tell the user to create an app manually:

1. Open `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps`
2. Create a non-confidential app with the redirect URIs and scopes above
3. Paste the client ID back here

Do not proceed to Phase 5 without a `clientId`.

---

## Phase 5 — Build

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" "<INTENT_JSON_PATH>"
```

Parse each output line as it arrives:

| Event line | What to do |
|-----------|-----------|
| `WIDGET_READY:{"name":"X","index":N,"total":M}` | Print `✓ X ready (N/M)` |
| `T3_RETRY:{"widget":"X","errors":[...],"intentPath":"..."}` | Update `fnBody` in `intent.json`, re-run script (exit code 2 = retry needed) |
| `TSC_PASS` | Print `✓ TypeScript clean` |
| `AUTH_MISSING:{"var":"clientId",...}` | Warn user: go back and complete Phase 4.5 |
| `PARTIAL_BUILD_DETECTED` | Inform user, continue — build is idempotent |
| `SERVER_READY:{"port":N,"url":"..."}` | Save the URL |
| `BUILD_RESULT:{"success":true,...}` | Open `previewUrl` in browser |

On success, tell the user:

> "Your dashboard is live at [url]. Tell me what to change — I can add widgets, adjust time ranges, or deploy it to your team."
