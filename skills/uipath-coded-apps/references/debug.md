# Debug: Auth and Configuration Issues

Diagnoses and fixes authentication and configuration problems in UiPath coded apps and coded action apps.

**AUTONOMY PRINCIPLE**: Do everything you can with your tools. Only ask the user for things they must do themselves: entering passwords, confirming External App changes in UiPath Cloud. Never ask the user to "let you know" when something is done if you can detect it yourself.

**SDK-FIRST PRINCIPLE**: When fixing code, always check what methods `@uipath/uipath-typescript` already provides before writing custom code.

---

## Step 1: Gather Project Context

Read the app's current configuration:

1. **Find `.env`** — look for `.env`, `.env.local`, `.env.development`. Extract:
   - `VITE_UIPATH_CLIENT_ID`
   - `VITE_UIPATH_REDIRECT_URI`
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

For local dev, `VITE_UIPATH_REDIRECT_URI` must match what's registered in the External Application. Common values:
- Vite default: `http://localhost:5173`
- CRA default: `http://localhost:3000`
- Custom: check `vite.config.ts` server port

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

**Cause:** The redirect URI in `.env` doesn't match what's registered in the UiPath External Application.

**Fix:**
1. Check `VITE_UIPATH_REDIRECT_URI` in `.env`
2. Go to UiPath Cloud → Org Settings → External Applications → your app
3. Verify the redirect URI listed there matches exactly (including `http://` vs `https://` and trailing slash)
4. Add `http://localhost:5173` if it's missing

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
1. Is `VITE_UIPATH_REDIRECT_URI` set correctly and registered in the External Application?
2. Is the dev server running on the port in the redirect URI?
3. Clear browser storage and retry.

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
3. Add redirect URIs:
   - Dev: `http://localhost:5173`
   - Production: the deployed app URL (e.g., `https://<org>.uipath.host/<routingName>`)
   - Action apps: `https://cloud.uipath.com/<orgName>/<tenantName>/actions_`
4. Under **Resources**, add scopes from [oauth-scopes.md](oauth-scopes.md)
5. Save and copy the **Client ID** to `VITE_UIPATH_CLIENT_ID` in `.env`
