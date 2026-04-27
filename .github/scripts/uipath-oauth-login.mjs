/**
 * Headless OAuth login for Helm E2E tests.
 * Automates the UiPath Identity authorization code + PKCE flow via Puppeteer,
 * producing a user-scoped token that carries cloud entitlements.
 *
 * Uses Puppeteer (WebSocket debugging) instead of Playwright (pipe debugging)
 * because self-hosted CI agents block the stdio pipe that Playwright requires.
 *
 * Environment variables:
 *   AUTHORITY  - UiPath Identity authority URL (default: https://staging.uipath.com)
 *   EMAIL      - UiPath account email
 *   PASSWORD   - UiPath account password
 *   TENANT     - Target tenant name (default: DefaultTenant)
 *   ORG        - Target org slug for org-selection page (optional)
 *   HEADLESS   - Set to "false" to show the browser (default: true)
 */
import puppeteer from "puppeteer";
import { createServer } from "http";
import { randomBytes, createHash } from "crypto";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const AUTHORITY = process.env.AUTHORITY || "https://staging.uipath.com";
const EMAIL = process.env.EMAIL;
const PASSWORD = process.env.PASSWORD;
if (!EMAIL || !PASSWORD) {
  console.error("EMAIL and PASSWORD environment variables are required.");
  process.exit(1);
}

const CLIENT_ID = "36dea5b8-e8bb-423d-8e7b-c808df8f1c00";
const REDIRECT_PORT = 8104;
const REDIRECT_URI = `http://localhost:${REDIRECT_PORT}/oidc/login`;
const SCOPES = [
  "offline_access", "ProcessMining", "OrchestratorApiUserAccess",
  "StudioWebBackend", "IdentityServerApi", "ConnectionService",
  "DataService", "DocumentUnderstanding", "EnterpriseContextService",
  "Directory", "JamJamApi", "LLMGateway", "LLMOps", "OMS",
  "RCS.FolderAuthorization", "TM.Projects", "TM.TestCases",
  "TM.Requirements", "TM.TestSets", "AutomationSolutions",
  "StudioWebTypeCacheService", "Docs.GPT.Search",
].join(" ");
const HEADLESS = process.env.HEADLESS !== "false";

function base64url(buf) {
  return buf.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function generatePKCE() {
  const verifier = base64url(randomBytes(32));
  const challenge = base64url(createHash("sha256").update(verifier).digest());
  return { verifier, challenge };
}

/** Where to drop screenshots + DOM dumps for post-mortem. */
function debugDir() {
  return process.env.AUTH_DEBUG_DIR
    || process.env.BUILD_ARTIFACTSTAGINGDIRECTORY
    || process.env.TEMP
    || "/tmp";
}

/** Screenshot the org-select page + log every clickable / data-cy element. */
async function dumpOrgSelectDom(page) {
  try {
    const dir = debugDir();
    mkdirSync(dir, { recursive: true });
    const ssPath = join(dir, "auth-debug-orgselect.png");
    await page.screenshot({ path: ssPath, fullPage: true });
    console.log(`Org-select screenshot: ${ssPath}`);
  } catch (err) {
    console.error(`Org-select screenshot failed: ${err.message}`);
  }
  try {
    const items = await page.evaluate(() => {
      const out = [];
      const els = document.querySelectorAll(
        'a, button, [role="link"], [role="button"], [data-cy], [data-test-id]'
      );
      for (const el of els) {
        const text = el.textContent?.trim().replace(/\s+/g, " ").slice(0, 80) || "";
        out.push({
          tag: el.tagName.toLowerCase(),
          text,
          href: el.getAttribute("href"),
          dataCy: el.getAttribute("data-cy"),
          dataTestId: el.getAttribute("data-test-id"),
          ariaLabel: el.getAttribute("aria-label"),
        });
      }
      return out;
    });
    console.log(`Org-select clickable elements (${items.length}):`);
    for (const it of items) {
      console.log(
        `  [${it.tag}] data-cy=${it.dataCy} data-test-id=${it.dataTestId} ` +
        `aria-label=${JSON.stringify(it.ariaLabel)} href=${it.href} text=${JSON.stringify(it.text)}`
      );
    }
  } catch (err) {
    console.error(`Org-select DOM dump failed: ${err.message}`);
  }
}

/** Start HTTP server and return a promise that resolves with the auth code. */
function startCallbackServer() {
  return new Promise((resolve, reject) => {
    const server = createServer((req, res) => {
      const url = new URL(req.url, `http://localhost:${REDIRECT_PORT}`);
      if (url.pathname === "/oidc/login") {
        const code = url.searchParams.get("code");
        const st = url.searchParams.get("state");
        const error = url.searchParams.get("error");
        if (error) {
          res.writeHead(200);
          res.end("Login failed: " + error);
          server.close();
          reject(new Error("OAuth error: " + error));
          return;
        }
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end("<html><body><h2>Login successful!</h2></body></html>");
        server.close();
        resolve({ authCode: code, returnedState: st });
      }
    });
    server.listen(REDIRECT_PORT, () => {
      console.log(`Callback server listening on port ${REDIRECT_PORT}`);
    });
    server.on("error", reject);
  });
}

async function main() {
  const { verifier, challenge } = generatePKCE();
  const state = base64url(randomBytes(16));

  // 1. Start callback server
  const callbackPromise = startCallbackServer();

  // 2. Build authorization URL
  const authUrl = new URL(`${AUTHORITY}/identity_/connect/authorize`);
  authUrl.searchParams.set("client_id", CLIENT_ID);
  authUrl.searchParams.set("redirect_uri", REDIRECT_URI);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("scope", SCOPES);
  authUrl.searchParams.set("state", state);
  authUrl.searchParams.set("code_challenge", challenge);
  authUrl.searchParams.set("code_challenge_method", "S256");

  // 3. Launch browser via Puppeteer (uses WebSocket, not pipes)
  console.log(`Launching browser (headless=${HEADLESS})...`);
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: HEADLESS,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
      defaultViewport: { width: 1920, height: 1080 },
    });
  } catch (err) {
    console.error("FATAL: Failed to launch browser:", err.message);
    process.exit(1);
  }
  console.log("Browser launched successfully.");

  const page = (await browser.pages())[0] || await browser.newPage();

  try {
    // Pre-seed OneTrust cookie to dismiss cookie banner
    await page.setCookie(
      { name: "OptanonAlertBoxClosed", value: new Date().toISOString(), domain: ".uipath.com", path: "/" },
      { name: "OptanonConsent", value: `isIABGlobal=false&datestamp=${new Date().toISOString()}&groups=1:1,2:1,3:1,4:1`, domain: ".uipath.com", path: "/" },
    );

    console.log("Navigating to authorization URL...");
    await page.goto(authUrl.toString(), { waitUntil: "networkidle2", timeout: 30000 });
    console.log(`Page loaded: ${page.url()}`);

    // Fill in the login form using the same data-cy selectors as Robot integration tests
    console.log("Waiting for sign-in page...");
    await page.waitForSelector("button[data-cy='authorize-with-email']", { timeout: 30000 });
    console.log("Cloud sign-in page detected.");
    await page.click("button[data-cy='authorize-with-email']");

    await page.waitForSelector("input[data-cy='login-email-input']", { timeout: 10000 });
    // Triple-click to select all, then type to replace any existing text
    await page.click("input[data-cy='login-email-input']", { clickCount: 3 });
    await page.type("input[data-cy='login-email-input']", EMAIL);

    await page.waitForSelector("input[data-cy='login-password-input']", { timeout: 10000 });
    await page.click("input[data-cy='login-password-input']", { clickCount: 3 });
    await page.type("input[data-cy='login-password-input']", PASSWORD);

    console.log("Submitting credentials...");
    await Promise.all([
      page.waitForNavigation({ waitUntil: "networkidle2", timeout: 30000 }),
      page.click("button[data-cy='login-button']"),
    ]);

    // Handle organization selection if the user belongs to multiple orgs.
    // Originally a single `a[href*="${ORG}"]` selector — that worked on
    // staging but matches nothing on alpha (different DOM). Replaced with
    // a selector cascade + diagnostic dump so the next failure tells us
    // exactly what to target.
    const TARGET_ORG = process.env.ORG;
    let onOrgSelect = false;
    try {
      await page.waitForFunction(
        () => window.location.href.includes("organization-select"),
        { timeout: 15000 }
      );
      onOrgSelect = true;
    } catch {
      console.log("Org-select page not detected within 15s — assuming single-org auto-redirect.");
    }

    if (onOrgSelect) {
      console.log(`Organization selection detected (target=${TARGET_ORG || "<unset>"}). Dumping DOM…`);
      await dumpOrgSelectDom(page);

      if (!TARGET_ORG) {
        throw new Error("Org-select page appeared but ORG env var is empty. Set ORG to the target org slug.");
      }

      // Try CSS selectors in order from most specific to most permissive.
      const cssSelectors = [
        `a[href*="${TARGET_ORG}"]`,
        `[data-cy*="${TARGET_ORG}"]`,
        `[data-test-id*="${TARGET_ORG}"]`,
        `[aria-label*="${TARGET_ORG}"]`,
      ];
      let clicked = false;
      for (const sel of cssSelectors) {
        const el = await page.$(sel);
        if (el) {
          console.log(`Picking org via CSS selector: ${sel}`);
          await Promise.all([
            page.waitForNavigation({ waitUntil: "networkidle2", timeout: 30000 }).catch(() => {}),
            el.click(),
          ]);
          clicked = true;
          break;
        }
      }

      // Last-resort: text-content match on any clickable element.
      if (!clicked) {
        const matched = await page.evaluate((org) => {
          const candidates = document.querySelectorAll(
            'a, button, [role="link"], [role="button"], [data-cy], [class*="org"]'
          );
          for (const el of candidates) {
            const t = el.textContent?.trim();
            if (t && (t === org || t.toLowerCase() === org.toLowerCase() || t.includes(org))) {
              el.scrollIntoView();
              el.click();
              return true;
            }
          }
          return false;
        }, TARGET_ORG);
        if (matched) {
          console.log(`Picked org via text-content match for "${TARGET_ORG}".`);
          // Give the SPA a moment to navigate.
          await new Promise(r => setTimeout(r, 2000));
          clicked = true;
        }
      }

      if (!clicked) {
        throw new Error(
          `Could not find a clickable element for org "${TARGET_ORG}" on alpha's org-select page. ` +
          `See the DOM dump above and the screenshot saved to AUTH_DEBUG_DIR.`
        );
      }
    }

    console.log("Waiting for OAuth callback...");
    await page.waitForFunction(
      (port) => window.location.href.startsWith(`http://localhost:${port}/`),
      { timeout: 60000 },
      REDIRECT_PORT
    );
    console.log("Redirect received!");
  } catch (err) {
    try {
      const dir = debugDir();
      mkdirSync(dir, { recursive: true });
      const screenshotPath = join(dir, "auth-debug-error.png");
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.error(`Error screenshot: ${screenshotPath}`);
      console.error(`Current URL: ${page.url()}`);
    } catch (ssErr) {
      console.error(`Could not take screenshot: ${ssErr.message}`);
    }
    throw err;
  } finally {
    await browser.close();
  }

  // 4. Wait for the callback server to receive the auth code
  const { authCode, returnedState } = await callbackPromise;

  if (returnedState !== state) {
    throw new Error(`State mismatch: expected ${state}, got ${returnedState}`);
  }

  // 5. Exchange authorization code for tokens
  console.log("Exchanging authorization code for tokens...");
  const tokenResponse = await fetch(`${AUTHORITY}/identity_/connect/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: authCode,
      redirect_uri: REDIRECT_URI,
      client_id: CLIENT_ID,
      code_verifier: verifier,
    }),
  });

  const tokenData = await tokenResponse.json();
  if (!tokenResponse.ok) {
    throw new Error(`Token exchange failed: ${JSON.stringify(tokenData)}`);
  }

  console.log("Token acquired!");
  const accessToken = tokenData.access_token;
  const refreshToken = tokenData.refresh_token;

  // Decode JWT to extract org ID
  const payload = JSON.parse(
    Buffer.from(accessToken.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"), "base64").toString()
  );
  const orgId = payload.prt_id || payload.prtId || payload.organizationId;
  console.log(`Organization ID: ${orgId}, User: ${payload.sub}`);

  // Fetch org/tenant info
  const info = await (await fetch(
    `${AUTHORITY}/${orgId}/portal_/api/filtering/leftnav/tenantsAndOrganizationInfo`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  )).json();

  const orgName = info.organization?.name || "unknown";
  const TARGET_TENANT = process.env.TENANT || "DefaultTenant";
  const tenant = info.tenants?.find(t => t.name === TARGET_TENANT) || info.tenants?.[0];
  if (tenant?.name !== TARGET_TENANT) {
    console.warn(`WARNING: Tenant '${TARGET_TENANT}' not found, fell back to '${tenant?.name}'`);
  }
  console.log(`Organization: ${orgName}, Tenant: ${tenant?.name}`);

  // Write ~/.uipath/.auth
  const authDir = join(process.env.USERPROFILE || process.env.HOME, ".uipath");
  mkdirSync(authDir, { recursive: true });
  const authFile = join(authDir, ".auth");
  writeFileSync(authFile, [
    `UIPATH_ACCESS_TOKEN=${accessToken}`,
    `UIPATH_REFRESH_TOKEN=${refreshToken || ""}`,
    `UIPATH_URL=${AUTHORITY}`,
    `UIPATH_ORGANIZATION_ID=${orgId}`,
    `UIPATH_ORGANIZATION_NAME=${orgName}`,
    `UIPATH_TENANT_ID=${tenant?.id || ""}`,
    `UIPATH_TENANT_NAME=${tenant?.name || ""}`,
  ].join("\n"), "utf8");

  console.log(`Auth file written to ${authFile}`);
}

main().catch((err) => {
  console.error("FAILED:", err.message);
  if (err.stack) console.error(err.stack);
  process.exit(1);
});
