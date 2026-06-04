# Dashboard Build Plugin

Implements `build` action from `CAPABILITY.md`. Reads an `intent.json`, runs `build-dashboard.mjs`, streams progress to terminal.

## Critical Rules

1. Read `primitives/tier-resolution.md` before classifying any metric.
2. Write `intent.json` with compact fields only — never full TypeScript in the intent file (except T3 `fnBody`).
3. Fire pre-warm (`npm ci`) BEFORE showing the plan — hidden from user.
4. Show plan in plain English — no API names, no tier labels.
5. HALT after plan — do not build until user explicitly confirms.
6. Parse build script stdout line by line — each `WIDGET_READY:` event → print one progress tick.
7. On `T3_RETRY`: update `fnBody` in `intent.json`, re-run build script (exit code 2 = retry needed).
8. On `BUILD_RESULT`: extract `previewUrl`, open it in browser.
9. Never commit generated dashboard files.
10. Check for clientId BEFORE starting the build — a missing clientId means the dashboard cannot authenticate at runtime. Do NOT skip this phase.

## 5-Phase Build Flow

### Phase 0 — Incremental check (1 Bash)

```bash
node -e "require('fs').existsSync('.dashboard/state.json') && process.exit(0) || process.exit(1)" && echo INCREMENTAL || echo FRESH
```

INCREMENTAL → follow `primitives/incremental-editor.md`
FRESH → continue to Phase 1

### Phase 1 — Boot (1 parallel Read block, 3 files)

ALL THREE in ONE message block:
1. `primitives/auth-context.md`
2. `primitives/tier-resolution.md`
3. `references/dashboards/aesthetic/layout-patterns.md`

### Phase 2 — Preflight (1 Bash)

```bash
uip login status --output json
```

Extract: `orgName`, `tenantName`, `cloudUrl`, `tenantId` (UUID from `~/.uipath/.auth`).
Derive `apiUrl`: insert `api.` subdomain (e.g. `alpha.uipath.com` → `alpha.api.uipath.com`).

Pre-warm silently (do not tell user):
```bash
cd <PROJECT_DIR> && npm ci --prefer-offline &
```

### Phase 3 — Plan (0 tool calls, in-context)

For each user metric:
1. Check hard-refuse list in `primitives/tier-resolution.md` — refuse metric only (not whole dashboard)
2. Classify tier using tier-resolution rules
3. Write `intent.json` (see schema in `primitives/build-plan.md`)

Render plan:
```
Here's your **[Name]** — N widgets. Confirm to build, or tell me what to change.

• **[Widget Name] ([timeRange])** — one-line plain-English description
...

What you can do: "make it 7 days", "add X", "remove Y"
```

No API names. No tier labels. No technical jargon.

### Phase 4 — Approval gate

HALT. Do not run build script until user confirms.
If user edits: update intent.json, re-render plan, HALT again.

### Phase 4.5 — External Client (0–1 Bash)

**Every dashboard needs an external OAuth app client ID.** Without it the browser PKCE auth flow has no app to authenticate against and the dashboard shows a blank error screen.

**Check intent.json first:**
```bash
node -e "const p=JSON.parse(require('fs').readFileSync('${INTENT_JSON_PATH}','utf8')); process.exit(p.clientId ? 0 : 1)" && echo HAS_CLIENT || echo NEEDS_CLIENT
```

**If HAS_CLIENT:** skip to Phase 5.

**If NEEDS_CLIENT:** ask the user:
> "Your dashboard needs an external OAuth app to handle authentication. Do you have an existing client ID, or should I create one for you?"

**If user provides existing client ID:**
- Update `clientId` in intent.json with their value
- Skip to Phase 5

**If user says create one (or doesn't know):**
```bash
uip admin external-apps create "UiPath Dashboard - <DASHBOARD_NAME>" \
  --non-confidential \
  --redirect-uri "http://localhost:5173,http://localhost:5174,http://localhost:5175" \
  --user-scope "OR.Assets,OR.Assets.Read,OR.Jobs,OR.Jobs.Write,OR.Folders,OR.Folders.Read,OR.Buckets,OR.Buckets.Read,OR.Execution,OR.Execution.Read,OR.Tasks,OR.Tasks.Write,OR.Queues,OR.Queues.Read,OR.Users,OR.Users.Read,Insights.RealTimeData" \
  --output json
```

Extract `ClientId` from the response and update intent.json:
```bash
# The response JSON contains a "ClientId" field
CLIENT_ID=$(echo '<RESPONSE>' | node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).ClientId || '')")
```

Update intent.json: set `clientId` to the extracted value.

Tell the user: "Created OAuth app — client ID saved. Building your dashboard now."

**If the command fails** (permission error, network issue): tell the user to create an external app manually at `<CLOUD_URL>/<ORG>/portal_/adminui/#/externalApps` and provide the client ID. Don't proceed without a client ID.

### Phase 5 — Build (1 Bash, stream events)

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${INTENT_JSON_PATH}"
```

Parse stdout line by line:
- `WIDGET_READY:{"name":"X","index":N,"total":M}` → print `✓ X ready (N/M)`
- `T3_RETRY:{...}` → exit code 2 → update fnBody in intent.json → re-run
- `TSC_PASS` → print `✓ TypeScript clean`
- `SERVER_READY:{"port":N,"url":"..."}` → save URL
- `BUILD_RESULT:{...}` → open previewUrl in browser

On success: "Your dashboard is live at [url]. Tell me what to change."
