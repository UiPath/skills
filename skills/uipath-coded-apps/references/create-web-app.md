# Create a UiPath Coded Web App

Scaffold a new UiPath Coded Web Application using Vite + React + TypeScript with the `@uipath/uipath-typescript` SDK.

## Pre-flight: Collect Required Information

**CRITICAL: You do NOT know these values. You CANNOT infer or assume them. Ask the user and wait for their reply before writing any files.**

### Step 1 — Determine required scopes first

**Before asking the user any setup questions**, figure out what the app needs:

1. From the user's **request**, identify which UiPath services the app will use (e.g., Entities, Tasks, Processes, Maestro, Conversational Agent, Buckets, etc.).
2. Read [oauth-scopes.md](oauth-scopes.md) and collect the exact scopes required for every method those services expose.
3. Compose the full deduplicated space-separated scopes string.

You need these scopes **before** Step 2 so you can tell the user exactly what scopes to configure on their Client ID.

### Step 2 — Ask the user for setup info

Output the following text directly (replace `<scopes>` with the actual scopes from Step 1). **Do NOT call any tools yet — just output this text and wait for the user's reply.**

---

Here's what your app needs:

**OAuth scopes:** `<scopes>`

**Redirect URI:** `http://localhost:5173` (computed automatically at runtime — works in both local dev and production)

Please answer these questions to continue:

**1. App name** — lowercase kebab-case project folder name (e.g. `my-dashboard`)

**2. Environment** — which UiPath environment?
   - `cloud` — Production *(most common)*
   - `staging` — Staging
   - `alpha` — Alpha

**3. Org name** — your UiPath organization slug (from `cloud.uipath.com/<orgName>`)

**4. Tenant name** — your UiPath tenant (often `DefaultTenant`)

**5. Client ID** — do you have an existing OAuth External Application client ID with the scopes above?
   - If yes, paste it
   - If no, say **"create one"** and I'll set it up via browser automation

---

**Wait for the user's reply before proceeding.**

### Step 2.5 — Ensure Playwright CLI is available (only if user said "create one")

Before running browser automation, check if Playwright is installed:

```bash
npx playwright --version 2>/dev/null
```

If the command fails or returns no output, install it:

```bash
npm install -D playwright && npx playwright install chromium --with-deps
```

Once confirmed available, read [oauth-client-setup.md](oauth-client-setup.md) and follow it exactly to create the External Application with the scopes from Step 1 and redirect URI `http://localhost:5173`. That reference has all the browser automation details.

### Step 3 — Resolve org name (if not provided)

If the user typed their org name, use it. If they said "find from browser", navigate to the UiPath cloud host for their environment and extract the org name from the URL path (first segment after the domain).

---

## Step 4 — Run Setup Script

Once you have all values (app name, org, tenant, client ID, environment, scopes), run the setup script. The script path is `scripts/setup.sh` in this skill's directory — derive the absolute path from where this file was loaded.

```bash
bash <skill-dir>/scripts/setup.sh <app-name> <org-name> <tenant-name> <client-id> "<scopes>" <environment>
```

**Set `timeout: 300000`** (5 minutes) on the Bash call — `npm install` can take several minutes and the default 2-minute timeout is not enough.

The script creates a complete project:

| File | What it does |
|------|-------------|
| `vite.config.ts` | Vite config with `base: './'`, `global: 'globalThis'`, path-browserify alias |
| `uipath.json` | CLI deployment config with `scope` and `clientId` |
| `.env` / `.env.example` | OAuth env vars (both `UIPATH_*` and `VITE_UIPATH_*`) |
| `src/hooks/useAuth.tsx` | `AuthProvider` + `useAuth` hook handling PKCE callback and login |
| `src/App.tsx` | App shell wrapping content in `<AuthProvider>` |
| Tailwind CSS | `tailwind.config.js`, `postcss.config.js`, `src/index.css` |

---

## Environment Variables

The script creates `.env` with this structure:

```
UIPATH_BASE_URL=https://api.uipath.com
UIPATH_CLIENT_ID=<client-id>
UIPATH_ORG_NAME=<org-name>
UIPATH_TENANT_NAME=<tenant-name>
UIPATH_SCOPE=<scopes>

VITE_UIPATH_BASE_URL=${UIPATH_BASE_URL}
VITE_UIPATH_CLIENT_ID=<client-id>
VITE_UIPATH_ORG_NAME=<org-name>
VITE_UIPATH_TENANT_NAME=<tenant-name>
VITE_UIPATH_SCOPE=<scopes>
```

**Why `${}` for BASE_URL only:** The CLI overwrites `UIPATH_BASE_URL` with the production value at deploy time. The `VITE_` version references it via `${}` so it picks up the new value automatically. Other vars are set directly.

**No redirect URI env var.** The SDK computes it at runtime as `window.location.origin + window.location.pathname`.

---

## uipath.json

The script creates `uipath.json` at the project root. This file is required by the `uip codedapp` CLI for deployment and by the Vite plugin for local dev meta tag injection:

```json
{
  "scope": "<scopes>",
  "clientId": "<client-id>"
}
```

Keep this in sync with `.env` if the client ID or scopes change.

---

## SDK Setup

After the setup script runs, create `src/uipath.ts` to instantiate the `sdk` and any services the app needs. Get the `sdk` instance from the `useAuth` hook rather than creating a new one:

```typescript
import { useAuth } from './hooks/useAuth';
import { Assets } from '@uipath/uipath-typescript/assets';
// import other services as needed

// In a component or hook:
const { sdk } = useAuth();
export const assets = new Assets(sdk);
```

See the **SDK Module Imports** table in `SKILL.md` for all subpath imports.

---

## Auth Pattern

The setup script generates `src/hooks/useAuth.tsx` with `AuthProvider` and `useAuth`. `App.tsx` wraps everything in `<AuthProvider>` and the hook handles PKCE callback detection, login redirect, and logout:

```typescript
// src/App.tsx (generated by setup script)
const authConfig: UiPathSDKConfig = {
  clientId: import.meta.env.VITE_UIPATH_CLIENT_ID,
  orgName: import.meta.env.VITE_UIPATH_ORG_NAME,
  tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME,
  baseUrl: import.meta.env.VITE_UIPATH_BASE_URL,
  redirectUri: window.location.origin + window.location.pathname,
  scope: import.meta.env.VITE_UIPATH_SCOPE,
};

function AppContent() {
  const { isAuthenticated, isLoading, error } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!isAuthenticated) return <div>Redirecting to login...</div>;
  return <div>Your app content here</div>;  // ← replace with real content
}
```

**Key SDK methods** (used inside `useAuth.tsx` — do not call these directly in app code):

| Method | Purpose |
|--------|---------|
| `sdk.isInOAuthCallback()` | Returns true if URL has OAuth `code` param |
| `sdk.completeOAuth()` | Exchanges the code for tokens |
| `sdk.isAuthenticated()` | Returns true if a valid token exists |
| `sdk.initialize()` | Initiates PKCE OAuth flow (redirects to UiPath login) |
| `sdk.getToken()` | Returns the current access token |

---

## Calling SDK Services

After authentication, use the exported service instances:

```typescript
import { assets, entities } from './uipath';

// In a React component or effect:
const items = await assets.getAll({ folderKey: 'your-folder-key' });
const records = await entities.getAllRecords('EntityName');
```

See [oauth-scopes.md](oauth-scopes.md) for the full list of methods and their required scopes.

When implementing specific SDK services, read the corresponding reference:

| Service | Reference |
|---------|-----------|
| Assets, Queues, Buckets, Processes, Tasks | [sdk/orchestrator.md](sdk/orchestrator.md) |
| Data Fabric Entities / ChoiceSets | [sdk/data-fabric.md](sdk/data-fabric.md) |
| Maestro Processes / Cases | [sdk/maestro.md](sdk/maestro.md) |
| Action Center Tasks | [sdk/action-center.md](sdk/action-center.md) |
| Conversational Agent | [sdk/conversational-agent.md](sdk/conversational-agent.md) |
| Pagination patterns | [sdk/pagination.md](sdk/pagination.md) |
| UI patterns (polling, BPMN, HITL) | [patterns.md](patterns.md) |

---

## Vite Configuration

The setup script generates `vite.config.ts` with `base: './'` already set. **Do not change this** — the Cloudflare Worker handles URL routing; the app must use relative asset paths.

Do not add `server.proxy` — it interferes with the OAuth callback and asset resolution.

## Router Base Path (if using a client-side router)

If the app uses React Router, Vue Router, or similar, use `getAppBase()` as the router basename. It reads the `uipath:app-base` meta tag injected by the platform at runtime and falls back to `'/'` locally — safe to use unconditionally.

```typescript
import { getAppBase } from '@uipath/uipath-typescript';
import { BrowserRouter } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter basename={getAppBase()}>
      {/* your routes */}
    </BrowserRouter>
  );
}
```

For React Router v6 (`createBrowserRouter`) and Vue Router patterns, see [assets/templates/web-app.md](../assets/templates/web-app.md).

---

## Run Locally

```bash
npm run dev
```

Open `http://localhost:5173`. The app redirects to UiPath login on first load. After login, it returns to the app.

If login fails, see [debug.md](debug.md).

---

## Deploy

When ready, follow [pack-publish-deploy.md](pack-publish-deploy.md) for the full deployment pipeline.

Before deploying to production, register your deployed app URL (e.g. `https://<org>.uipath.host/<routingName>`) — and the same URL with a trailing slash — as redirect URIs in your External Application in UiPath Cloud. No `.env` change is needed; the SDK derives the redirect URI from `window.location.origin + window.location.pathname` at runtime.
