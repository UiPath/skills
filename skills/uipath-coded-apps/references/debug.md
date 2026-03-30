# Debug: Auth and Configuration Issues

Diagnoses and fixes authentication and configuration problems in UiPath coded apps and coded action apps.

**AUTONOMY PRINCIPLE**: Do everything you can with your tools. Only ask the user for things they must do themselves: entering passwords, confirming External App changes in UiPath Cloud. Never ask the user to "let you know" when something is done if you can detect it yourself.

**SDK-FIRST PRINCIPLE**: When fixing code, always check what methods `@uipath/uipath-typescript` already provides before writing custom code.

---

## Step 1: Gather Project Context

Read the app's current configuration:

1. **Find `.env`** — look for `.env`, `.env.local`, `.env.development`. Extract:
   - `VITE_UIPATH_CLIENT_ID`
   - `VITE_UIPATH_SCOPE`
   - `VITE_UIPATH_ORG_NAME`
   - `VITE_UIPATH_TENANT_NAME`
   - `VITE_UIPATH_BASE_URL`

2. **Identify SDK services in use** — grep for `new Assets(`, `new Entities(`, `new Buckets(`, `new Processes(`, `new Tasks(`, `new Queues(`, `new MaestroProcesses(`, `new Cases(`, `new ConversationalAgent(` in `**/*.ts` and `**/*.tsx`.

3. **Find the app URL** — check `vite.config.ts` for a custom port, check `package.json` scripts for `--port`, check if the server is running: `lsof -i :5173 -i :3000 -i :8080 2>/dev/null`. Default Vite: `http://localhost:5173`.

---

## Step 2: Proactive Validation (Before Testing in Browser)

**Fix these immediately — do not wait for the user to report an error.**

### 2a — Scope mismatch

Map each SDK service found in Step 1 to its required scopes using [oauth-scopes.md](oauth-scopes.md). Compare against the scope string in `.env`.

If scopes are missing:
1. Update `VITE_UIPATH_SCOPE` in `.env` to add the missing scopes.
2. Tell the user which scopes need to be added to their External Application in UiPath Cloud.

### 2b — Base URL

`VITE_UIPATH_BASE_URL` **must** use the API subdomain — not the portal domain:

| Environment | Correct | Wrong |
|---|---|---|
| cloud | `https://api.uipath.com` | `https://cloud.uipath.com` |
| staging | `https://staging.api.uipath.com` | `https://staging.uipath.com` |
| alpha | `https://alpha.api.uipath.com` | `https://alpha.uipath.com` |

Fix in `.env` if wrong.

### 2c — Redirect URI

The SDK uses `window.location.origin + window.location.pathname` at runtime as the redirect URI — no `VITE_UIPATH_REDIRECT_URI` env var is needed. The URI that must be registered in the External Application is determined by where the app is running:
- Vite default: `http://localhost:5173` (and `http://localhost:5173/` — register both)
- CRA default: `http://localhost:3000` (and `http://localhost:3000/`)
- Custom port: check `vite.config.ts` for `server.port`

If you see a `redirect_uri_mismatch` error, identify the actual URL the browser is on and register it (with and without trailing slash) in the External Application.

---

## Step 3: Clear Browser State

Stale OAuth tokens and PKCE state cause most auth failures. **Always clear before testing.**

**If Playwright MCP is available:**
```javascript
// Navigate to the app URL first, then run via browser_evaluate:
localStorage.clear();
sessionStorage.clear();
document.cookie.split(';').forEach(c => {
  document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
});
'Cleared';
```

**Manual fallback** — tell the user:
> Open DevTools (F12) → Application tab → Storage → Clear site data.
> Or use an Incognito/Private browser window.

---

## Step 4: Reproduce and Diagnose

Start the dev server if not running:
```bash
npm run dev
```

Navigate to the app. Observe what happens at each stage:
- Does the browser redirect to UiPath login?
- Does login complete but redirect back with an error in the URL?
- Does the app load but show an error, or do API calls fail?

---

## Common Issues and Fixes

### `redirect_uri_mismatch` / Login Loop

**Cause:** The redirect URI the SDK sends at runtime (`window.location.origin + window.location.pathname`) is not registered in the UiPath External Application.

**Fix:**
1. Identify the URL the browser is on when login is triggered (e.g. `http://localhost:5173` or `http://localhost:5173/`)
2. Go to UiPath Cloud → Org Settings → External Applications → your app
3. Register that URL as a redirect URI — add both with and without a trailing slash (e.g. `http://localhost:5173` and `http://localhost:5173/`) since trailing slash behavior may vary
4. For production, register the deployed app URL and its trailing-slash variant (e.g. `https://<org>.uipath.host/<routingName>` and `https://<org>.uipath.host/<routingName>/`)
5. There is no `VITE_UIPATH_REDIRECT_URI` env var to update — the redirect URI is derived dynamically

### `invalid_scope` Error in Auth URL

**Cause:** The External Application doesn't have the requested scopes enabled.

**Fix:**
1. Read [oauth-scopes.md](oauth-scopes.md) and verify all required scopes for your SDK services
2. In UiPath Cloud, go to your External Application → Resources → add the missing scopes
3. Also verify `VITE_UIPATH_SCOPE` in `.env` lists them correctly

### API Calls Fail with 401 After Login

**Cause 1:** Token has the wrong scopes for the API being called.
**Fix:** Add the missing scope to `.env` **and** to the External Application. See [oauth-scopes.md](oauth-scopes.md).

**Cause 2:** Token expired.
**Fix:** Clear browser storage (Step 3) and re-authenticate.

### API Calls Fail with CORS Error

**Cause:** App is calling `cloud.uipath.com` directly. The portal domain does not allow browser CORS requests.
**Fix:** Set `VITE_UIPATH_BASE_URL` to `https://api.uipath.com` (the API subdomain does allow CORS).

### `sdk.isAuthenticated()` Returns `false` After Callback

**Cause:** The app doesn't call `sdk.completeOAuth()` before checking `isAuthenticated()`.

**Wrong code (custom URL parsing):**
```typescript
const params = new URLSearchParams(window.location.search);
if (params.has('code')) {
  // Don't do this — use SDK methods instead
  await sdk.initialize();
}
```

**Correct code:**
```typescript
// isInOAuthCallback() checks for ?code= in the URL
if (sdk.isInOAuthCallback()) {
  await sdk.completeOAuth();  // exchange code for tokens
}
if (!sdk.isAuthenticated()) {
  await sdk.initialize();     // start new OAuth flow
  return;
}
// Now safe to use SDK services
```

### App Shows "Loading..." / Init Hangs

**Cause:** `sdk.initialize()` redirects the browser — if the redirect doesn't return to the app, the OAuth flow never completes.

**Check:**
1. Is the current app URL (`window.location.origin + window.location.pathname`) registered as a redirect URI in the External Application? Register both with and without trailing slash.
2. Is the dev server running on the expected port (default: 5173)?
3. Clear browser storage and retry.

### `npm install` fails with 401 Unauthorized from `npm.pkg.github.com`

**Cause:** The user's `.npmrc` has `@uipath` scoped to GitHub Packages registry, which requires authentication. Public UiPath packages are on the public npm registry, not GitHub Packages.

**Fix:** Install `@uipath` packages with an explicit registry override:

```bash
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org
npm install @uipath/uipath-ts-coded-action-apps --@uipath:registry=https://registry.npmjs.org
npm install
```

The `--@uipath:registry` flag overrides the scoped registry for this install only, without modifying `.npmrc`.

---

### Action App: Form Data Not Loading

**Cause:** `codedActionAppsService.getTask()` failed silently.

**Fix:** Add error handling and logging:
```typescript
codedActionAppsService.getTask()
  .then((task) => {
    console.log('Task loaded:', task);
    if (task.data) setFormData(task.data as FormData);
  })
  .catch((err) => console.error('getTask failed:', err));
```

Check the browser console for the error. Common causes: missing `@uipath/uipath-ts-coded-action-apps` package, or app not being opened from within Action Center (the service requires an Action Center context).

### `404` After Deploy / App Not Found

**Cause:** The routing name in `vite.config.ts` doesn't match the deployment routing name.

**Fix:** Ensure `base: '/<routing-name>/'` in `vite.config.ts` matches the routing name used when the app was deployed.

---

## External Application Setup

If the user needs to create or modify an External Application:

1. Go to UiPath Cloud → **Org Settings** → **External Applications**
2. Click **Add Application** → select **Non-Confidential**
3. Add redirect URIs (the SDK uses `window.location.origin + window.location.pathname` at runtime — no env var needed):
   - Dev: `http://localhost:5173` and `http://localhost:5173/` (register both — trailing slash behavior may vary)
   - Production: `https://<org>.uipath.host/<routingName>` and `https://<org>.uipath.host/<routingName>/` (register both)
   - Action apps: `https://cloud.uipath.com/<orgName>/<tenantName>/actions_`
4. Under **Resources**, add scopes from [oauth-scopes.md](oauth-scopes.md)
5. Save and copy the **Client ID** to `VITE_UIPATH_CLIENT_ID` in `.env`
