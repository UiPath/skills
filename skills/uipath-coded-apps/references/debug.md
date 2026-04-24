# Debug: UiPath Coded App Issues

Diagnoses and fixes failures in UiPath coded apps and coded action apps — auth, OAuth callback, scopes, API calls, OData queries, CORS, deploy/routing, and related config.

**AUTONOMY PRINCIPLE**: Do everything you can with your tools. Only ask the user for things the agent physically cannot do: entering passwords or 2FA codes during login, confirming a destructive portal action. Never ask the user to "let you know" when something is done if you can detect it yourself.

**Specifically, External Application configuration changes (adding scopes, adding redirect URIs) are automated by Playwright scripts in [oauth-client-setup.md](oauth-client-setup.md).** When a fix requires a portal change, run the script — do not:
- Say *"I can't make that change from here"* (you can — the scripts launch Chrome and drive the portal UI)
- Run `open <portal URL>` to hand the browser to the user
- List manual click-through steps for the user to perform
- Present "Option A: open the portal for you to click / Option B: try something else" menus

The only time to fall back to manual is if Step 0b reports `chrome-missing` OR the script has failed after 2–3 attempts with a captured error.

**SDK-FIRST PRINCIPLE**: When fixing code, always check what methods `@uipath/uipath-typescript` already provides before writing custom code.

**HARD RULE**: Do not edit any file, env var, or external config until **Step 0** has produced a concrete observation — a specific URL, console error, HTTP status, or on-page error text. Guessing at fixes when you don't know the failing layer wastes tool calls and introduces regressions.

---

## Step 0: Reproduce the Failure

Vague reports like *"login doesn't work"*, *"fails after login"*, or *"the app is broken"* can have many root causes across very different layers: SDK init, OAuth redirect, token scope, API call, OData query, CORS, routing, or a plain component bug. **Reproduce the failure yourself and observe before doing anything else.** Do not ask the user for details you can collect by running the app.

### 0a — Start the dev server

Check if already running, else start in the background:

```bash
lsof -i :5173 2>/dev/null || (npm run dev &)
```

Adjust the port if `vite.config.ts` uses a non-default `server.port`.

### 0b — Check for Chrome and Playwright

The reproduction script uses the system's real Chrome via Playwright CLI (same pattern as `oauth-client-setup.md`). Verify both are available:

```bash
# Chrome
(ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" 2>/dev/null \
 || command -v google-chrome 2>/dev/null \
 || command -v google-chrome-stable 2>/dev/null \
 || ls "/c/Program Files/Google/Chrome/Application/chrome.exe" 2>/dev/null \
 || ls "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" 2>/dev/null) \
 && echo "chrome-found" || echo "chrome-missing"

# Playwright — if not found, follow oauth-client-setup.md Step 2 (Setup B)
# to install into ~/.uipath-skills/playwright/
npx playwright --version 2>/dev/null || echo "playwright-missing"
```

If Chrome is missing, skip to Step 0d — ask the user to describe the failure (URL in the address bar, on-screen error text, or devtools console/network output) since the agent can't drive a browser itself.

### 0c — Run the reproduction script

Write the following to `~/.uipath-skills/playwright/reproduce.mjs` (or your project root if Playwright is installed there — see [`oauth-client-setup.md` Step 2](oauth-client-setup.md#step-2-ensure-playwright-is-available)). Substitute `APP_URL` if the port isn't 5173. Run from the directory the script lives in:

```bash
cd ~/.uipath-skills/playwright && node ./reproduce.mjs
```

> **Do not write to `/tmp/`** — ESM `import 'playwright'` fails because `/tmp/` has no parent `node_modules`. The script must live alongside (or under a directory tree containing) a `node_modules/playwright`.

```js
// ~/.uipath-skills/playwright/reproduce.mjs
import { chromium } from 'playwright';
import { homedir } from 'os';
import { join } from 'path';

const APP_URL = 'http://localhost:5173';
const USER_DATA_DIR = join(homedir(), '.uipath-playwright-profile');
const SCRIPT_NAME = 'reproduce';

// Regex used to locate the login trigger on an app that renders an explicit
// login screen (the scaffold template uses "Sign in with UiPath"). Adjust
// if your app uses different text (e.g., "Continue", "Authenticate").
const LOGIN_BUTTON_REGEX = /sign in|log in|login|continue|authenticate/i;

// Hoisted so the unhandledRejection handler can snapshot page state and close
// the persistent-profile context on failure. Without closing, Chrome stays
// alive after the Node process dies and blocks the next run against the same
// profile until the user manually kills Chrome.
let __page = null;
let __context = null;
process.on('unhandledRejection', async (err) => {
  if (__page) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const shotPath = `./${SCRIPT_NAME}-FAIL-${stamp}.png`;
    try { await __page.screenshot({ path: shotPath, fullPage: true }); } catch {}
    let htmlPreview = '';
    try { htmlPreview = (await __page.content()).slice(0, 3000); } catch {}
    let title = '';
    try { title = await __page.title(); } catch {}
    console.error(JSON.stringify({
      status: 'error',
      message: err?.message || String(err),
      url: __page.url(), title,
      screenshot: shotPath,
      htmlPreview,
    }, null, 2));
  } else {
    console.error(JSON.stringify({ status: 'error', message: err?.message || String(err) }));
  }
  try { await __context?.close(); } catch {}
  process.exit(1);
});

// Pre-flight: confirm the dev server is reachable before launching Chrome.
// Catches the common failure where the user Ctrl-C'd `npm run dev` between
// runs, so we exit with a clear message instead of an opaque Playwright stack.
async function checkDevServer() {
  try {
    const res = await fetch(APP_URL, { method: 'GET', signal: AbortSignal.timeout(3000) });
    if (!res.ok && res.status >= 500) throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    console.error(JSON.stringify({
      status: 'error',
      message: `Dev server not reachable at ${APP_URL} (${err?.message || err}). Start it with \`npm run dev\` (see Step 0a) and retry.`,
    }));
    process.exit(1);
  }
}

(async () => {
  await checkDevServer();
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    channel: 'chrome',
  });
  __context = context;
  const page = context.pages()[0] || await context.newPage();
  __page = page;

  // Capture ALL console messages (capped to last 50) plus errors separately.
  // Apps often log useful diagnostics via console.log/warn — don't drop them.
  const consoleAll = [];
  const consoleErrors = [];
  page.on('console', (msg) => {
    const entry = `[${msg.type()}] ${msg.text()}`;
    consoleAll.push(entry);
    if (consoleAll.length > 50) consoleAll.shift();
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  const failedRequests = [];
  page.on('response', async (res) => {
    if (res.status() >= 400) {
      let body = '';
      try { body = (await res.text()).slice(0, 500); } catch {}
      failedRequests.push({ url: res.url(), status: res.status(), body });
    }
  });

  await page.goto(APP_URL);

  // If the app renders a landing page with a login button (scaffolded apps
  // do, since they use explicit login), click it to trigger the OAuth flow.
  // If no button is visible within 2s, assume auto-redirect and continue.
  try {
    const btn = page.getByRole('button', { name: LOGIN_BUTTON_REGEX });
    if (await btn.isVisible({ timeout: 2000 })) await btn.click();
  } catch {}

  const isLocalhost = () => {
    const h = new URL(page.url()).hostname;
    return h === 'localhost' || h === '127.0.0.1';
  };
  const hasOAuthError = () => /[?&](error|errorCode)=/i.test(page.url());

  // Phase 1: wait up to 30s for the browser to leave localhost (OAuth
  // redirect kicked off). Fast-fail if it never leaves — captures state
  // for apps stuck on a login screen, missing client ID, SDK init error, etc.
  const phase1Deadline = Date.now() + 30 * 1000;
  while (Date.now() < phase1Deadline && isLocalhost()) {
    await page.waitForTimeout(1000);
  }

  // Phase 2: if we left localhost, give the user up to 3 minutes to
  // complete login and return (or UiPath to show an OAuth error page).
  if (!isLocalhost()) {
    const phase2Deadline = Date.now() + 3 * 60 * 1000;
    while (Date.now() < phase2Deadline) {
      if (isLocalhost()) break;
      if (hasOAuthError()) break; // UiPath error page (e.g. redirect_uri_mismatch) — bail fast
      await page.waitForTimeout(2000);
    }
  }

  // Settle 5s so client-side PKCE exchange, routing, and first API calls
  // have time to run (and fail, if they're going to).
  await page.waitForTimeout(5000);

  const finalUrl = page.url();
  const errorText = await page.evaluate(() => document.body.innerText.slice(0, 1000));

  await context.close();

  console.log(JSON.stringify({
    finalUrl,
    consoleAll,
    consoleErrors,
    failedRequests,
    errorText,
  }, null, 2));
})();
```

Parse the JSON output — it contains everything needed to classify the failure:
- `finalUrl` — where the browser ended up (check for `?error=`, `?code=`, or an unexpected domain)
- `consoleAll` — last 50 console messages of any level (SDK init traces, warnings, etc.)
- `consoleErrors` — JS errors only
- `failedRequests` — any 4xx/5xx responses with status, URL, and truncated body
- `errorText` — first 1000 chars of visible page text (catches on-screen error banners)

**On unhandled failure** (script crashes mid-run — e.g. the login selector throws, the page navigates to an unreachable host, or Playwright hits a protocol error) the handler emits a different payload on **stderr**:
```json
{ "status": "error", "message": "...", "url": "...", "title": "...", "screenshot": "./reproduce-FAIL-<stamp>.png", "htmlPreview": "..." }
```
Read the `screenshot` path with the `Read` tool — it often diagnoses the failure by itself (e.g. a stuck login screen, an OAuth error page, a blank canvas). Fall back to `htmlPreview` if the screenshot is inconclusive. The cleanup step below removes these PNGs once you're done.

**When to customize the script:**
- **Login trigger text is different.** Adjust `LOGIN_BUTTON_REGEX` if the app's button doesn't match `sign in | log in | login | continue | authenticate`.
- **Auto-redirect apps.** If the app calls `sdk.initialize()` in a top-level `useEffect` and there's no login button, leave the click block in place — `isVisible` times out in 2s and the script continues.
- **Interaction-driven failure.** If the bug only reproduces after a specific UI action (*"fails when I click Approve on a task"*), add `await page.click(...)` / `await page.fill(...)` steps **after** Phase 2 and **before** the final 5s settle.

**Clean up (mandatory).** Once you've captured enough evidence to classify the failure (Step 0d below), delete the script and any failure screenshots immediately:

```bash
rm ~/.uipath-skills/playwright/reproduce.mjs ~/.uipath-skills/playwright/reproduce-FAIL-*.png 2>/dev/null
```

Do not leave the `.mjs` file in the user's workspace.

### 0d — Classify the failure

Match the observation to the correct fix section. **Jump directly to the matching section below — do not work through Steps 1–3 first unless no row matches.**

| Observation | Failing layer | Go to |
|---|---|---|
| URL never leaves `localhost` — browser doesn't redirect to UiPath | SDK init / config | Step 1 + Step 2 |
| Stuck on UiPath side; page shows `redirect_uri_mismatch` | Redirect URI not registered | *redirect_uri_mismatch / Login Loop* |
| Returned to app with `?error=invalid_scope` in URL | OAuth scopes | *`invalid_scope` Error in Auth URL* |
| Returned with `?code=...` but console shows a PKCE / callback error | Callback processing | *`sdk.isAuthenticated()` Returns `false` After Callback* |
| App stuck on "Loading..." indefinitely | Callback never completes | *App Shows "Loading..." / Init Hangs* |
| App renders, first API call returns **401** | Token / scope | *API Calls Fail with 401 After Login* |
| App renders, API returns **403** | Folder key or missing admin privileges | Check `UIPATH_FOLDER_KEY`; re-check scopes |
| App renders, API returns **400** with OData error | Query shape | Verify OData field names / filter syntax against the relevant SDK reference in `references/sdk/` |
| App renders, API returns **404** | Wrong endpoint, wrong folder, or resource doesn't exist | Verify base URL, folder, and resource id |
| Network / CORS error in console | Wrong base URL | *API Calls Fail with CORS Error* |
| Deployed app URL returns `404` | Vite base path / routing | *`404` After Deploy / App Not Found* |

**If no row matches or the observation is inconclusive**, continue to Step 1 for config-level diagnosis.

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

3. **Find the app URL** — check `vite.config.ts` for a custom port, check `package.json` scripts for `--port`. Default Vite: `http://localhost:5173`.

---

## Step 2: Proactive Validation

Fix these immediately — they are common config-level issues that Step 0 might not surface directly but frequently cause auth failures.

### 2a — Scope mismatch

Map each SDK service found in Step 1 to its required scopes using [oauth-scopes.md](oauth-scopes.md). Compare against the scope string in `.env`.

If scopes are missing:
1. Update `VITE_UIPATH_SCOPE` in `.env` to add the missing scopes.
2. **Copy the consolidated script verbatim** from [Step 3 of `oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script) (one script for all ops), save to `~/.uipath-skills/playwright/uipath-oauth.mjs`, then run with `--op add-scopes` — substituting `--cloud-host`, `--org-name`, `--client-id` (from `.env` → `VITE_UIPATH_CLIENT_ID`), and `--scopes-by-resource` per the [mapping table](oauth-client-setup.md#scope--resource-mapping-reference). Do not rewrite the script or "mirror the pattern" — the selectors are battle-tested and rewriting drops the bug fixes. Do not ask the user to click through the portal manually. Only fall back to [manual instructions](oauth-client-setup.md#adding-scopes-to-an-existing-app) if Chrome isn't available.

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

If you see a `redirect_uri_mismatch` error, identify the actual URL the browser is on. Then **copy the consolidated script verbatim** from [Step 3 of `oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script), save to `~/.uipath-skills/playwright/uipath-oauth.mjs`, and run with `--op add-redirects` — passing `--cloud-host`, `--org-name`, `--client-id` (from `.env`), and `--redirects` with both the failing URL and its trailing-slash variant. Do not rewrite the script or invent a different approach — rewrites drop the bug fixes (truncated column handling, pencil-Edit button) and the script fails. Do not ask the user to click through the portal.

---

## Step 3: Clear Browser State

Stale OAuth tokens and PKCE state cause most auth-callback failures. Clear before re-testing if Step 0 showed a suspicious callback state (e.g. `?code=` still in the URL, or `completeOAuth` errors in the console).

**Option A — run a clear-state Playwright script** before re-running Step 0c:

```js
// ~/.uipath-skills/playwright/clear-state.mjs
import { chromium } from 'playwright';
import { homedir } from 'os';
import { join } from 'path';

const APP_URL = 'http://localhost:5173';
const USER_DATA_DIR = join(homedir(), '.uipath-playwright-profile');

(async () => {
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: true,
    channel: 'chrome',
  });
  const page = await context.newPage();
  await page.goto(APP_URL);
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
    document.cookie.split(';').forEach((c) => {
      document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
    });
  });
  await context.close();
  console.log('cleared');
})();
```

Write to `~/.uipath-skills/playwright/clear-state.mjs` (same location as the reproduction script — see Step 0c) and run:

```bash
cd ~/.uipath-skills/playwright && node ./clear-state.mjs
```

Then immediately clean up (mandatory, not optional):

```bash
rm ~/.uipath-skills/playwright/clear-state.mjs 2>/dev/null
```

**Option B — tell the user:**
> Open DevTools (F12) → Application tab → Storage → Clear site data.
> Or use an Incognito/Private browser window.

---

## Common Issues and Fixes

### `redirect_uri_mismatch` / Login Loop

**Cause:** The redirect URI the SDK sends at runtime (`window.location.origin + window.location.pathname`) is not registered in the UiPath External Application.

> **You fix this yourself with Playwright.** Do not tell the user *"register the URI in UiPath Cloud"* and stop there. Do not run `open <portal URL>`. Do not present a bullet list of admin-portal clicks. The consolidated `uipath-oauth.mjs` script (in [`oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script)) launches Chrome and performs every one of those clicks automatically when run with `--op add-redirects`.

**Fix (autonomous) — execute these steps yourself without deferring to the user:**
1. Identify the URL the browser was sent to when login was triggered (e.g. `http://localhost:5173` or `http://localhost:5173/`). Step 0c's `finalUrl` usually shows it.
2. **Copy the consolidated script verbatim** from [Step 3 of `oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script) into `~/.uipath-skills/playwright/uipath-oauth.mjs`. Do **not** rewrite or paraphrase — the selectors handle the portal's truncated Client-ID column and per-row pencil-Edit button.
3. Run with `--op add-redirects` from the directory the script lives in (Setup B default below; for Setup A use the project root):
   ```bash
   cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs --op add-redirects \
     --cloud-host https://staging.uipath.com --org-name myorg \
     --client-id <uuid> \
     --redirects 'http://localhost:5173,http://localhost:5173/'
   ```
4. Verify stdout contains `{"status":"ok"}`. Clear browser state (Step 3), re-run Step 0c to confirm the fix.
5. There is no `VITE_UIPATH_REDIRECT_URI` env var to update — the redirect URI is derived dynamically.

Fall back to [manual instructions](oauth-client-setup.md#adding-redirect-uris-to-an-existing-app) only if Step 0b reported `chrome-missing` or the script has genuinely failed after 2–3 runs with captured errors.

> Production redirect URIs are registered automatically by `uip codedapp deploy`. If they're missing on the External Application after a deploy, the same script can add them.

### `invalid_scope` Error in Auth URL

**Cause:** The External Application doesn't have the requested scopes enabled.

> **You fix this yourself with Playwright.** Do not tell the user *"the External App needs the scope added in UiPath Cloud"* and stop there. Do not run `open <portal URL>`. Do not present a bullet list of admin-portal clicks. The consolidated `uipath-oauth.mjs` script (in [`oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script)) launches Chrome and performs every one of those clicks automatically when run with `--op add-scopes`.

**Fix (autonomous) — execute these steps yourself without deferring to the user:**
1. Read [oauth-scopes.md](oauth-scopes.md) and determine every scope the SDK services in use require.
2. Update `VITE_UIPATH_SCOPE` in `.env` to list all required scopes (space-separated).
3. **Copy the consolidated script verbatim** from [Step 3 of `oauth-client-setup.md`](oauth-client-setup.md#step-3-write-the-consolidated-script) into `~/.uipath-skills/playwright/uipath-oauth.mjs`. Do **not** rewrite the script.
4. Run with `--op add-scopes` from the directory the script lives in (Setup B default below; for Setup A use the project root):
   ```bash
   cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs --op add-scopes \
     --cloud-host https://staging.uipath.com --org-name myorg \
     --client-id <uuid> \
     --scopes-by-resource '{"Orchestrator":["OR.Tasks.Read"]}'
   ```
   > Use the **shortest substring** that matches both the dropdown label and the attached-list label as the key (e.g. `"Orchestrator"`, not `"Orchestrator API Access"`). See the [mapping reference](oauth-client-setup.md#scope--resource-mapping-reference) for the safe key per resource — the long dropdown label fails when the resource is already attached because the attached-list shows a different label (`UiPath.Orchestrator`).
5. Verify stdout contains `{"status":"ok"}`. Clear browser state (Step 3) and re-test.

Fall back to the [manual instructions](oauth-client-setup.md#adding-scopes-to-an-existing-app) only if Step 0b reported `chrome-missing` or the script has genuinely failed after 2–3 runs with captured errors.

### API Calls Fail with 401 After Login

**Cause 1:** Token has the wrong scopes for the API being called.
**Fix:** Update `VITE_UIPATH_SCOPE` in `.env` with the missing scope (see [oauth-scopes.md](oauth-scopes.md)), then run the [Add Scopes to an Existing App](oauth-client-setup.md#add-scopes-to-an-existing-app) script to register it on the External App. Clear browser storage (Step 3) and re-authenticate so the new token includes the added scope.

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
1. Is the current app URL (`window.location.origin + window.location.pathname`) registered as a redirect URI in the External Application? If not, run the [Add Redirect URIs to an Existing App](oauth-client-setup.md#add-redirect-uris-to-an-existing-app) script (include both with and without trailing slash).
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

**Cause:** Vite `base` is set to a routing name or sub-path instead of `'./'`, or the client-side router basename is hardcoded instead of using `getAppBase()`.

**Fix:** Check both:

1. `vite.config.ts` must have `base: './'` (not `'/<routing-name>/'` — the platform handles URL routing via its Cloudflare Worker).
2. If the app uses a client-side router (React Router, Vue Router), the basename must use `getAppBase()` from `@uipath/uipath-typescript` — not a hardcoded path. `getAppBase()` reads the `uipath:app-base` meta tag injected by the platform at runtime and falls back to `'/'` locally.

After fixing, rebuild (`npm run build`) and re-deploy (`uip codedapp deploy`). If 404 persists, check that `deploy` returned a valid `appUrl` in `.uipath/app.config.json`.

---

## External Application Setup

For any create or update of an External Application (adding redirect URIs, adding scopes, creating a new app), use the automated scripts in [oauth-client-setup.md](oauth-client-setup.md). The file covers:

- [Create a new External Application](oauth-client-setup.md#step-3-write-the-automation-script)
- [Add Redirect URIs to an Existing App](oauth-client-setup.md#add-redirect-uris-to-an-existing-app)
- [Add Scopes to an Existing App](oauth-client-setup.md#add-scopes-to-an-existing-app)
- Manual fallback steps for each operation, if Chrome isn't available

Key constants to remember when filling in the scripts:
- Dev redirect URIs: `http://localhost:5173` and `http://localhost:5173/` (register both)
- Action apps redirect URI: `https://cloud.uipath.com/<orgName>/<tenantName>/actions_`
- Production web-app URIs are registered automatically by `uip codedapp deploy` — do not add them manually.
