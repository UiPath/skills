# OAuth Client Setup via Playwright CLI

This reference describes how to create a UiPath External Application (OAuth client) using **Playwright CLI** browser automation — the AI writes a Node.js script and runs it via Bash.

## Cloud Host URLs

| Environment | Cloud Host |
|---|---|
| cloud | `https://cloud.uipath.com` |
| staging | `https://staging.uipath.com` |
| alpha | `https://alpha.uipath.com` |

## Prerequisites

You need: `orgName`, `environment` (cloud/staging/alpha), app name, redirect URI(s), and required OAuth scopes.

## Step 1: Check / Install Playwright

Run the following to check if Playwright is available:

```bash
npx playwright --version 2>/dev/null
```

If the command fails or returns no output, install it:

```bash
npm install -D playwright && npx playwright install chromium --with-deps
```

## Step 2: Write the Automation Script

Write the following Node.js script to a temp path (e.g. `/tmp/oauth-setup.mjs`), substituting the real values for `ORG_NAME`, `CLOUD_HOST`, `APP_NAME`, `REDIRECT_URIS`, and `SCOPES_BY_RESOURCE` before writing:

```js
// /tmp/oauth-setup.mjs
import { chromium } from 'playwright';

const CLOUD_HOST = 'https://cloud.uipath.com';   // substitute real value
const ORG_NAME   = 'myorg';                        // substitute real value
const APP_NAME   = 'my-uipath-app';                // substitute real value

// Add both with and without trailing slash for localhost and the production URL
const REDIRECT_URIS = [
  'http://localhost:5173',
  'http://localhost:5173/',
  'https://my-app.example.com',       // substitute real production URL if known
  'https://my-app.example.com/',
];

// Map each resource category to the list of scopes needed within it.
// Keys must exactly match the resource dropdown labels in the UiPath portal.
// Common resource → scope mappings:
//   'UiPath.Orchestrator' → OR.Assets, OR.Administration, OR.Execution, OR.Jobs, OR.Queues, OR.Tasks
//   'Data Fabric API'     → DataFabric.Schema.Read, DataFabric.Data.Read, DataFabric.Data.Write
//   'PIMS'                → PIMS
const SCOPES_BY_RESOURCE = {
  'UiPath.Orchestrator': ['OR.Assets', 'OR.Execution'],  // substitute real scopes
};

const EXTERNAL_APPS_URL = `${CLOUD_HOST}/${ORG_NAME}/portal_/admin/external-apps/oauth`;

async function isOnLoginPage(page) {
  const url = page.url();
  return (
    url.includes('/identity_/') ||
    url.includes('/login') ||
    url.includes('account.uipath.com')
  );
}

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page    = await context.newPage();

  // --- Step 1: Navigate to External Applications page ---
  await page.goto(EXTERNAL_APPS_URL);
  await page.waitForLoadState('networkidle');

  // --- Step 2: Wait for login if required (poll up to 2 minutes) ---
  if (await isOnLoginPage(page)) {
    console.error('Browser opened. Please log in to UiPath Cloud in the browser window.');
    console.error('The script will continue automatically once login is detected.');

    const deadline = Date.now() + 2 * 60 * 1000; // 2 minutes
    let loggedIn = false;
    while (Date.now() < deadline) {
      await page.waitForTimeout(5000);
      if (!(await isOnLoginPage(page))) {
        loggedIn = true;
        break;
      }
    }
    if (!loggedIn) {
      console.error('Timed out waiting for login. Please re-run the script and log in within 2 minutes.');
      await browser.close();
      process.exit(1);
    }

    // Re-navigate to the External Applications page after login
    await page.goto(EXTERNAL_APPS_URL);
    await page.waitForLoadState('networkidle');
  }

  // --- Step 3: Click "Add application" ---
  await page.getByRole('button', { name: /add application/i }).click();
  await page.waitForLoadState('networkidle');

  // --- Step 4a: Fill in application name ---
  const nameInput = page.getByLabel(/application name/i);
  await nameInput.click();
  await nameInput.fill(APP_NAME);

  // --- Step 4b: Select Non-Confidential application ---
  await page.getByLabel(/non-confidential application/i).check();

  // --- Step 4c: Add OAuth scopes by resource category ---
  for (const [resource, scopes] of Object.entries(SCOPES_BY_RESOURCE)) {
    // Open the "Add scopes" dialog
    await page.getByRole('button', { name: /add scopes/i }).last().click();
    await page.waitForSelector('[role="dialog"]');

    // Select the resource in the dropdown
    await page.getByRole('combobox', { name: /resource/i }).click();
    await page.getByRole('option', { name: resource }).click();
    await page.waitForTimeout(500); // wait for scope list to load

    // Check each required scope
    for (const scope of scopes) {
      const scopeCheckbox = page.getByLabel(scope);
      if (await scopeCheckbox.count() > 0) {
        await scopeCheckbox.check();
      } else {
        console.error(`Warning: scope "${scope}" not found for resource "${resource}"`);
      }
    }

    // Confirm / save the resource addition
    await page.getByRole('button', { name: /save|confirm|add/i }).last().click();
    await page.waitForLoadState('networkidle');
  }

  // --- Step 4d: Enter redirect URIs ---
  for (const uri of REDIRECT_URIS) {
    const redirectInput = page.getByPlaceholder(/enter url here/i).last();
    await redirectInput.fill(uri);
    await redirectInput.press('Enter');
    await page.waitForTimeout(300);
  }

  // --- Step 5: Submit the form ---
  await page.getByRole('button', { name: /^add$/i }).click();
  await page.waitForLoadState('networkidle');

  // --- Step 6: Extract the Client ID ---
  // After creation the portal typically shows the new app's detail page or a
  // success dialog containing the Application ID (a UUID).
  let clientId = null;

  // Try to find a UUID-shaped string on the page
  const pageText = await page.innerText('body');
  const uuidMatch = pageText.match(
    /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i
  );
  if (uuidMatch) {
    clientId = uuidMatch[0];
  }

  // If not found on the current page, navigate back to the list and open the app
  if (!clientId) {
    await page.goto(EXTERNAL_APPS_URL);
    await page.waitForLoadState('networkidle');
    await page.getByText(APP_NAME).first().click();
    await page.waitForLoadState('networkidle');
    const detailText = await page.innerText('body');
    const match = detailText.match(
      /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i
    );
    if (match) clientId = match[0];
  }

  await browser.close();

  if (!clientId) {
    console.error('Could not extract Client ID automatically. See the manual fallback section.');
    process.exit(1);
  }

  // Output JSON so the calling AI agent can parse it
  console.log(JSON.stringify({ clientId }));
})();
```

## Step 3: Run the Script

```bash
node /tmp/oauth-setup.mjs
```

The script launches a **visible** (non-headless) Chromium browser so the user can see what is happening and log in if needed. The AI should watch stdout for the JSON result.

## Step 4: Parse the Client ID

The script prints a single JSON line to stdout on success:

```json
{"clientId":"00aee0f6-37c7-4985-8d73-04d3cc36c409"}
```

Parse this to obtain the `clientId` value needed for the `.env` file or `uipath.json` config.

## Step 5: Clean Up

Delete the temporary script after a successful run:

```bash
rm /tmp/oauth-setup.mjs
```

## Handling Script Failures

If the script exits with a non-zero code or does not print valid JSON:

1. Check stderr output for diagnostic messages.
2. Try re-running — the user may not have had time to log in.
3. If the UI has changed (button labels, form layout), update the script's locators and retry.
4. After 2–3 failed attempts, fall back to the manual process below.

---

## Manual Fallback

If Playwright automation is not possible, provide the user with these instructions:

1. Go to `https://{cloudHost}/{orgName}/portal_/admin/external-apps/oauth`
2. Click **"Add application"**
3. Set the **Application name** to `<app name>`
4. Select **"Non-Confidential application"** (required for browser/PKCE flow)
5. For each required resource category, click **"Add scopes"**, select the resource from the dropdown, check the required scopes, and confirm
6. Add all required redirect URIs (with and without trailing slash for both localhost and production URLs) in the **Redirect URL** field, pressing Enter after each
7. Click **"Add"** and copy the generated **Application ID** (a UUID) — this is the Client ID
8. Paste the Client ID back to the AI agent

### Scope → Resource Mapping Reference

| SDK Scope(s) | Select This Resource |
|---|---|
| `OR.Assets`, `OR.Administration`, `OR.Execution`, `OR.Jobs`, `OR.Queues`, `OR.Tasks` | **UiPath.Orchestrator** |
| `DataFabric.Schema.Read`, `DataFabric.Data.Read`, `DataFabric.Data.Write` | **Data Fabric API** |
| `PIMS` | **PIMS** |
