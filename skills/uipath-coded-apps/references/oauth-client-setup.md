# OAuth Client Management via Playwright CLI

This reference describes how to **create** and **update** UiPath External Applications (OAuth clients) using **Playwright CLI** browser automation — the AI writes a single Node.js script and runs it via Bash with an `--op` flag.

Update operations (adding redirect URIs, adding scopes) are used by `debug.md` to autonomously fix misconfigured External Apps without asking the user to click through the UiPath portal.

## Cloud Host URLs

| Environment | Cloud Host |
|---|---|
| cloud | `https://cloud.uipath.com` |
| staging | `https://staging.uipath.com` |
| alpha | `https://alpha.uipath.com` |

## Prerequisites

You need: `orgName`, `environment` (cloud/staging/alpha), app name, redirect URI(s), and required OAuth scopes.

## Step 1: Check for Chrome

The Playwright script launches the system's real Chrome (`channel: 'chrome'`) rather than Playwright's bundled Chromium — real Chrome handles enterprise SSO and work profiles correctly. Detect whether Chrome is installed with:

```bash
(ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" 2>/dev/null \
 || command -v google-chrome 2>/dev/null \
 || command -v google-chrome-stable 2>/dev/null \
 || ls "/c/Program Files/Google/Chrome/Application/chrome.exe" 2>/dev/null \
 || ls "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" 2>/dev/null) \
 && echo "chrome-found" || echo "chrome-missing"
```

**If the output is `chrome-missing`, skip the Playwright automation entirely and go straight to the [Manual Fallback](#manual-fallback) section below.** Do not install Playwright, do not write the script, do not retry — the script cannot launch without Chrome, and retrying will only produce the same "executable not found" error.

## Step 2: Ensure Playwright is Available

Only run this step if Step 1 reported `chrome-found`.

**Critical constraint:** Node's ESM `import` resolution **only walks up from the script's directory** looking for `node_modules`. It does **not** honor `NODE_PATH`, and it does **not** find globally-installed packages. So **the script must live in a directory whose parent tree contains a `node_modules/playwright`** — otherwise `import 'playwright'` fails with `ERR_MODULE_NOT_FOUND`.

This couples the script's location to Playwright's install location. Pick one of two setups:

### Setup A — project-local (use if the user's app already has playwright)

Check first:

```bash
test -e "$(pwd)/node_modules/playwright/package.json" && echo "project-local-found"
```

If this prints `project-local-found`, the script will live at the project root: `./uipath-oauth.mjs`. Run it from the project directory: `node ./uipath-oauth.mjs --op ...`.

### Setup B — isolated install (default; use if Setup A didn't match)

Install Playwright into a dedicated directory outside the user's project, and write the script alongside it:

```bash
mkdir -p ~/.uipath-skills/playwright \
  && cd ~/.uipath-skills/playwright \
  && (test -f package.json || npm init -y >/dev/null) \
  && (test -e node_modules/playwright || npm install playwright)
```

The script then lives at `~/.uipath-skills/playwright/uipath-oauth.mjs`. Run it from that directory: `cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs --op ...`.

> `npx playwright install chromium` is **not** needed — the script uses the system's installed Chrome via `channel: 'chrome'`.
>
> **Avoid** `npm install -D playwright` inside the user's app — adds ~300MB to their `devDependencies` for a tool that runs once or twice.
>
> **Avoid** `npm install -g playwright` for this script — globally installed packages are not resolvable from ESM `import` in modern Node. The script will fail with `Cannot find package 'playwright'` even when `npm list -g` shows it installed. Use Setup B instead.
>
> **Avoid** `/tmp/` as the script location. `/tmp/` has no parent `node_modules`, so ESM `import 'playwright'` from there always fails. Use the project root (Setup A) or `~/.uipath-skills/playwright/` (Setup B).

## Step 3: Write the Consolidated Script

> **⚠️ Copy the script below as your starting point.** The structure (consolidated `--op` flag, persistent profile, login-extension, `waitForResponse` Client ID capture, failure diagnostics, search-by-prefix, pencil-Edit button, two-path scope add) is battle-tested. Use it as-is for the first run.
>
> **You MAY edit individual selectors** when failure evidence (the screenshot + htmlPreview from the failure diagnostic) shows a specific selector no longer matches the live portal. The portal DOM drifts; that's expected. The screenshot-driven debug loop is the supported way to keep the script working over time.
>
> Do **NOT**:
> - Rewrite the whole script from scratch or "mirror the pattern" of another script — you will drop bug fixes (truncated Client-ID column handling, two-path scope add, login-extension, failure diagnostics) and waste hours rediscovering them
> - Invent a "direct edit URL" for the app — UiPath's portal routes through a filtered list + Edit button; direct-URL hacks are not tested
> - Change the `USER_DATA_DIR` path — the login session is persisted there; using any other directory forces the user to log in again
> - Split the script back into per-operation files — one consolidated script is the supported pattern
> - Change a selector without evidence (a failure screenshot, an htmlPreview snippet, or `npx playwright codegen` output). Speculative selector changes regress more often than they fix.
>
> **Script location:** `~/.uipath-skills/playwright/uipath-oauth.mjs` (Setup B from Step 2) **or** the user's project root if Setup A applied. **Do not write the script to `/tmp/`** — ESM `import 'playwright'` will fail because `/tmp/` has no parent `node_modules`.
>
> **Always locate apps by Client-ID prefix, never by name.** Multiple apps in the same org can share the same display name (e.g. three apps literally called `action-center-tasks`). The Client ID is the only unique, stable identifier. The script searches by the first 8 chars of the UUID because the Application ID column in the portal table is truncated and full-UUID matching against visible DOM text returns zero hits.

Write the following to `~/.uipath-skills/playwright/uipath-oauth.mjs` (Setup B) or `<project-root>/uipath-oauth.mjs` (Setup A):

```js
// ~/.uipath-skills/playwright/uipath-oauth.mjs — UiPath External Application Playwright helper.
//
// Operations (set via --op):
//   create         Create a new External App, print { clientId } on stdout
//   add-redirects  Add redirect URIs to an existing app (by --client-id)
//   add-scopes     Add scopes to an existing app (by --client-id)
//
// Common args: --cloud-host <url>  --org-name <slug>
// create:      --name <app-name>  --redirects <comma-sep>  --scopes-by-resource <json>
// add-redirects:  --client-id <uuid>  --redirects <comma-sep>
// add-scopes:     --client-id <uuid>  --scopes-by-resource <json>
//
// Stdout: a single JSON line on success: {"status":"ok", ...}
// Stderr: progress logs prefixed with [HH:MM:SS], plus a JSON error blob
//         on failure (with screenshot + htmlPreview for diagnosis).
import { chromium } from 'playwright';
import { homedir } from 'os';
import { join } from 'path';

// ---- Arg parsing (no external deps) ----
function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith('--')) continue;
    const key = k.slice(2);
    const next = argv[i + 1];
    if (next !== undefined && !next.startsWith('--')) { out[key] = next; i++; }
    else { out[key] = true; }
  }
  return out;
}
const args = parseArgs(process.argv);
const OP = args.op;
const CLOUD_HOST = args['cloud-host'];
const ORG_NAME = args['org-name'];
const CLIENT_ID = args['client-id'];
const APP_NAME = args.name;
const SCOPES_BY_RESOURCE = args['scopes-by-resource'] ? JSON.parse(args['scopes-by-resource']) : null;
const REDIRECTS = args.redirects ? args.redirects.split(',').map(s => s.trim()).filter(Boolean) : [];

if (!OP || !CLOUD_HOST || !ORG_NAME) {
  console.error('Usage: node uipath-oauth.mjs --op <create|add-redirects|add-scopes> --cloud-host <url> --org-name <org> [op-specific args]');
  process.exit(2);
}

const USER_DATA_DIR = join(homedir(), '.uipath-playwright-profile');
const EXTERNAL_APPS_URL = `${CLOUD_HOST}/${ORG_NAME}/portal_/admin/external-apps/oauth`;
const SCRIPT_NAME = 'uipath-oauth';

// ---- Progress log to stderr (keeps stdout clean for JSON output) ----
const log = (m) => console.error(`[${new Date().toISOString().slice(11, 19)}] ${m}`);

// ---- Failure diagnostics: screenshot + html on uncaught failure ----
// Hoisted so the unhandledRejection handler can also close the browser
// context — without this, the persistent-profile Chrome window stays alive
// after the Node process dies, blocking subsequent runs against the same
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
      status: 'error', op: OP,
      message: err?.message || String(err),
      url: __page.url(), title,
      screenshot: shotPath,
      htmlPreview,
    }, null, 2));
  } else {
    console.error(JSON.stringify({ status: 'error', op: OP, message: err?.message || String(err) }));
  }
  // Close the persistent-profile context so Chrome doesn't leak.
  try { await __context?.close(); } catch {}
  process.exit(1);
});

const isOnLoginPage = (u) =>
  u.includes('/identity_/') || u.includes('/login') || u.includes('account.uipath.com');

// Wait for user login. Initial 2 min budget; extend by 90s whenever the URL
// changes (user is mid 2FA/SSO and making progress).
async function waitForLogin(page) {
  let deadline = Date.now() + 2 * 60 * 1000;
  let lastUrl = page.url();
  log('Waiting for login...');
  while (Date.now() < deadline) {
    await page.waitForTimeout(3000);
    const url = page.url();
    if (!isOnLoginPage(url)) { log('Login complete.'); return; }
    if (url !== lastUrl) { deadline = Date.now() + 90 * 1000; lastUrl = url; }
  }
  throw new Error('Login timed out (no URL change for 2+ minutes).');
}

// Pre-flight: confirm key anchors are present on the External Apps page.
// Fails fast (5s) if the portal DOM has drifted.
async function preflight(page) {
  log('Pre-flight: verifying External Apps page DOM...');
  const addAppBtn = page.getByRole('button', { name: /add application/i });
  const searchInput = page.getByPlaceholder(/search/i).first();
  await Promise.all([
    addAppBtn.waitFor({ state: 'visible', timeout: 5000 }),
    searchInput.waitFor({ state: 'visible', timeout: 5000 }),
  ]);
  log('Pre-flight passed.');
}

// Find an app by Client ID prefix and click its pencil-Edit button.
async function openAppByClientId(page, clientId) {
  log(`Searching for app with Client ID prefix "${clientId.slice(0, 8)}"...`);
  const search = page.getByPlaceholder(/search/i).first();
  await search.waitFor({ state: 'visible', timeout: 5000 });
  await search.click();
  await search.fill(clientId.slice(0, 8));
  await page.waitForTimeout(2000); // server-side filter

  // Race three known patterns for the Edit button. data-testid is most stable
  // (verified MUI icon convention).
  const editBtn = page
    .locator('button:has(svg[data-testid="EditOutlinedIcon"])')
    .or(page.getByRole('button', { name: /^edit$/i }))
    .or(page.locator('button[aria-label="Edit" i]'));

  if ((await editBtn.count()) === 0) {
    throw new Error(`No Edit button after filtering by "${clientId.slice(0, 8)}". Verify the Client ID matches an app in this org.`);
  }
  await editBtn.first().click();
  await page.waitForTimeout(2000);
  log('Edit drawer opened.');
}

// Add scopes inside the app's edit surface — historically a drawer/dialog,
// but the create flow on the modern portal navigates to a full PAGE
// (/external-apps/oauth/add). Try drawer/dialog selectors first (still used
// by some update flows / portal versions), then fall back to the page body.
async function addScopesInOpenDrawer(page, scopesByResource) {
  let editDrawer;
  try {
    editDrawer = page.locator('[role="dialog"]:visible, .MuiDrawer-paper:visible, ap-drawer:visible, ap-dialog:visible, aside:visible').first();
    await editDrawer.waitFor({ state: 'visible', timeout: 2000 });
    log('Edit surface is a drawer/dialog.');
  } catch {
    log('No drawer/dialog visible — using page body (full-page create flow).');
    editDrawer = page.locator('body');
  }

  for (const [resource, scopes] of Object.entries(scopesByResource)) {
    log(`Adding scopes for resource: ${resource}`);

    // The dropdown label and the attached-list label often differ (e.g.
    // dropdown "Orchestrator API Access" vs attached-list "UiPath.Orchestrator").
    // Try the literal label first; if no row matches, fall back to the first
    // word as a substring (e.g. "Orchestrator") which usually appears in both.
    let attachedRow = editDrawer.locator('[role="row"]').filter({ hasText: resource }).first();
    let attachedMatcher = resource;
    if ((await attachedRow.count()) === 0) {
      const firstWord = resource.split(/\s+/)[0];
      if (firstWord && firstWord !== resource) {
        const candidate = editDrawer.locator('[role="row"]').filter({ hasText: firstWord }).first();
        if ((await candidate.count()) > 0) {
          attachedRow = candidate;
          attachedMatcher = firstWord;
          log(`  Matched attached row by first-word fallback "${firstWord}".`);
        }
      }
    }
    const alreadyAttached = (await attachedRow.count()) > 0;

    let drawer;
    if (alreadyAttached) {
      log(`  "${resource}" already attached — using its per-row Edit.`);
      const rowEditBtn = attachedRow.locator('button:has(svg[data-testid="EditOutlinedIcon"])');
      if ((await rowEditBtn.count()) === 0) {
        throw new Error(`"${resource}" row's Edit button (svg[data-testid="EditOutlinedIcon"]) not found.`);
      }
      await rowEditBtn.first().click();
      await page.waitForTimeout(1500);

      // The per-resource Edit surface on the modern portal is an <ap-drawer>
      // / <portal-sheet> web component WITHOUT role="dialog" — the old
      // [role="dialog"] selector matches a hidden notification surface and
      // times out. Try several anchors, then fall back to page body.
      drawer = page.locator('[role="dialog"]:visible, ap-drawer:visible, portal-sheet:visible, .MuiDrawer-paper:visible').last();
      try {
        await drawer.waitFor({ state: 'visible', timeout: 2000 });
        log('  Per-row edit surface located via drawer/sheet selector.');
      } catch {
        // Fall back: wait for the drawer's resource heading to be visible,
        // then scope subsequent locators to the page body.
        try {
          await page.getByRole('heading', { name: new RegExp(attachedMatcher, 'i') }).waitFor({ state: 'visible', timeout: 5000 });
        } catch {}
        log('  Per-row edit surface — falling back to page body.');
        drawer = page.locator('body');
      }
    } else {
      log(`  "${resource}" not yet attached — using Add scopes.`);
      await page.getByRole('button', { name: /add scopes/i }).last().click();
      await page.waitForTimeout(1500);
      drawer = page.locator('[role="dialog"][aria-label*="resource" i]');
      await drawer.waitFor({ state: 'visible', timeout: 10000 });

      const resourceSelect = drawer.locator('[data-cy="scope-resource-select"] [role="button"]');
      await resourceSelect.click();
      await page.waitForTimeout(500);

      const listbox = page.getByRole('listbox', { name: 'Resource' });
      await listbox.waitFor({ state: 'visible', timeout: 5000 });
      await listbox.locator('[role="option"]').filter({ hasText: resource }).click();
      await page.waitForTimeout(1000);
    }

    for (const scope of scopes) {
      const scopeLabel = drawer.locator('label.MuiFormControlLabel-root').filter({ hasText: scope });
      if ((await scopeLabel.count()) > 0) {
        const cb = scopeLabel.locator('input[type="checkbox"]');
        if (!(await cb.isChecked())) await cb.check({ force: true });
      } else {
        console.error(`  Warning: scope "${scope}" not found under "${resource}"`);
      }
    }

    await drawer.locator('[data-cy="scopes-add-edit-submit-button"]').click();
    await page.waitForTimeout(2000);
  }
}

// Type each redirect URI and Enter to commit.
async function typeRedirects(page, redirects) {
  for (const uri of redirects) {
    const input = page.getByPlaceholder(/enter url here/i).last();
    await input.fill(uri);
    await input.press('Enter');
    await page.waitForTimeout(300);
  }
}

(async () => {
  log(`Operation: ${OP}`);
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false, channel: 'chrome',
  });
  __context = context; // expose to the unhandledRejection handler for cleanup
  const page = context.pages()[0] || await context.newPage();
  __page = page;
  // Tight default timeouts — slow ops use explicit waitFor with longer windows.
  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(30000);

  // Watch save responses so update ops can verify success at the end.
  let saveOk = false;
  page.on('response', (res) => {
    const m = res.request().method();
    const path = new URL(res.url()).pathname;
    if (/\/ExternalClient\/?/.test(path) && (m === 'PATCH' || m === 'PUT') && res.ok()) {
      saveOk = true;
    }
  });

  await page.goto(EXTERNAL_APPS_URL);
  await page.waitForLoadState('domcontentloaded');

  if (isOnLoginPage(page.url())) {
    await waitForLogin(page);
    await page.goto(EXTERNAL_APPS_URL);
    await page.waitForLoadState('domcontentloaded');
  }

  await page.waitForTimeout(2000);
  await preflight(page);

  // ============ CREATE ============
  if (OP === 'create') {
    if (!APP_NAME || !SCOPES_BY_RESOURCE) throw new Error('create requires --name and --scopes-by-resource');

    log('Clicking "Add application"...');
    await page.getByRole('button', { name: /add application/i }).click();
    await page.waitForTimeout(1500);

    log('Filling application name...');
    const nameInput = page.getByLabel(/application name/i);
    await nameInput.click();
    await nameInput.fill(APP_NAME);

    log('Selecting Non-Confidential...');
    await page.getByLabel(/non-confidential application/i).check();
    await page.waitForTimeout(500);

    await addScopesInOpenDrawer(page, SCOPES_BY_RESOURCE);

    log('Entering redirect URIs...');
    await typeRedirects(page, REDIRECTS);

    // Re-check name — drawer cycles can clear it.
    if (!(await nameInput.inputValue())) {
      await nameInput.click();
      await nameInput.fill(APP_NAME);
    }

    log('Submitting and capturing Client ID from POST /ExternalClient...');
    const responsePromise = page.waitForResponse(
      res =>
        res.request().method() === 'POST' &&
        /\/ExternalClient\/?$/.test(new URL(res.url()).pathname) &&
        res.ok(),
      { timeout: 30000 },
    );

    await page.locator('[data-cy="add-edit-submit-button"]').click();

    let clientId = null;
    try {
      const response = await responsePromise;
      const body = await response.json();
      clientId = body.id || body.Id || null;
    } catch (err) {
      console.error(`[capture] waitForResponse failed: ${err.message}`);
    }

    if (!clientId) {
      log('Primary capture missed — falling back to re-query by name.');
      await page.goto(EXTERNAL_APPS_URL);
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1500);
      const search = page.getByPlaceholder(/search/i).first();
      await search.fill(APP_NAME);
      await page.waitForTimeout(1500);
      const editBtn = page.locator('button:has(svg[data-testid="EditOutlinedIcon"])');
      if ((await editBtn.count()) > 0) {
        await editBtn.first().click();
        await page.waitForTimeout(2000);
        const text = await page.innerText('body');
        const m = text.match(/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i);
        if (m) clientId = m[0];
      }
    }

    await context.close();
    if (!clientId) throw new Error('Could not extract Client ID via network or DOM fallback.');
    log('Success.');
    console.log(JSON.stringify({ status: 'ok', op: 'create', clientId }));
    return;
  }

  // ============ ADD-REDIRECTS ============
  if (OP === 'add-redirects') {
    if (!CLIENT_ID || !REDIRECTS.length) throw new Error('add-redirects requires --client-id and --redirects');

    await openAppByClientId(page, CLIENT_ID);
    log(`Adding ${REDIRECTS.length} redirect URI(s)...`);
    await typeRedirects(page, REDIRECTS);

    log('Saving...');
    await page.locator('[data-cy="add-edit-submit-button"]').click();
    await page.waitForTimeout(5000);

    await context.close();
    if (!saveOk) throw new Error('Save request did not return OK — verify in the portal.');
    log('Success.');
    console.log(JSON.stringify({ status: 'ok', op: 'add-redirects', added: REDIRECTS }));
    return;
  }

  // ============ ADD-SCOPES ============
  if (OP === 'add-scopes') {
    if (!CLIENT_ID || !SCOPES_BY_RESOURCE) throw new Error('add-scopes requires --client-id and --scopes-by-resource');

    await openAppByClientId(page, CLIENT_ID);
    await addScopesInOpenDrawer(page, SCOPES_BY_RESOURCE);

    log('Saving app...');
    await page.locator('[data-cy="add-edit-submit-button"]').click();
    await page.waitForTimeout(5000);

    await context.close();
    if (!saveOk) throw new Error('Save request did not return OK — verify in the portal.');
    log('Success.');
    console.log(JSON.stringify({ status: 'ok', op: 'add-scopes', added: SCOPES_BY_RESOURCE }));
    return;
  }

  throw new Error(`Unknown --op: ${OP}`);
})();
```

## Step 4: Run the Script

The script writes one JSON line to **stdout** on success and progress logs to **stderr**. Watch both. The script launches a **visible** Chrome window so the user can complete the login flow on first run.

> **Run the script from the directory you wrote it to** (project root for Setup A, `~/.uipath-skills/playwright/` for Setup B). Running from any other directory — including `/tmp/` — will fail with `Cannot find package 'playwright'`.

The examples below assume **Setup B** (the default). For Setup A, replace `cd ~/.uipath-skills/playwright` with `cd <project-root>` and adjust the script path accordingly.

### Operation: create

Use this when no External App exists yet for the project.

```bash
cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs \
  --op create \
  --cloud-host https://staging.uipath.com \
  --org-name myorg \
  --name my-uipath-app \
  --redirects 'http://localhost:5173,http://localhost:5173/' \
  --scopes-by-resource '{"Orchestrator":["OR.Assets","OR.Execution"]}'
```

> **Use the shortest substring that matches both the dropdown label and the attached-list label** as the key (e.g. `"Orchestrator"`, not `"Orchestrator API Access"`). See the [mapping reference](#scope--resource-mapping-reference) for the safe key per resource.

On success, stdout: `{"status":"ok","op":"create","clientId":"<uuid>"}` — write this `clientId` into `.env` as `VITE_UIPATH_CLIENT_ID` (and into `uipath.json`).

### Operation: add-redirects

Use this when login fails with `redirect_uri_mismatch`, or a new dev port/host needs registration.

```bash
cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs \
  --op add-redirects \
  --cloud-host https://staging.uipath.com \
  --org-name myorg \
  --client-id 00000000-0000-0000-0000-000000000000 \
  --redirects 'http://localhost:5173,http://localhost:5173/'
```

On success, stdout: `{"status":"ok","op":"add-redirects","added":[...]}`.

### Operation: add-scopes

Use this for `invalid_scope` errors or 401 responses where the SDK service requires a scope the token is missing.

```bash
cd ~/.uipath-skills/playwright && node ./uipath-oauth.mjs \
  --op add-scopes \
  --cloud-host https://staging.uipath.com \
  --org-name myorg \
  --client-id 00000000-0000-0000-0000-000000000000 \
  --scopes-by-resource '{"Orchestrator":["OR.Tasks.Read"]}'
```

> Use the shortest substring key (e.g. `"Orchestrator"`) — see the [mapping reference](#scope--resource-mapping-reference). Passing the long dropdown label (`"Orchestrator API Access"`) only works when the resource is *not yet attached*; if it's already on the app, the substring won't match the attached-list label (`UiPath.Orchestrator`) and the script will take the wrong code path.

On success, stdout: `{"status":"ok","op":"add-scopes","added":{...}}`. After this, also update `VITE_UIPATH_SCOPE` in `.env` to include the new scopes — both the External App and the env config must list them.

> **Resource label vs scope name:** The keys in `--scopes-by-resource` must match the portal's dropdown labels exactly (e.g. `"Orchestrator API Access"`, `"Maestro API Access"`), not the scope names. The values are the scope names. See the [Scope → Resource Mapping Reference](#scope--resource-mapping-reference) below.

## Step 5: Parse the Output

The script prints exactly one JSON line to **stdout** on success. Parse it. For `create`, extract `clientId`. For update ops, verify `status: ok`.

Anything on **stderr** is either:
- Progress logs (`[HH:MM:SS] message`) — informational, ignore unless debugging
- A JSON error blob with screenshot + htmlPreview — see "If the Script Fails" below

## Step 6: Clean Up (Mandatory)

Immediately after the script prints `status: ok`, delete the script and any failure artifacts. **Not optional** — leaving `.mjs` files behind is pollution that can get committed if the script lives in the project (Setup A).

For Setup B (default — script at `~/.uipath-skills/playwright/`):

```bash
rm ~/.uipath-skills/playwright/uipath-oauth.mjs ~/.uipath-skills/playwright/uipath-oauth-FAIL-*.png 2>/dev/null
```

For Setup A (script at the project root):

```bash
rm ./uipath-oauth.mjs ./uipath-oauth-FAIL-*.png 2>/dev/null
```

The Playwright install itself stays — it's a one-time bootstrap and the persistent profile (`~/.uipath-playwright-profile`) holds the login session for future runs.

For `add-scopes`, also tell the user to **clear browser state** and re-test (see `debug.md` Step 3) — stale tokens won't have the new scope.

---

## If the Script Fails

The script captures a JSON error blob on **stderr** when any await throws (typically a Playwright locator timeout):

```json
{
  "status": "error",
  "op": "add-scopes",
  "message": "locator.click: Timeout 10000ms exceeded. ...",
  "url": "https://staging.uipath.com/myorg/portal_/admin/external-apps/oauth",
  "title": "External Applications",
  "screenshot": "./uipath-oauth-FAIL-2026-04-15T....png",
  "htmlPreview": "<html>..."
}
```

When you see this:

1. **Read the screenshot** (`Read` tool on the `screenshot` path). Often enough by itself to diagnose.
2. **Inspect `htmlPreview`** if the screenshot is inconclusive. Search it for the DOM around the expected element (attached-resource row, Edit button, scope checkbox, etc.).
3. **Update the specific selector** that timed out. The `message` names exactly which locator failed. Adjust the regex/CSS, re-run.
4. **Do not** fall back to manual at this stage — the evidence is in hand. Only escalate to [Manual Fallback](#manual-fallback) if the same selector fails after 2–3 targeted attempts OR Step 1 reported `chrome-missing`.

### Codegen-first when authoring new selectors

When you need a new selector (a portal element the script doesn't currently address) or an existing one breaks beyond a quick fix, **do not guess**. Run Playwright Codegen against the live portal:

```bash
npx playwright codegen https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth
```

Playwright opens an inspector that records every click and emits the exact `getByRole` / `locator` calls. Copy the relevant ones into the script with a comment naming the date verified — for example:

```js
// captured via codegen 2026-04-15; if this fails, re-run codegen against the live portal
const someBtn = page.getByRole('button', { name: 'Some Label' });
```

This replaces the failure mode of "guess → fail → screenshot → guess again" with evidence from Playwright's own inspector.

---

## Manual Fallback

If Playwright automation is not possible (Chrome missing, portal UI changed, script fails repeatedly), provide the user with the relevant instructions from the sections below.

### Creating a New External Application

1. Go to `https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth`
2. Click **"Add application"**
3. Set the **Application name** to `<app name>`
4. Select **"Non-Confidential application"** (required for browser/PKCE flow)
5. For each required resource category, click **"Add scopes"**, select the resource from the dropdown, check the required scopes, and confirm
6. Add the localhost redirect URIs (with and without trailing slash — e.g. `http://localhost:5173` and `http://localhost:5173/`) in the **Redirect URL** field, pressing Enter after each. Production URIs will be registered automatically by `uip codedapp deploy`.
7. Click **"Add"** and copy the generated **Application ID** (a UUID) — this is the Client ID
8. Paste the Client ID back to the AI agent

### Adding Redirect URIs to an Existing App

1. Go to `https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth`
2. Paste the first 8 characters of your Client ID (from `.env` → `VITE_UIPATH_CLIENT_ID`) into the search box to filter the list. Use a **prefix**, not the full UUID — the Application ID column is truncated, so full-UUID matching fails. Filtering by Client-ID prefix is also the only reliable disambiguator when multiple apps share the same display name.
3. Click the **pencil Edit icon** at the right of the row (clicking the row text itself does not open the edit form)
4. In the **Redirect URL** field, enter each new URI (with and without trailing slash) and press Enter after each
5. Click **"Save"**
6. Confirm back to the agent once saved

### Adding Scopes to an Existing App

1. Go to `https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth`
2. Paste the first 8 characters of your Client ID into the search box. Use a **prefix**, not the full UUID — the Application ID column is truncated, so full-UUID matching fails. Filtering by Client-ID prefix is also the only reliable disambiguator when multiple apps share the same display name.
3. Click the **pencil Edit icon** at the right of the row (clicking the row text itself does not open the edit form)
4. For each resource you need to add scopes for, look at the list of already-attached resources in the app's edit view:
   - **If the resource is already listed** (e.g. `UiPath.Orchestrator` is already on the app and you're adding another `OR.*` scope to it): click the **pencil Edit icon next to that resource's row**. A dialog opens showing the existing scope checkboxes pre-selected — check the additional scopes you need, then confirm. Do **not** click "Add scopes" for a resource that's already attached; the resource will be missing from that dropdown.
   - **If the resource is not yet listed**: click **"Add scopes"**, select the resource from the dropdown (see mapping table below), check the required scopes, click the confirm button.
5. Repeat for each resource category
6. Click **"Save"** on the app form
7. **Also update `VITE_UIPATH_SCOPE` in `.env`** to include the new scopes — both sides must match
8. Clear browser storage and re-test

### Scope → Resource Mapping Reference

| SDK Scope(s) | Resource (dropdown label) | Attached-list label | Safe `--scopes-by-resource` key |
|---|---|---|---|
| `OR.Assets`, `OR.Administration`, `OR.Execution`, `OR.Execution.Read`, `OR.Jobs`, `OR.Queues`, `OR.Tasks` | **Orchestrator API Access** | `UiPath.Orchestrator` | `Orchestrator` |
| `DataFabric.Schema.Read`, `DataFabric.Data.Read`, `DataFabric.Data.Write` | **Data Fabric API** | `DataFabric` | `DataFabric` |
| `PIMS` | **Maestro API Access** | `Maestro` (or similar) | `Maestro` |
| `ConversationalAgents` | **Conversational Agents** | varies | `Conversational` |
| `Traces.Api` | **Traces API Access** | varies | `Traces` |

> **Three different label spaces — pick the right one for the right place:**
> - The **scope** (column 1) is what goes into `VITE_UIPATH_SCOPE` in `.env`.
> - The **dropdown label** (column 2) is what you click in the portal's "Add scopes" resource selector.
> - The **attached-list label** (column 3) is what the portal shows on the row of an *already-attached* resource inside the app's edit view.
> - The **`--scopes-by-resource` key** (column 4) is what you pass to the script. Use the **shortest substring that matches both the dropdown label and the attached-list label** — that way the script can locate the row whether the resource is being added fresh (matches the dropdown) or already attached (matches the attached-list label). The script also has a first-word fallback if the literal key doesn't match.
>
> **Example:** `--scopes-by-resource '{"Orchestrator":["OR.Tasks.Read"]}'` works whether `Orchestrator API Access` is in the dropdown or `UiPath.Orchestrator` is already attached. `'{"Orchestrator API Access":[...]}'` only works for the dropdown, not the attached row.
