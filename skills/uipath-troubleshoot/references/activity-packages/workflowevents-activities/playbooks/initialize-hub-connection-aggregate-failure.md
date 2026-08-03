---
confidence: medium
---

# Initialize Apps Hub Connection — Aggregate Exception (AggregateException)

## Context

What this looks like:
- A Studio Web app-workflow run faults at `InitializeHubConnection` (display name **Initialize Apps Hub Connection**) with `System.AggregateException` and the message `One or more errors occurred. (<inner message>)`.
- `InitializeHubConnection` is internal Studio Web machinery the user never placed. At workflow start it resolves the Apps/Orchestrator resource URL and an access token, then starts the SignalR hub connection. It is an async activity, so a failure in its **synchronous bootstrap** surfaces wrapped in an `AggregateException` — the real cause is the inner exception.
- Note: the actual hub `StartConnectionAsync` runs on a **background thread that logs (not throws)** its errors, so a job-faulting `AggregateException` is **not** the raw socket connect failing — it is the bootstrap before that (resource-URL / token / session validation). Unwrap the inner exception.

What can cause it (read the inner exception):
- **Inner `WorkflowApplicationException` — `SignalR: Invalid SessionId: <id> OR Orchestrator Url: <url>`.** The session id or the resolved resource URL was blank when the activity validated them. Indicates the Apps/Studio Web session context or the resource-URL resolution did not produce a usable value.
- **Inner resource-URL / token-acquisition failure.** `runtime.AccessProvider.GetResourceUrl(...)` / `GetAccessToken(...)` threw — the robot could not resolve the Apps or Orchestrator endpoint, or could not obtain an access token (auth / connectivity / permission).
- **Inner transport/HTTP failure during bootstrap** — a network failure while resolving the hub endpoint.

What to look for:
- **`InnerException` / `InnerExceptions` type and message** — the decisive signal; the `AggregateException` wrapper text alone is not enough.
- **The `SignalR: Invalid SessionId ... OR Orchestrator Url ...` phrase** — points at blank session/URL context rather than a transport failure.
- **Whether the run is a Studio Web app preview / Apps-invoked run** — this activity only runs in that context; a normal Orchestrator job never executes it.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.AggregateException`; the faulted activity is `InitializeHubConnection`.
2. **Unwrap the inner exception.** Read the inner type/message from the `Info` stack and from `uip or jobs traces <job-key> --output json` / `uip traces spans get --job-key <job-key> --output json`. This selects the branch.
3. **Branch on the inner cause:**
   - `WorkflowApplicationException: SignalR: Invalid SessionId ... OR Orchestrator Url ...` → blank session/URL context.
   - resource-URL / token failure → endpoint resolution or auth failure.
   - transport/HTTP → network failure reaching the endpoint.
4. **Confirm the execution context** — that the run is a Studio Web app preview / Apps invocation (the only context where this activity runs).

## Resolution

- **Resolve by inner cause, not the wrapper.** Map the unwrapped inner exception to its fix.
- **Invalid session / resource URL (`WorkflowApplicationException`):** the Apps/Studio Web session context did not provide a session id or a resolvable resource URL — re-launch the app preview / Apps run from Studio Web so a valid session is established, and confirm the tenant's Apps service URL resolves for this robot. A blank URL points at resource-URL resolution, not the user's workflow.
- **Resource-URL / token-acquisition failure:** verify the robot can reach the Apps/Orchestrator endpoints and that the run has the rights/connectivity to obtain an access token (network, proxy, and the account's permissions).
- **Transport/HTTP inner failure:** treat as an environmental connectivity issue to the hub endpoint; re-run once the robot host's connectivity is stable.
- This activity is platform machinery — the fix is in the session/endpoint/auth context, not in the user's workflow logic.
