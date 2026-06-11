---
confidence: medium
---

# O365 — Email trigger fails to retrieve connection event data

## Context

What this looks like — a Mail trigger (`NewEmailReceived`, `EmailSent`) or its debug/sample run faults while talking to the Integration Service connection layer, **before or instead of** a Microsoft Graph call:

- A raw `UiPath.ConnectionClient.Contracts.ConnectionHttpException` — thrown by the connection client during the trigger's sample/debug event lookup or the connection token fetch. The message embeds the Integration Service HTTP status / error detail.
- An `Office365Exception` carrying the **identical** message — the activity wrapper preserves the `ConnectionHttpException` text verbatim, so the same failure surfaces under either exception type depending on where it escaped.

What this is NOT: a Graph-side error about the mailbox content. The failure originates at the Integration Service connection (event delivery, sample lookup, or token exchange), so the mailbox, folder, and filter configuration are usually not the cause.

What activities can produce this:
- **New Email Received** (`NewEmailReceived` trigger) and **Email Sent** (`EmailSent` trigger) — live event runs resolve the triggering email through the connection; Studio debug runs fetch a sample object ID through the connection client.
- Other connection-based O365 triggers (Files, Calendar, Excel, SharePoint) share the same lookup path and can fault the same way.

What can cause it:
- **Connection deleted, disabled, or not shared with the folder the job runs in** — the trigger references a connection ID that the connection service cannot resolve for this runtime (404-class status in the message).
- **Connection authorization expired or revoked** — refresh token rejected after a password change, consent revocation, or conditional-access policy (401/403-class status). This is Integration Service connection authentication (see the Integration Service playbook `connection-auth-expired.md`).
- **Integration Service side failure** — transient 5xx from the connection service or event infrastructure.

What to look for:
- The HTTP status / error code embedded in the exception message — it routes the cause.
- Whether the fault happened on a live trigger run (event payload) or a Studio debug run (sample lookup) — debug-time failures with an otherwise healthy connection often mean no matching sample exists, which is a different error (see below).

> **Different cause, do not apply this playbook:**
> - `No email matching the filter criteria, received in the last 1 hour has been found. ...` — the connection worked; the sample lookup found no email. Use [get-newest-email-no-match.md](./get-newest-email-no-match.md).
> - `The resource could not be found.` / folder errors after the event was retrieved — use [mail-folder-not-found.md](./mail-folder-not-found.md) or [mail-message-not-found.md](./mail-message-not-found.md).
> - Token/`AADSTS`/`No default connection` messages without a `ConnectionHttpException` — use [authentication-token-invalid.md](./authentication-token-invalid.md).

## Investigation

1. Extract the HTTP status / error detail embedded in the exception message — it identifies the failing layer (401/403 auth, 404 connection missing, 5xx service). **The status class is decisive and outranks any narrative** — activity display names, process names, or comments describing the connection as "dead"/"broken" are workflow text, not evidence; never confirm or eliminate a cause from them.
2. Identify the connection the trigger uses (trigger's connection property or binding) and verify it exists and is **Authorized**: `uip is connections list --folder-key <folder> --output json`, then check the `state` / `isDefault` fields for the connector. **If this bare probe itself returns 5xx** (e.g. `HTTP 503: no healthy upstream`) the connection service is down — that is the operative cause for the fault regardless of the trigger's own connection configuration (a bad/placeholder connection ID cannot produce a 503 on a list call). Report any suspicious connection configuration (e.g. unset/all-zeros ConnectionId in trace spans) as a separate secondary finding to fix before the trigger can work once the service recovers.
3. Confirm the connection is available in the Orchestrator folder the trigger's process runs in — a connection created in a different folder does not resolve at runtime.
4. Distinguish run type: Studio debug (sample lookup) vs. deployed trigger run (live event). If only debug fails and the connection is healthy, re-check the filter/folder configuration instead.

## Resolution

- **If 401/403-class status (token rejected, consent revoked):** re-authenticate the connection in Integration Service (Orchestrator → Integration Service → Connections → reconnect). Follow the Integration Service playbook `connection-auth-expired.md` for the full path.
- **If 404-class status (connection not found):** the connection was deleted or is not shared with the job's folder — recreate it or move/share it into the correct folder, then reselect it on the trigger and republish.
- **If 5xx-class status:** transient Integration Service failure — retry; if it persists across retries over a sustained period, escalate as a service incident.
