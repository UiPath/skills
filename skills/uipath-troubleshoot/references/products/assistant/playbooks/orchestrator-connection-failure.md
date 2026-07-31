---
confidence: medium
---

# Assistant Cannot Connect to Orchestrator

## Context

The user is signed in but the Assistant cannot reach/attach to its Orchestrator tenant — stays Offline, "Connecting…" never resolves, or drops to disconnected. Distinct from sign-in (`sign-in-failure.md`): the identity step succeeded, the Orchestrator attach did not.

What this looks like:
- `combined.log`: `/robot/connectToServer` invoked (often repeated); `Finished running handler` with `result: false`/`null`; `robotStatus` transitions to Offline/Disconnected.
- `Robot.log`: a trace in `CloudConnectFlow` (e.g. `CloudConnectFlow.TryOpenFlow`) or the connect path; `TaskCanceledException` / `HttpClient.Timeout`, `HttpRequestException`, or an HTTP `401` / `403` against an Orchestrator URL (`/odata/*`, `/api/*`).
- The Orchestrator host in `Robot.log` — cloud (`cloud.uipath.com`) or an on-prem URL.

What can cause it:
1. **Orchestrator unreachable** — `TaskCanceledException` / `HttpClient.Timeout` / `HttpRequestException` reaching the Orchestrator host: network (VPN/proxy/firewall/DNS), or on-prem Orchestrator down.
2. **Machine/robot not authorized** — `401` / `403`: the machine key / robot is not registered to the tenant/folder, or the license/robot assignment is missing.
3. **Wrong Orchestrator URL** — the connect target host is not the tenant the user belongs to (stale or mistyped on-prem URL).
4. **TLS/certificate** — on-prem with a self-signed or untrusted cert: TLS handshake failure in the connect trace.

What to look for:
- Transport error vs HTTP status — same split as sign-in; it decides cause 1 vs 2.
- Whether sign-in itself succeeded (rules this in vs `sign-in-failure.md`).

## Investigation

1. Confirm sign-in succeeded (`interactiveConnectSignIn` result true earlier in `combined.log`); if not, go to `sign-in-failure.md` first.
2. Find `/robot/connectToServer` in `combined.log` and note the timestamp and `result`.
3. In `Robot.log` (timezone-convert), read the `CloudConnectFlow` trace at that timestamp:
   - Transport exception, no HTTP status → cause 1.
   - `401` / `403` from the Orchestrator host → cause 2.
   - TLS/cert error → cause 4.
   - Endpoint host ≠ expected tenant → cause 3.
4. For a `401`/`403` (cause 2), the Orchestrator side is the authority — cross-reference the `orchestrator` domain (machine/robot registration, license) before concluding.
5. For cause 1, ask the user to `curl -v https://<orchestrator-host>/api/status` from the machine to isolate DNS / proxy / firewall / server-down.

## Resolution

- **Cause 1 (unreachable):** restore connectivity to the Orchestrator host (VPN, proxy/firewall allowlist, DNS); for on-prem, confirm the Orchestrator service is up. Re-test with the `curl` above.
- **Cause 2 (`401`/`403`):** register/assign the machine and robot to the correct tenant/folder and confirm an available license — resolve via the `orchestrator` domain, then reconnect.
- **Cause 3 (wrong URL):** correct the Orchestrator URL in Assistant → Preferences and reconnect.
- **Cause 4 (TLS/cert):** install the on-prem Orchestrator's certificate chain into the machine trust store (or fix the server cert); reconnect.
