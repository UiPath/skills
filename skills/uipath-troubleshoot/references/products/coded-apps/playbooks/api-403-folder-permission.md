---
confidence: high
---

# API Call Fails 403 After Login

## Context

What this looks like:
- The app authenticates and renders, then an SDK call to `https://api.uipath.com/...` returns `HTTP 403 Forbidden`
- The token is valid (login succeeded, other calls may work) — the server accepted the identity but denied access to this resource

What can cause it:
- The folder the SDK targets is wrong or unset — `UIPATH_FOLDER_KEY` (or the folder key passed to the service call) points at a folder that does not contain the resource, or is missing entirely
- The resource (asset, queue, process, bucket) exists in a **different folder** than the one the app targets
- The authenticated user lacks the Orchestrator **role/permission** for that resource type in that folder

What to look for:
- **Discriminator: 403 vs 401.** `403 Forbidden` = valid token, insufficient access (this playbook). `401 Unauthorized` = missing/expired scope on the token — see [api-401-after-login.md](./api-401-after-login.md). Do NOT apply a scope fix to a 403.
- Which folder the failing call targets, and which folder actually holds the resource
- Whether the user's role assignments include the needed permission at the folder scope

## Investigation

1. Identify the 403'ing request in the network tab and the resource it targets (e.g. `/odata/Assets`). Confirm the status is `403`, not `401`.

2. Determine the folder the app targets — check `UIPATH_FOLDER_KEY` in the app's environment/config, or the folder key passed to the SDK service call. Resolve it against the tenant's folders:

   ```bash
   uip or folders list --output json \
     --output-filter "[].{name: FullyQualifiedName, key: Key}"
   ```

3. Confirm the resource actually lives in the targeted folder (list the resource in that folder — e.g. `uip or assets list --folder-key <key> --output json`). If it is in a different folder, that is the cause.

4. If the folder is correct, check the user's effective access at that folder scope:

   ```bash
   uip admin authorization check-access <user-guid> --scope Folder --folder-id <folder-uuid> --output json
   uip admin authorization roles assignments list --identity-id <user-guid> --output json
   ```

   Inspect `Data.roleAssignments[]` for a role granting the needed permission (e.g. `Assets.View`) at that folder. If absent, that is the cause.

## Resolution

- **If `UIPATH_FOLDER_KEY` is unset or wrong:** set it to the key of the folder that holds the resource (from step 2), then restart the dev server. For a deployed app, set the folder key in the deploy configuration and redeploy.

- **If the resource is in a different folder:** point the app at that folder's key, or move/create the resource in the folder the app targets.

- **If the user lacks the role:** assign an Orchestrator role that grants the required permission at the correct folder scope (via Orchestrator Admin → Roles, or `uip admin authorization` role-assignment commands). Re-test after the assignment propagates.
