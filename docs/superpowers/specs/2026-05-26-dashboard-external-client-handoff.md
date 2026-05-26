# Handoff Plan: Dashboard Auth Pivot — External Client (Non-Confidential OAuth)

**Date:** 2026-05-26  
**Branch:** `feat/uipath-dashboards-skill`  
**Status:** Ready for implementation — do NOT start without reading this fully  
**Priority:** High — security requirement

---

## Context & Why This Change

### The Problem with the Current Auth Model

The dashboard skill currently uses two auth strategies:
- **Dev preview**: `VITE_UIPATH_PAT` — a session access token from `uip login`
- **Production (FP surface)**: `ActionCenterTokenManager` — the FP host injects tokens via postMessage

The FP surface approach has a **security issue**: when a dashboard is hosted on UiPath's First Party surfaces (the portal), the host passes its OWN token to the app. That token belongs to the FP surface's service account, not the logged-in user. This means dashboards would act as the FP surface identity rather than the user's identity — a privilege escalation vector.

### The Fix

Switch to **non-confidential external client OAuth (PKCE)**. The dashboard app registers as an OAuth client with specific scopes, and each user authenticates themselves via the standard UiPath OAuth flow. No service tokens, no PAT in environment files.

---

## What Changes (High-Level)

| Component | Before | After |
|---|---|---|
| `useAuth.ts` | PAT secret OR ActionCenterTokenManager | OAuth PKCE with clientId + scopes |
| `uipath.json` | `{ "name": "..." }` | `{ "name": "...", "scope": "<all scopes>", "clientId": "<id>" }` |
| `.env.local` | `VITE_UIPATH_PAT=...` | `VITE_UIPATH_CLIENT_ID=...` |
| Build Phase 4 (Plan) | No mention of auth | Asks user for existing external client OR creates new one |
| Build Phase 6 (Config) | Writes PAT to .env.local | Writes CLIENT_ID to .env.local; no PAT anywhere |
| Deploy flow | No change needed | No change needed |

---

## OAuth Scopes — Complete List from TS SDK Docs

Source: https://uipath.github.io/uipath-typescript/oauth-scopes/

Use ALL of these in the external client. The dashboard may need any of them depending on what metrics the user requests.

```
OR.Assets
OR.Assets.Read
OR.Jobs
OR.Jobs.Write
OR.Folders
OR.Folders.Read
OR.Buckets
OR.Buckets.Read
OR.Execution
OR.Execution.Read
OR.Tasks
OR.Tasks.Write
OR.Queues
OR.Queues.Read
OR.Users
OR.Users.Read
DataFabric.Schema.Read
DataFabric.Data.Read
DataFabric.Data.Write
PIMS
Insights.RealTimeData
ConversationalAgents
Traces.Api
openid
profile
```

**As a single space-separated string (for uipath.json and CLI commands):**
```
OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Write OR.Folders OR.Folders.Read OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read OR.Tasks OR.Tasks.Write OR.Queues OR.Queues.Read OR.Users OR.Users.Read DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS Insights.RealTimeData ConversationalAgents Traces.Api openid profile
```

---

## Redirect URLs

Every external client for a dashboard needs exactly **two** redirect URIs:

| Purpose | URL | Notes |
|---|---|---|
| Local preview | `http://localhost:5173` | Vite dev server port (hardcoded in vite.config.ts `server.port: 5173`) |
| FP surface (portal) | `https://{ENV}.uipath.com/{orgName}/portal_` | Environment-aware — see below |

**Portal redirect URL by environment:**
- Alpha: `https://alpha.uipath.com/{orgName}/portal_`
- Staging: `https://staging.uipath.com/{orgName}/portal_`
- Prod: `https://cloud.uipath.com/{orgName}/portal_`

The `{orgName}` is the `Data.Organization` value from `uip login status --output json`. This is known at build time (Phase 2 preflight already extracts it).

---

## External Client Creation via CLI

The `uip admin` skill already covers external app management. The create command:

```bash
uip admin external-apps create \
  --name "UiPath Dashboard - <DASHBOARD_NAME>" \
  --type NonConfidential \
  --redirect-uri "http://localhost:5173" \
  --redirect-uri "https://<ENV>.uipath.com/<ORG_NAME>/portal_" \
  --scope "<ALL_SCOPES>" \
  --output json
```

Parse the `ClientId` from the JSON response.

**To check if an external app already exists:**
```bash
uip admin external-apps list --output json | node -e "
  const apps = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
  const match = apps.find(a => a.Name && a.Name.includes(process.argv[2]));
  process.stdout.write(match ? JSON.stringify(match) : '');
" "<TEMP_FILE>" "<DASHBOARD_NAME>"
```

---

## Plan Phase Change (Phase 4 — What the User Sees)

The plan shown to the user must now include an **external client section** at the end, before the approval prompt. Add this to `build-plan.md` approval gate section:

```
**One more thing before I build:**

Your dashboard needs an OAuth app to securely sign users in.

Do you have an existing non-confidential external app in UiPath?
  A. Yes — paste the Client ID and I'll use it
  B. No — I'll create one for you automatically

(Choosing B adds ~30 seconds to the build)
```

- If user chooses **A**: proceed to Phase 6, inject their `clientId` into the plan.json
- If user chooses **B**: Phase 5.5 creates the external client (see below), then proceeds to Phase 6.

This question appears in the plan approval block — it's part of the plan approval step, not a separate step.

---

## New Phase 5.5 — External Client (when user chooses "create new")

Insert between Phase 5 (approval) and Phase 6 (configure) when user wants a new client:

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")

# Derive portal redirect URL from environment
if echo "$DATA_BASE_URL" | grep -q "alpha"; then
  PORTAL_REDIRECT="https://alpha.uipath.com/${ORG}/portal_"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then
  PORTAL_REDIRECT="https://staging.uipath.com/${ORG}/portal_"
else
  PORTAL_REDIRECT="https://cloud.uipath.com/${ORG}/portal_"
fi

uip admin external-apps create \
  --name "UiPath Dashboard - ${DASHBOARD_NAME}" \
  --type NonConfidential \
  --redirect-uri "http://localhost:5173" \
  --redirect-uri "${PORTAL_REDIRECT}" \
  --scope "OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Write OR.Folders OR.Folders.Read OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read OR.Tasks OR.Tasks.Write OR.Queues OR.Queues.Read OR.Users OR.Users.Read DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS Insights.RealTimeData ConversationalAgents Traces.Api openid profile" \
  --output json > "${TEMP_DIR}/uip-extapp.json"

CLIENT_ID=$(node -e "
  const d = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
  process.stdout.write(d.ClientId || d.clientId || '');
" "${TEMP_DIR}/uip-extapp.json")
rm -f "${TEMP_DIR}/uip-extapp.json"

echo "CLIENT_ID=${CLIENT_ID}"
```

**If user provides existing client ID (Option A):**
```bash
CLIENT_ID="<user-provided-client-id>"
```

---

## Phase 6 — Configure (changes)

Add `CLIENT_ID` to the plan.json written in Phase 6. Remove `VITE_UIPATH_PAT` from `.env.local`. The plan.json `pat` field stays as `"FROM_AUTH"` (used only for Insights API calls which still need a token — see Note below).

**New `.env.local` written by `build-dashboard.mjs`:**
```
VITE_UIPATH_CLOUD_URL=<cloudUrl>
VITE_UIPATH_BASE_URL=<apiUrl>
VITE_UIPATH_ORG_NAME=<orgName>
VITE_UIPATH_TENANT_NAME=<tenantName>
VITE_INSIGHTS_TENANT_ID=<tenantId>
VITE_UIPATH_CLIENT_ID=<clientId>
```

Note: `VITE_UIPATH_PAT` is **removed** from `.env.local`. The dashboard uses OAuth PKCE — no PAT in the environment.

**Important Note on Insights API calls:** The Insights RTM endpoints use a Bearer token that comes from the OAuth PKCE session (`sdk.getAccessToken()` or equivalent). The `useInsights.ts` hook's `getToken` function needs to get the token from the SDK's OAuth session, not from a PAT env var. This is a secondary change in `useAuth.ts` (see below).

---

## Files That Need Changing

### 1. `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md`

**Changes:**
- Phase 4 plan format: add external client question block (see above)
- After Phase 5: add Phase 5.5 for external client creation
- Phase 6 scaffold bash: remove `VITE_UIPATH_PAT` from `.env.local` write, add `VITE_UIPATH_CLIENT_ID`
- Phase 6 plan.json: add `clientId` field, keep `pat: "FROM_AUTH"` (for Insights token)

### 2. `assets/templates/dashboard/scaffold/uipath.json`

**Before:**
```json
{ "name": "UiPath Dashboard" }
```

**After:**
```json
{
  "name": "UiPath Dashboard",
  "scope": "OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Write OR.Folders OR.Folders.Read OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read OR.Tasks OR.Tasks.Write OR.Queues OR.Queues.Read OR.Users OR.Users.Read DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS Insights.RealTimeData ConversationalAgents Traces.Api openid profile",
  "clientId": ""
}
```

`clientId` is empty in the template — `build-dashboard.mjs` fills it in from plan.json.

### 3. `assets/templates/dashboard/scaffold/.env.example`

**Remove:** `VITE_UIPATH_PAT=`  
**Add:** `VITE_UIPATH_CLIENT_ID=`

### 4. `assets/templates/dashboard/scaffold/src/hooks/useAuth.ts`

**Full rewrite of `resolveConfig()` function:**

```typescript
const SCOPES = 'OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Write OR.Folders OR.Folders.Read OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read OR.Tasks OR.Tasks.Write OR.Queues OR.Queues.Read OR.Users OR.Users.Read DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS Insights.RealTimeData ConversationalAgents Traces.Api openid profile'

function resolveConfig(): UiPathSDKConfig {
  return {
    baseUrl: import.meta.env.VITE_UIPATH_BASE_URL as string,
    orgName: import.meta.env.VITE_UIPATH_ORG_NAME as string,
    tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME as string,
    clientId: import.meta.env.VITE_UIPATH_CLIENT_ID as string,
    scopes: SCOPES.split(' '),
    redirectUri: `${window.location.origin}${window.location.pathname}`,
  }
}
```

**Also change the init flow** — remove PAT shortcut, always use SDK OAuth:
```typescript
const init = async () => {
  setIsLoading(true)
  setError(null)
  try {
    if (sdk.isInOAuthCallback()) {
      await sdk.completeOAuth()
      window.history.replaceState({}, document.title, window.location.pathname)
    }
    setIsAuthenticated(sdk.isAuthenticated())
  } catch (err) {
    setError(err instanceof UiPathError ? err.message : 'Authentication failed')
  } finally {
    setIsLoading(false)
  }
}
```

**`getToken` function** — get token from SDK's internal session (for Insights API calls):
```typescript
const getToken = useCallback(async (): Promise<string> => {
  // Get access token from the OAuth session managed by the SDK
  // Try the SDK's token manager first, then fall back to sessionStorage search
  const keys = Object.keys(sessionStorage)
  const tokenKey = keys.find(k => k.includes('access_token') || k.includes('accessToken'))
  if (tokenKey) {
    const raw = sessionStorage.getItem(tokenKey)
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as { value?: string; access_token?: string }
        const token = parsed.value ?? parsed.access_token ?? raw
        if (token && token.length > 10) return token
      } catch {
        if (raw.length > 10) return raw
      }
    }
  }
  throw new Error('Access token not available — please sign in')
}, [])
```

**`login` function** stays the same:
```typescript
const login = useCallback(async () => {
  await sdk.login()
}, [sdk])
```

### 5. `assets/templates/dashboard/scaffold/src/App.tsx`

**No `sdkConfig` prop needed** (already correct from previous session).  
**Add a "Sign in" button** since users now need to authenticate:
```tsx
if (!isAuthenticated) {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        {error && <p className="text-destructive text-sm">{error}</p>}
        <button
          onClick={() => void login()}
          className="rounded-md bg-primary px-6 py-2 text-primary-foreground text-sm font-medium hover:opacity-90"
        >
          Sign in with UiPath
        </button>
      </div>
    </div>
  )
}
```

### 6. `assets/scripts/build-dashboard.mjs`

**Changes:**
- Read `clientId` from plan.json
- Write `VITE_UIPATH_CLIENT_ID=${clientId}` to `.env.local` instead of `VITE_UIPATH_PAT`
- Write `clientId` to `uipath.json` (fill the empty placeholder)

```javascript
// After writing .env.local, also update uipath.json with the clientId:
const uipathJsonPath = join(P, 'uipath.json')
if (existsSync(uipathJsonPath) && plan.clientId) {
  const uj = JSON.parse(readFileSync(uipathJsonPath, 'utf8'))
  uj.clientId = plan.clientId
  writeFileSync(uipathJsonPath, JSON.stringify(uj, null, 2))
}
```

### 7. `references/dashboards/primitives/auth-context.md`

**Minor update:** Remove references to PAT being written to `.env.local`. Add note about `CLIENT_ID` instead. The PAT is still read from `.auth` file but only for the Insights token in `getToken()`, not for OAuth config.

---

## plan.json Schema Change

Add `clientId` field. Keep `pat: "FROM_AUTH"` (still needed for Insights API Bearer token via `getToken()`).

```json
{
  "projectDir": "...",
  "dashboardName": "...",
  "routingName": "...",
  "orgName": "...",
  "tenantName": "...",
  "cloudUrl": "...",
  "apiUrl": "...",
  "tenantId": "...",
  "pat": "FROM_AUTH",
  "clientId": "<external-client-id>",
  "widgets": [...],
  "dashboardTsx": "...",
  "indexTs": "...",
  "appTsxImports": "...",
  "appTsxRoutes": "..."
}
```

---

## Build plan.md Change (Phase 4 — Plan Format)

Add to the end of the plan, just before the "What you can do" section:

```markdown
**One more thing before I build:**

Your dashboard needs an OAuth app to let users sign in securely.

Do you have an existing non-confidential external app in UiPath?
- **Yes** — reply with the Client ID and I'll use it
- **No** — reply "create one" and I'll set it up automatically (adds ~30 seconds)
```

This is part of the approval gate interaction. After the user responds to the plan edits AND provides the client ID decision, the agent proceeds. Both confirmations count as a single "approval."

---

## Regenerate package-lock.json

After changing `useAuth.ts` to remove the PAT shortcut and use OAuth, run `npm install` in the scaffold to make sure the lockfile is current. No new npm dependencies should be needed — the SDK already supports OAuth PKCE.

---

## What NOT to Change

- **Insights RTM API calls** — these still use `getToken()` from `useAuth`, which now gets the token from the SDK's OAuth session instead of `VITE_UIPATH_PAT`. No changes needed in `useInsights.ts` or `insights-client.ts`.
- **Deploy flow** — no auth changes needed for deploy. The PAT in `build-dashboard.mjs` (`readPatFromAuth()`) is only for the pre-warm npm ci check, not OAuth.
- **Widget templates** — no changes.
- **insights-catalog.md** — no changes.
- **data-router.md** — no changes.

---

## Testing Checklist (after implementation)

- [ ] Fresh build: agent asks about external client in Phase 4
- [ ] Option A: user provides client ID → used in `uipath.json` and `.env.local`
- [ ] Option B: agent creates external client → `uip admin external-apps create` runs → CLIENT_ID extracted
- [ ] `.env.local` contains `VITE_UIPATH_CLIENT_ID` and does NOT contain `VITE_UIPATH_PAT`
- [ ] `uipath.json` in project dir has correct `clientId` and full `scope` string
- [ ] `npm run dev` → sign-in button appears → clicking it redirects to UiPath OAuth
- [ ] After OAuth callback: dashboard loads, widgets render
- [ ] `tsc --noEmit` passes on scaffold with new `useAuth.ts`
- [ ] coder-eval smoke test `dashboard_scaffold` still passes (may need updating for new env var name)

---

## Related Files for Next Session

All on branch `feat/uipath-dashboards-skill`:

| File | Why relevant |
|---|---|
| `references/dashboards/plugins/build/impl.md` | Phases 4, 5.5, 6 need updating |
| `references/dashboards/primitives/build-plan.md` | Plan format + approval gate text |
| `assets/templates/dashboard/scaffold/src/hooks/useAuth.ts` | Full rewrite of resolveConfig + init + getToken |
| `assets/templates/dashboard/scaffold/uipath.json` | Add scope + empty clientId |
| `assets/templates/dashboard/scaffold/.env.example` | Replace PAT with CLIENT_ID |
| `assets/scripts/build-dashboard.mjs` | Write clientId to .env.local and uipath.json |
| `references/dashboards/primitives/auth-context.md` | Minor update re: credentials |
| `tests/tasks/uipath-coded-apps/dashboard/` | Update smoke + e2e tests for new env var |

---

## Session Context for Next Agent

This session built the `uipath-coded-apps` dashboard capability from scratch across ~50+ commits. Key things that are working:

- **Template-substitution architecture**: `build-dashboard.mjs` takes `plan.json` config → loads widget templates → TypeScript always correct
- **Single-script build**: agent writes plan.json (1 Write) + runs script (1 Bash) = entire build done in 2 tool calls
- **Pre-warm**: scaffold + npm ci starts during plan review (Phase 3.5), done before user approves
- **Platform fixes**: all Node.js for file ops (no cp -r), process.argv for JSON parsing (no /dev/stdin), os.tmpdir() for temp files (no /tmp)
- **Deploy flow**: 10-step with state.json, --path-name (not --routing-name), APP_SAFE_NAME sanitization

The auth pivot is the **only remaining architectural change** needed before the skill can be considered production-ready. Everything else is working.
