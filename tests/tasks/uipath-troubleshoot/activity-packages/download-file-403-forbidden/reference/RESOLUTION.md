# Final Resolution

---

**Root Cause:** `Download File from URL` performs a **native HTTP request** that
does not carry the browser's cookies, session, or interactive sign-in. The target
report URL (`https://portal.example.com/reports/q3-summary.xlsx`) is behind the
portal's authentication, so the server rejects the unauthenticated robot request
with `HTTP 403 (Forbidden)`. The same link works in the user's logged-in browser
because that request carries the session.

**What went wrong:** The `PortalFetch` job (started 2026-06-16T10:02:19Z) faulted
~2 seconds in at `Download File from URL` with `The remote server returned an
error: (403) Forbidden.` (`HttpRequestException`) for the portal URL. The user
confirms the link only works after signing in to the portal.

**Why:** `DownloadFileFromUrl` is not a browser — it sends a plain HTTP GET with
no auth context (and, by default, no special `User-Agent`). Servers that require
authentication (or a recognized browser identity) return `401`/`403` to such
requests. A `403` here means the request reached the server and was refused
(authorization), not a DNS/host failure and not an `HttpClient` lifecycle error.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PortalFetch -- Faulted at 2026-06-16T10:02:21.480Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Portal Sync (key `fa020002-d4e5-4f60-8a02-000000000002`)
- Final error: `Download File from URL: The remote server returned an error: (403) Forbidden.` (`System.Net.Http.HttpRequestException`) -> `Main.xaml` -> `DownloadFileFromUrl "Download File from URL"`

### File Operations (Root Cause)
- Activity surface: `UiPath.Activities.System.FileOperations.DownloadFileFromUrl`, `Url=https://portal.example.com/reports/q3-summary.xlsx`, no `UserAgentHeader`/auth.
- The server returned `403` (the request reached it and was refused) — an auth problem, distinct from a DNS host error or an HttpClient loop error. The URL works only in a signed-in browser.

---

**Immediate fix:**

Give the request the identity/auth the server requires, or fetch via the browser.

### Fix path A -- download through an authenticated UI browser session (preferred for portal-gated URLs)
The native download cannot carry the portal login. Use the **logged-in browser**:
`Click` the page's download element inside a **Wait for Download** container so the
file is captured through the authenticated Chrome/Edge session.

### Fix path B -- supply the required identity/auth
- If the server only needs a browser identity (some 403s), set `UserAgentHeader`
  to a real browser user-agent string and re-run.
- If the resource has an API/token, fetch it with an HTTP Request activity that
  sends the required auth header/token.

### Verification (hand to the user - off-host)
Confirm the URL requires a portal login (works only in a signed-in browser);
after switching to the browser-download path (or supplying auth), the file is
returned instead of `403`.

- **Source:** `file-operations/playbooks/download-file-403-401-auth.md`

---

**Preventive fix:**

1. **Method choice** -- for portal/authenticated downloads, drive the logged-in
   browser (Click + Wait for Download) or call an authenticated API; reserve
   `Download File from URL` for public/direct URLs.
   - **Why:** The native download can't carry interactive auth, so gated URLs
     return 401/403.
   - **Who:** RPA developer.

2. **User-Agent** -- set `UserAgentHeader` when a server filters by user-agent.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The portal URL requires authentication the native Download File from URL can't carry, so the server returns 403 | High | Confirmed | Yes | `(403) Forbidden` at Download File from URL for a portal URL; works only in a signed-in browser; no UserAgentHeader/auth | Download via an authenticated UI browser session (Click + Wait for Download), or supply auth / UserAgentHeader |

---

Would you like help switching to a browser-based download (Click + Wait for
Download), or cleaning up the `.local/investigations/` folder?
