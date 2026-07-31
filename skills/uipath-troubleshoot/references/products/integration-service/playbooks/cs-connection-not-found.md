---
confidence: high
---

# Connection Service — Connection Not Found / Invalid (CNS1006, CNS1000, CNS1049, CNS1003)

> **Fault bucket: 👤 A — customer-resolvable.** The caller asked Connection Service for a connection that does not exist *from the caller's context*: wrong ID, deleted connection, a connector with no connections yet, a connection living in someone else's personal workspace, or a folder the caller cannot see. The fix is on the customer's side — create/select the right connection or move it where the runner can reach it. This is the **service-API view** of the same failure the connector activity surfaces as `DAP-GE-3000` — the full workspace/folder disambiguation procedure in [connection-not-resolved.md](./connection-not-resolved.md) and [connection-invalid.md](./connection-invalid.md) applies; this page adds the exact CNS code semantics.

## Context

What this looks like:
- HTTP `404` (occasionally `400`) from a Connection Service API call, error body `{ "code": "CNS1006", "message": "Connection [<guid>] is invalid or you do not have access…", "traceId": "…" }`
- At runtime it usually reaches the user wrapped by the activity layer (`DAP-GE-3000` "Failed to retrieve connection") or by Maestro (IntSvc `102002`/`102008`)

Code semantics — these are NOT interchangeable:

| Code | Name | Exact meaning | HTTP |
|------|------|---------------|:---:|
| `CNS1006` | ConnectionIdInvalid | The specific connection ID does not exist **or the caller has no access to it** — deleted, wrong tenant, or cross-workspace | 404 / 400 |
| `CNS1000` | ConnectionForConnectorNotFound | The connector exists but has **zero connections** in the caller's scope ("Connector [x] does not have any connections") — hit on the *default-connection* lookup | 404 |
| `CNS1049` | NotFound | Generic not-found; the notable specific case: the connection lives on a **personal workspace** that is not shared with the caller ("Connection '…' is on a personal folder…"). Also used as passthrough when a downstream dependency 404s. | 404 |
| `CNS1003` | SessionIdInvalid | The OAuth **authentication session** (create/re-auth flow) is stale or expired — not the connection itself | 404 |

What can cause it:
- The connection was deleted (or its folder was) after a process/trigger was configured against it
- The process was published with a connection from the author's **personal workspace**; the runner (robot account) cannot see it → `CNS1049`/`CNS1006`
- Automation references a hard-coded connection ID from a different tenant/environment (e.g. dev → prod promotion without rebinding)
- `CNS1000`: an activity or API asked for a "default connection" for a connector nobody has connected yet in that tenant/folder
- `CNS1003`: the user left an OAuth consent window open too long, or retried a stale create-connection session — harmless, just restart the flow

What to look for:
- The connection GUID in the message — search it in the tenant's Integration Service UI and across folders
- Whether the caller is a robot account (deployed run) vs the user (debug) — access differs
- Whether the same GUID works from the author's account (points at workspace/folder scoping, not deletion)

## Investigation

1. **Extract the connection ID and caller identity** from the error (`traceId` body field correlates the request). Determine whether the caller was a user, a robot account, or an S2S client.
2. **Follow the ownership procedure from [connection-invalid.md](./connection-invalid.md)** — read the project's connection resource file (`**/connection/<connector-key>/*.json`), extract `resource.name` (owner) and `resource.folders` (binding), and compare against the runner's folder. That procedure is authoritative for disambiguating *deleted* vs *cross-workspace* vs *wrong folder*.
3. **Map the code to the scenario:**
   - `CNS1000` → nothing to hunt for; no connection exists for that connector in scope. Create one.
   - `CNS1049` with the personal-folder message → the connection exists but lives in a personal workspace; sharing/moving is the fix, not recreating.
   - `CNS1006` → the ID itself doesn't resolve for the caller; distinguish deleted vs cross-tenant vs no-access via step 2.
   - `CNS1003` → ignore the connection entirely; the *authentication session* expired. Retry the connect/re-auth flow from the start.
4. **If the caller lacks access but the connection exists**, check folder permissions next — a FolderAuth 403 surfaces as a different code (`CNS1045`, see [cs-permission-denied.md](./cs-permission-denied.md)); a 404 here means the folder scoping itself hides the connection.

## Resolution

- **Deleted / never existed:** create a new connection for the connector in the folder where the automation runs, and rebind the activity/trigger to it.
- **Personal-workspace connection (`CNS1049`):** move the connection to a shared folder the robot can access, or recreate it in the correct folder. Do not publish processes bound to personal-workspace connections for unattended runs.
- **`CNS1000` on default-connection lookup:** create at least one connection for the connector in that tenant/folder (and mark it default if the flow relies on the default).
- **`CNS1003`:** restart the connection creation / re-authentication flow; the session token is single-use and short-lived. No escalation needed unless it repeats immediately on a fresh attempt.
- **Escalate only** when the connection verifiably exists in the right folder with the right permissions and `CNS1006` still fires — then it is a resolution defect; hand the owner team the `traceId`, connection ID, and caller identity.
