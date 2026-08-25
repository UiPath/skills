---
confidence: high
---

# Connection Service — Permission / Authorization Denied (CNS1045, CNS1044, CNS1046, CNS1047, CNS1043, CNS3001)

> **Fault bucket: 👤 A — customer/admin-resolvable.** The caller reached Connection Service but was rejected by an authorization layer: missing **folder permission** (the big one — `CNS1045`), missing OAuth **scope**, a client ID not allowed on the endpoint, a bad/unsupported token, or an **Automation Ops governance policy** blocking the connector. In every case the fix is an admin action (grant permission/scope, adjust policy) — not a retry and not a service escalation.

## Context

What this looks like:
- HTTP `403`/`401` (or `400` for the missing-folder-key case) from Connection Service
- The highest-volume production signature: `CNS1045` — *"The robot does not have the Connections.View permission in the folder where this connection lives. Ask your administrator to grant Connections.View on that folder, or move the connection to a folder where the robot has the required permission."* (sometimes with a `(Folder: <key>)` hint)
- Debug runs work (user identity has the permission) but deployed/unattended runs fail (robot account doesn't) — the classic signature of a folder-permission gap

| Code | Name | Rejecting layer | Exact meaning | HTTP |
|------|------|-----------------|---------------|:---:|
| `CNS1045` | InsufficientFolderPermission | Folder authorization | Caller lacks a folder-scoped permission (default named permission: `Connections.View`) on the folder holding the connection/trigger | 403 |
| `CNS1044` | InsufficientPermissions | Scope authorization | The token lacks a required OAuth scope; also used when a downstream dependency answers 403 | 403 |
| `CNS1046` | InsufficientClientId | Client authorization | The token's `client_id` is not on the endpoint's allow-list (S2S/internal endpoints) | 401 |
| `CNS1047` | Unauthorized | Authentication | Token invalid/wrong audience; also *"External application authentication is not supported"* on endpoints that don't accept external-app tokens | 401 |
| `CNS1043` | MissingFolderKey | Request validation | An S2S caller did not supply the folder key that folder-scoped resolution requires | 400 |
| `CNS3001` | ForbiddenAccess | Governance | An **Automation Ops policy** blocks the action — e.g. *"The connector was disabled by an Automation Ops policy."* Fires on connection create and re-authenticate when the policy denies the connector | 403 |

Related: `CNS1025` — nominally "TriggerRequestInvalid" — is **reused** for *"In S2S context, the folder key is required"* on several connection/trigger endpoints. Treat that message the same as `CNS1043` regardless of the code.

What can cause it:
- Robot account was never granted `Connections.View` (or the folder-specific permission the message names) on the folder the connection lives in
- The connection was moved to a different folder after the process was deployed
- API/external-app integration was registered without the Connection Service scopes it calls
- An Automation Ops governance policy was tightened, disabling a connector tenant-wide or for specific groups
- Internal S2S callers omitting the folder key header/parameter after an integration change

What to look for:
- **Which permission and which folder** — the `CNS1045` message names the permission and often the folder key; that's the exact grant to make
- Caller identity: user vs robot account vs external app (the fix target differs)
- For `CNS3001`: which policy — check Automation Ops policies applied to the tenant/user group for the named connector

## Investigation

1. **Read the message, not just the code** — `CNS1045` tells you the missing permission and (usually) the folder. That is 90% of the diagnosis.
2. **Identify the caller identity** the request ran under (robot account for unattended jobs, the user for debug, the app registration for API calls). Verify in Orchestrator → Folders → the named folder → Assigned users/robots whether that identity holds the named permission (e.g. `Connections.View`; Maestro trigger paths may also need `Triggers` permissions).
3. **Reproduce the split**: if debug works and deployed fails, it is a robot-account grant, full stop.
4. **`CNS1044`/`CNS1047` on API integrations**: inspect the token (scopes, audience). For external apps, confirm the app registration includes the Integration Service / Connection Service scopes it invokes and that the endpoint supports external-app tokens at all (`CNS1047`'s "not supported" message means it never will — use a different auth model).
5. **`CNS3001`**: list Automation Ops policies for the tenant; find the connector allow/deny list that covers the affected user/group. The connection UI action that failed (create or re-authenticate) confirms the policy is evaluated on those flows.
6. **`CNS1043` / folder-key-required `CNS1025`**: only surfaces on S2S/machine callers — a missing folder key in the request. This is an integration bug in the *calling service*, not a permissions grant.

## Resolution

- **`CNS1045`:** have a folder admin grant the named permission (typically `Connections.View`) to the robot/user on the folder holding the connection — or move the connection to a folder where the runner already has it. Re-run; no re-authentication needed.
- **`CNS1044`:** add the missing OAuth scope to the app registration / token request. If it wrapped a downstream 403, treat the named dependency's permission model (e.g. Orchestrator role) instead.
- **`CNS1046`/`CNS1047`:** these are integration-configuration rejections — fix the token audience/client registration; do not retry with the same token. `CNS1046` on UiPath-internal endpoints reaching a customer is unusual — capture the `traceId` and escalate if the caller is a supported public surface.
- **`CNS3001`:** a governance decision, not an error — the admin either updates the Automation Ops policy to allow the connector or the user stops using the blocked connector. Never escalate to Integration Service to "fix" a policy block.
- **`CNS1043` / S2S folder key:** fix the calling integration to pass the folder key. If the caller is a UiPath product (not customer code), escalate to that product's team with the `traceId`.
