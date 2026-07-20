---
confidence: high
---

# redirect_uri_mismatch / Login Loop

## Context

What this looks like:
- After clicking sign-in, the browser reaches UiPath and shows an error page or a URL containing `error=redirect_uri_mismatch`
- Login "loops" — the app redirects to UiPath, UiPath redirects back, and the app immediately sends the user to sign in again without ever authenticating
- The OAuth `authorize` request in the network tab carries a `redirect_uri=` query parameter that UiPath rejects

What can cause it:
- The `redirectUri` in `uipath.json` (injected as the `uipath:redirect-uri` meta tag) is **not registered** on the External Application
- Trailing-slash mismatch — the app sends `http://localhost:5173` but only `http://localhost:5173/` is registered (or vice versa)
- Wrong port — dev server runs on a non-default port (`vite.config.ts` → `server.port`) but `redirectUri` / the registered URI still says `5173`
- Production URL missing after deploy — `uip codedapp deploy` normally registers the production redirect URI; if it didn't, the deployed app has no matching registered URI

What to look for:
- The **exact** `redirect_uri` value in the failing authorize request (including scheme, port, and trailing slash)
- Whether that value appears — byte-for-byte — in the registered redirect URIs from `uip admin external-apps get`

## Investigation

1. Read what the app sends. From `uipath.json`, note `redirectUri` and `clientId`:

   ```bash
   cat uipath.json
   ```

2. Read what the External Application allows:

   ```bash
   uip admin external-apps get <client-id> --output json \
     --output-filter "redirectUris"
   ```

3. Compare byte-for-byte. The value from step 1 (and the URL the browser is actually served at) must match a registered URI **exactly**, including the trailing slash. For a deployed app, the required redirect URI is the `appUrl` from `.uipath/app.config.json` (web apps) or `https://cloud.uipath.com/<org>/<tenant>/actions_` (action apps).

## Resolution

> `--redirect-uri` on `update` **replaces** the entire registered list — always pass the complete set (existing URIs from step 2 **plus** the missing one).

- **If the local dev URI is not registered:** register both slash variants alongside the existing URIs:

  ```bash
  uip admin external-apps update <client-id> \
    --redirect-uri '<existing-uris>,http://localhost:5173,http://localhost:5173/' \
    --output json
  ```

- **If the dev server runs on a non-default port:** set `redirectUri` in `uipath.json` to the actual URL, restart the dev server, and register that URL (both slash variants) with the `update` command above.

- **If the production URI is missing after deploy:** re-run `uip codedapp deploy` (it registers the production redirect URI). If it still isn't registered, add the `appUrl` from `.uipath/app.config.json` with the `update` command above.

- **If `uipath.json` `redirectUri` doesn't match the URL the app is served at:** fix `redirectUri` to the served URL and restart the dev server so the `uipath:redirect-uri` meta tag is re-injected.

After any change, clear browser storage (stale PKCE state) and re-authenticate.
