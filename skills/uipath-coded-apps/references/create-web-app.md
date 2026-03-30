# Create a UiPath Coded Web App

Scaffold a new UiPath Coded Web Application using Vite + React + TypeScript with the `@uipath/uipath-typescript` SDK.

## Pre-flight: Collect Required Information

**CRITICAL: You do NOT know these values. You CANNOT infer or assume them. Ask the user and wait for their reply before writing any files.**

### Step 1 — Determine required scopes

From the user's description, identify which UiPath SDK services the app will use. Read [oauth-scopes.md](oauth-scopes.md) and collect the exact scopes for every method those services expose. Compose the full deduplicated space-separated scopes string — you need this before asking for the Client ID so you can tell the user what scopes to configure.

### Step 2 — Ask the user for setup info

Ask for all of the following. You may ask together or one at a time:

1. **App name** — project folder name, lowercase kebab-case (e.g., `my-dashboard`)
2. **Environment** — `cloud` (production), `staging`, or `alpha`
3. **Organization name** — the org slug in their UiPath URL (`cloud.uipath.com/<orgName>`)
4. **Tenant name** — their UiPath tenant
5. **Which SDK services?** — ask which of these the app will use:
   - Data Fabric Entities / ChoiceSets
   - Storage Buckets
   - Orchestrator Tasks, Processes, Assets, Queues
   - Maestro Processes / Process Instances
   - Cases / Case Instances
   - Conversational Agent
6. **Client ID** — from their UiPath External Application (see below if they don't have one)

**If the user doesn't have a Client ID**, instruct them to:
> Go to **UiPath Cloud → Org Settings → External Applications**. Create a **Non-Confidential** application with:
> - **Redirect URIs** (register all that apply):
>   - Dev: `http://localhost:5173` and `http://localhost:5173/` (register both — trailing slash behavior may vary)
>   - Production: their deployed app URL (e.g. `https://<org>.uipath.host/<routingName>`) and the same URL with a trailing slash, to be safe
> - **Scopes**: `<the scopes you computed in Step 1>`
>
> Copy the Client ID and paste it here.

---

## Project Scaffolding

```bash
npm create vite@latest <app-name> -- --template react-ts
cd <app-name>
npm install
npm install @uipath/uipath-typescript
```

Use the file templates in [assets/templates/web-app.md](../assets/templates/web-app.md) as starting points for all generated files.

---

## Environment Configuration

Create `.env` in the project root:

```
VITE_UIPATH_CLIENT_ID=<client-id>
VITE_UIPATH_SCOPE=<space-separated-scopes>
VITE_UIPATH_ORG_NAME=<org-name>
VITE_UIPATH_TENANT_NAME=<tenant-name>
VITE_UIPATH_BASE_URL=<base-url>
```

> **No redirect URI env var needed.** The SDK uses `window.location.origin + window.location.pathname` at runtime as the redirect URI. Make sure those URLs are registered in your External Application in UiPath Cloud.

**Base URL by environment:**

| Environment | Base URL |
|---|---|
| `cloud` | `https://api.uipath.com` |
| `staging` | `https://staging.api.uipath.com` |
| `alpha` | `https://alpha.api.uipath.com` |

Also create `.env.example` with the same keys but empty values, and add `.env` to `.gitignore`.

---

## SDK Setup

Create `src/uipath.ts` with the core client and any selected services:

```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
// Add imports for selected services — see subpath table below
// import { Assets } from '@uipath/uipath-typescript/assets';
// import { Entities } from '@uipath/uipath-typescript/entities';

export const sdk = new UiPath();

// Instantiate selected services (pass sdk as the argument):
// export const assets = new Assets(sdk);
// export const entities = new Entities(sdk);
```

**Service subpath imports:**

| Service Class(es) | Import Subpath |
|---|---|
| `Entities`, `ChoiceSets` | `@uipath/uipath-typescript/entities` |
| `Buckets` | `@uipath/uipath-typescript/buckets` |
| `Assets` | `@uipath/uipath-typescript/assets` |
| `Processes` | `@uipath/uipath-typescript/processes` |
| `Tasks` | `@uipath/uipath-typescript/tasks` |
| `Queues` | `@uipath/uipath-typescript/queues` |
| `MaestroProcesses`, `ProcessInstances`, `ProcessIncidents` | `@uipath/uipath-typescript/maestro-processes` |
| `Cases`, `CaseInstances` | `@uipath/uipath-typescript/cases` |
| `ConversationalAgent` | `@uipath/uipath-typescript/conversational-agent` |

---

## OAuth Initialization Pattern

The SDK uses PKCE OAuth. Update `src/App.tsx`:

```typescript
import { sdk } from './uipath';
import { useEffect, useState } from 'react';

function App() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        // Handle OAuth callback (URL has ?code=...)
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth();
        }
        // Redirect to login if not authenticated
        if (!sdk.isAuthenticated()) {
          await sdk.initialize();
          return;
        }
        setReady(true);
      } catch (e) {
        setError(String(e));
      }
    };
    init();
  }, []);

  if (error) return <div>Error: {error}</div>;
  if (!ready) return <div>Loading...</div>;

  return <div>Your app content here</div>;
}

export default App;
```

**Key SDK methods — always use these instead of custom implementations:**

| Method | Purpose |
|--------|---------|
| `sdk.isInOAuthCallback()` | Returns true if URL has OAuth `code` param |
| `sdk.completeOAuth()` | Exchanges the code for tokens — call before `isAuthenticated()` |
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

`base: './'` is **always required**. The Cloudflare Worker handles URL routing at the platform level — the app must use relative asset paths to work correctly when served from any path.

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
});
```

Do not add a `server.proxy` to `vite.config.ts` — it interferes with the OAuth callback and asset resolution.

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
