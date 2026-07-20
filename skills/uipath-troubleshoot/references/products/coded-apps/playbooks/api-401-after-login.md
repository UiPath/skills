---
confidence: high
---

# API Call Fails 401 After Login

## Context

What this looks like:
- The app authenticates and renders, then an SDK call to `https://api.uipath.com/...` returns `HTTP 401 Unauthorized` (visible in the network tab or a caught SDK error)
- The failure is on a specific API call, **after** a successful login — not an OAuth `error=` on the callback URL (that is [invalid-scope.md](./invalid-scope.md))

What can cause it:
- The access token lacks the scope required by the API being called
- A scope was added to `uipath.json` and to the External Application, but the **current token was minted before the change** — the browser still holds the old token
- The token expired and was not refreshed

What to look for:
- **Discriminator: 401 vs 403.** `401 Unauthorized` = token/scope problem (this playbook). `403 Forbidden` = the token is valid but the caller lacks folder access or the `UIPATH_FOLDER_KEY` is wrong/missing — that is a different cause; do NOT apply the scope fix below to a 403.
- Which API call returns 401 (the endpoint path identifies the SDK service, and therefore the scope it needs)
- Whether the required scope is present in `uipath.json` AND registered on the External Application

## Investigation

1. Identify the 401'ing request in the network tab — the URL path maps to an SDK service (e.g. `/odata/Assets` → `Assets`, `/odata/Tasks` → `Tasks`). Confirm the status is `401`, not `403`.

2. Determine the scope that service requires (see the mapping in [invalid-scope.md](./invalid-scope.md) § Investigation).

3. Check the scope is requested by the app and allowed by the client:

   ```bash
   cat uipath.json                                   # scope field — what the app requests
   uip admin external-apps get <client-id> --output json --output-filter "scopes"
   ```

## Resolution

- **If the required scope is missing from the External Application:** register it (public PKCE client → `--user-scope`, which replaces the list — pass the full set), add it to `uipath.json` `scope`, then clear browser storage and re-authenticate:

  ```bash
  uip admin external-apps update <client-id> \
    --user-scope '<existing-scopes>,<missing-scope>' \
    --output json
  ```

- **If the scope is already registered and in `uipath.json` but the call still 401s:** the live token predates the scope. Clear browser storage (localStorage/sessionStorage/cookies) and re-authenticate so a fresh token carries the scope.

- **If the token simply expired:** clear browser storage and re-authenticate.

- **If the status is actually 403, not 401:** stop — this is a folder/permission issue, not a scope issue. Verify `UIPATH_FOLDER_KEY` is set to a folder the authenticated user can access, and that the user has the required Orchestrator role.
