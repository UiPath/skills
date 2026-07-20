---
confidence: medium
---

# Assistant Sign-In Fails

## Context

The user clicks sign in to UiPath cloud/Identity from the Assistant and it never completes — spins, returns to the signed-out state, or shows an auth error toast.

What this looks like:
- `combined.log`: the `/robot/interactiveConnectSignIn` IPC route invoked, often repeated within seconds; `Finished running handler` with `result: false`/`null`; `robotUserStatus` stays Offline.
- `Robot.log`: a stack trace in `InteractiveConnectFlow.SignIn` (namespace `UiPath.Service.*`); a failing call to `/identity_/*` or `/discovery_*`; `HttpRequestException`, `TaskCanceledException`, or an HTTP `401` / `403`.
- Exact on-screen text if the user can supply it (e.g. "We couldn't sign you in").

What can cause it:
1. **Cloud/Identity unreachable** — `HttpRequestException` / `TaskCanceledException` on `/discovery_*` or `/identity_/*`: DNS, VPN, proxy, or firewall between the machine and Identity.
2. **Auth rejected** — `401` / `403` from Identity: expired/invalid token, MFA/Conditional Access the desktop flow can't satisfy, or the account lacks tenant access.
3. **Wrong/stale environment** — the endpoint host in `Robot.log` is not the tenant the user expects (e.g. `staging.uipath.com` for a production user), or a stale cached URL.
4. **Browser-callback not returned** — the system browser completed sign-in but the redirect never reached the Assistant (default-browser/protocol-handler issue) — the DevTools console / no callback line is the tell.

What to look for:
- Which endpoint host `Robot.log` calls, and whether it resolves at all.
- Whether the failure is a transport error (cause 1) or an HTTP status (cause 2) — that split drives everything.

## Investigation

1. Anchor: confirm the user was signing in (not connecting to an already-signed-in Orchestrator — that is `orchestrator-connection-failure.md`).
2. In `combined.log`, find `/robot/interactiveConnectSignIn` and its `result`. Note the timestamp.
3. In `Robot.log` (timezone-convert first), read the `InteractiveConnectFlow.SignIn` trace near that timestamp. Classify the failure:
   - Transport exception (`TaskCanceledException` / `HttpRequestException`, no HTTP status) → cause 1.
   - HTTP `401` / `403` → cause 2.
   - Endpoint host ≠ expected tenant → cause 3.
   - No server-side trace at all, but the browser opened → cause 4; ask for DevTools console.
4. For cause 1, ask the user to `curl -v https://<host>/identity_/.well-known/openid-configuration` (or `nslookup <host>`) from the same machine to separate DNS / proxy / firewall.

## Resolution

- **Cause 1 (unreachable):** restore connectivity to the endpoint host — connect VPN, whitelist the host in the proxy/firewall, or fix DNS. Re-test with the `curl` above before retrying sign-in.
- **Cause 2 (`401`/`403`):** confirm the account has access to the tenant and is not blocked by MFA/Conditional Access for the desktop flow; sign out fully and back in to refresh the token. If Conditional Access blocks it, exempt the desktop app flow per org policy.
- **Cause 3 (wrong environment):** point the Assistant at the correct Orchestrator/cloud URL (Assistant → Preferences → Orchestrator settings) and sign in again.
- **Cause 4 (callback lost):** set the correct default browser / re-register the `uipath://` protocol handler; retry. File a UX bug if the app hangs silently instead of surfacing the lost callback.
