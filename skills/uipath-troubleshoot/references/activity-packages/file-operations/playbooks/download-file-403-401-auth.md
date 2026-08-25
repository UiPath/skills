---
confidence: medium
---

# Download File from URL — HTTP 403 (Forbidden) / 401 (Unauthorized)

## Context

What this looks like:
- `Download File from URL` faults with an HTTP error — `403 (Forbidden)` or `401 (Unauthorized)` (often surfaced as `The remote server returned an error: (403) Forbidden.`).
- The same URL may download fine in a **browser** where you are logged in.

What can cause it:
- **The native download carries no authentication.** `Download File from URL` issues a plain HTTP request — it does **not** send the browser's cookies, session, or interactive sign-in state. A URL behind an authenticated portal therefore returns 401/403.
- **Missing / blocked `User-Agent`.** Some servers reject requests without a recognized browser `User-Agent`, returning 403.

What to look for:
- Whether the URL sits behind a login / portal (works in a logged-in browser, fails for the robot).
- The status code: `401` → authentication required; `403` → forbidden (auth, or a `User-Agent`/policy block).
- Whether `UserAgentHeader` is set on the activity.

## Investigation

1. Read the error from job evidence; confirm it is an HTTP `401`/`403` at `Download File from URL` (not a DNS host error, an `HttpClient` loop error, or a file-finalize error).
2. Establish whether the URL requires authentication (does it work only in a signed-in browser?).
3. Read the activity's `UserAgentHeader` — is it set?

## Resolution

- **If the server only needs a browser identity (some 403s):** set `UserAgentHeader` to a real browser user-agent string and re-run.
- **If the URL is behind authentication (401 / portal 403):** the native download cannot carry the sign-in. Download through an **authenticated UI browser session** instead — use a `Click` on the page's download element, enclosed in a **Wait for Download** container, so the file is captured through the logged-in Chrome/Edge session. (Alternatively, if the API supports it, supply the required auth header/token via an HTTP Request activity.)
- **Confirm:** after authenticating (or switching to the browser-download path), the server returns the file instead of 401/403.
