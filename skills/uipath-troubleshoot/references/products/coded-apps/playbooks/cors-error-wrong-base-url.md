---
confidence: high
---

# CORS Error on API Call

## Context

What this looks like:
- The browser console shows a CORS failure on an SDK request, e.g.:
  ```
  Access to fetch at 'https://cloud.uipath.com/...' from origin 'http://localhost:5173'
  has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
  on the requested resource.
  ```
- The blocked request targets `cloud.uipath.com` (the portal domain), not `api.uipath.com`
- The request fails in the browser before any HTTP status is returned (preflight/opaque failure), so there is no 401/403/404 to inspect

What can cause it:
- `baseUrl` in `uipath.json` (injected as the `uipath:base-url` meta tag) points at the **portal domain** (`cloud.uipath.com`) instead of the **API subdomain** (`api.uipath.com`). The portal domain does not return `Access-Control-Allow-Origin` for browser XHR/fetch, so every SDK call is blocked.

What to look for:
- The host in the blocked request URL — if it is `cloud.uipath.com` (or `staging.uipath.com` / `alpha.uipath.com`), the base URL is wrong
- The `baseUrl` value in `uipath.json`

## Investigation

1. Read `baseUrl` from `uipath.json`:

   ```bash
   cat uipath.json
   ```

2. Confirm the blocked request host in the console error matches the (wrong) portal domain from `baseUrl`.

## Resolution

- **Set `baseUrl` in `uipath.json` to the API subdomain**, then restart the dev server so the plugin re-injects the `uipath:base-url` meta tag:

  | Environment | Correct (`baseUrl`) | Wrong |
  |-------------|---------------------|-------|
  | cloud | `https://api.uipath.com` | `https://cloud.uipath.com` |
  | staging | `https://staging.api.uipath.com` | `https://staging.uipath.com` |
  | alpha | `https://alpha.api.uipath.com` | `https://alpha.uipath.com` |

After restarting, re-test. The API subdomain returns the CORS headers the browser requires.
