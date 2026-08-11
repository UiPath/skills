---
confidence: high
---

# Token Refresh Failed (DAP-GE-3004)

> **Fault bucket: 🛠 B1 — IS platform / service-side (not customer-fixable → escalate).** `DAP-GE-3004` is IS failing to obtain an access token it needs to call a **first-party UiPath service** (e.g. Orchestrator, the Feature Flag service) while executing the activity. **This token is NOT the customer's connection credential** — it is issued by the platform for the first-party service, so re-authenticating the connection does nothing. Lead with: "This is a service-side token issue inside the platform, not your connection — retry; if it persists, contact the owner team (Integration Service)." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like:
- Error code `DAP-GE-3004` (FailedToGetAccessToken)
- IS could not obtain an access token for a **first-party UiPath service** it calls at runtime (Orchestrator, Feature Flag service, …) — fails before any third-party provider request
- Occurs only at specific times — it is a first-party-service token-acquisition/refresh failure, typically transient
- No provider status returned — an IS-side exception, before the connection or provider layer (classify it as such from the code + message; there is no `IsServiceError` field)
- Maps to the `FailedToGetAccessToken` SRE signal

What can cause it:
- The platform identity/token service could not issue or refresh the token for the first-party service (transient outage or token-lifecycle window)
- The first-party service (Orchestrator / Feature Flag service) was briefly unavailable when IS requested the token
- A platform-side configuration or trust issue between IS and the first-party service

> **This is NOT a connection-credential problem.** The customer's connection OAuth token is unrelated to `DAP-GE-3004`. If the symptom is a genuine connection whose third-party OAuth token expired or was revoked, that surfaces as a provider `401` ([request-failed.md](./request-failed.md)) or the Maestro-surfaced [connection-auth-expired.md](./connection-auth-expired.md) — re-authenticate the connection there, not here.

What to look for:
- **No `ConnectionId` tied to a failing third-party auth** — the failure is platform-internal, not connection-scoped
- Whether the failure is intermittent / clustered in time (points to a transient first-party-service token window) vs sustained (points to a platform fault)
- Whether other tenants/processes hit the same code in the same window (a platform-wide signal, not a single workflow)

## Investigation

1. **Confirm it is the first-party-service token path, not a connection.** No third-party `ProviderErrorCode` / provider status (the failure is inside IS, not a provider response). Do **not** chase the connection — a healthy `uip is connections ping` here does not rule the cause out, and an unhealthy one is a separate issue.
2. **Establish timing and blast radius.** Check whether `DAP-GE-3004` is intermittent and whether it correlates with a known Orchestrator / Feature Flag service disruption window in the triage evidence.
3. **Check for recurrence.** A single occurrence that does not repeat on retry is a transient first-party-service token blip. Repeated/sustained occurrences indicate a platform fault to escalate.

## Resolution

**Primary: retry, then escalate — do NOT re-authenticate the connection.** The token comes from a first-party service, not the customer's connection.

- **Transient (single / intermittent):** re-run the job. First-party-service token acquisition usually recovers on its own; the run should succeed on retry.
- **Sustained / repeated:** escalate to the Integration Service owner team with the `DAP-GE-3004` code, `RequestId`, timestamps, and the affected first-party service (Orchestrator / Feature Flag service). This is a platform token-acquisition fault the customer cannot resolve from their workflow.
- **Do not** attempt connection re-authentication, connection editing, or connector auth-config changes for this code — they do not address a first-party-service token failure.
