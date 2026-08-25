# Check Access (Effective Permissions)

Conceptual guide and scope-specific workflows for `uip admin authorization check-access`. For the full flag/argument table and output code, see [authorization-commands.md — Check Access](authorization-commands.md#check-access--uip-admin-authorization-check-access).

## Concept

`check-access` is the **Policy Decision Point (PDP)**. It answers: *"What can this principal actually do at this scope, right now?"*

Unlike `roles assignments list` (which reads stored assignments from the PAP catalog), `check-access` evaluates **effective** access — it folds in server-side rules from services that manage their own role catalogs (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`) that the PAP catalog alone may not reflect. The catalog *does* surface these services' roles and assignments (`roles list --service <svc>` / `roles assignments list --service <svc>`), but the PDP is the source of truth for "what permissions resolve right now".

Returned `Data`:

- `roleAssignments.results[]` — list of effective roles the principal has at the scope. Each row is a role with metadata (`roleId`, `roleName`, `serviceName` (display-name form), `roleType`) **and a nested `roleAssignments[]` array** recording each underlying grant.
- `grantedServicesMetadata` — services the principal has any access to.
- `grantedRolesMetadata` — roles contributing to the result.

## Direct vs. Inherited — Always Surface the Distinction

`check-access` aggregates effective permissions from **direct** user grants AND grants the user **inherits via group membership**. The user needs to see which is which — revoking a direct grant means targeting the user's own assignment; revoking an inherited grant means changing group membership (or the group's role binding).

For every role in `roleAssignments.results[]`, inspect the nested `roleAssignments[]`:

| Nested entry | Interpretation | Label to render |
|---|---|---|
| `securityPrincipalType: "User"` AND `securityPrincipalId == queried-user-id` | Role assigned directly to this user | `direct` |
| `securityPrincipalType: "Group"` | Role assigned to a group the user is a member of | `inherited from <Group displayName>` — resolve the `securityPrincipalId` via `uip admin groups get <id> --output json` (cache lookups within one report) |
| `securityPrincipalType: "Robot"` / `"ExternalApplication"` | Cross-principal grant (rare on a user `check-access`) | `via <Robot\|ExternalApplication> <name>` |

Multiple entries under one role's `roleAssignments[]` mean the user has the role via multiple paths — list **all** of them; do not collapse.

### Example presentation

```
Effective access for alice@example.com at tenant Prod-East — spans 3 services: IXP, Orchestrator, Apps

IXP (ownerServiceName: Reinfer)
  • IXP Tenant Admin     — inherited from Tenant Admins
  • IXP Project Reader   — direct

Orchestrator
  • Orchestrator Folder Admin — inherited from Tenant Admins

Apps
  • App User — direct
```

The response's `serviceName` field is already the display name (e.g., `"IXP"`, `"Data Service"`) — surface verbatim. When you only have `ownerServiceName` from a companion `roles get`, translate via [authorization-commands.md — Service display-name mapping](authorization-commands.md#service-display-name-mapping-cli-ownerservicename--user-facing-label).

## Identity Argument

The principal is the **positional** first argument — UUID, name, or email. The CLI resolves names and emails via the identity API.

```bash
uip admin authorization check-access <USER_GUID>
uip admin authorization check-access alice@example.com
uip admin authorization check-access "Alice Smith"
```

There is no `--identity-id` flag. With `--file`, the identity is set in the request body (`SecurityPrincipalId`) and the positional argument is omitted.

## Choosing the Scope

`check-access --scope` accepts only **`Tenant`** (default) or **`Folder`** — narrower than the scope vocab on `roles create` or `roles assignments create`.

| Scope | When to use | Required flags beyond identity |
|-------|-------------|--------------------------------|
| `Tenant` (default if omitted) | Per-tenant access | `--tenant-id <GUID>` optional (defaults to login tenant) |
| `Folder` | Folder-scoped access | `--scope Folder --folder-id <FOLDER_ID>`. `--tenant-id` becomes the owning tenant ParentId (defaults to login tenant) |

> **No `Organization` / `Project` scope on `check-access`.** The PDP doesn't expose those directly. To approximate:
> - **Org-wide entitlement check** — loop `check-access <USER> --tenant-id <TID>` over every tenant (`tenants list`), then aggregate `grantedRolesMetadata` per service.
> - **Project-level access** — use `--scope Folder` with the project's owning folder, or filter the default `Tenant` result to the service that owns the project (`--service documentunderstanding` etc.).

> `--folder-id` replaces the older `--scope-id` / `--parent-folder-id` pair. For Folder scope, `--folder-id` is the Folder's `Id` and `--tenant-id` is the owning tenant's `ParentId`.

## Workflow: Check a User's Effective Access at the Login Tenant

```bash
uip admin authorization check-access <USER_GUID> --output json
```

Default scope is `Tenant`, default tenant is the login tenant.

## Workflow: Check Across Tenants

```bash
uip admin authorization check-access <USER_GUID> --tenant-id <OTHER_TENANT_ID> --output json
```

## Workflow: Restrict to One Service

Especially useful for services that manage their own roles, where the PAP catalog may not reflect server-side rules:

```bash
uip admin authorization check-access <USER_GUID> --service orchestrator --output json
```

Known service names: `apps, authz, automationops, casemanagement, dataservice, documentunderstanding, identity, insights, licensing, oms, orchestrator, platform, processmining, reinfer, studio, taskmining, testmanager`. Other names are accepted free-form (passed through verbatim as `ServiceName`).

> **`--service centralizedaccess` is not in the list.** `check-access` does pass arbitrary `--service` values through verbatim, but the PDP has no separate "centralizedaccess" service to score — querying it returns no useful access info. For the multi-service / Centralized Access view, omit `--service` and let the default Tenant evaluation return every role the principal holds across services.

## Workflow: Folder Scope

```bash
uip admin authorization check-access <USER_GUID> \
  --scope Folder \
  --folder-id <FOLDER_ID> \
  --output json
```

`--tenant-id` defaults to the login tenant for the ParentId; override only when targeting a folder in a different tenant.

## Workflow: Advanced — File-Based Request

Use `--file <PATH>` for filters not exposed inline (e.g. `RoleNameStartsWith`). With `--file`, omit the positional identity and the inline scope flags — they're set in the body.

`check-access.json`:

```json
{
  "SecurityPrincipalId": "<PRINCIPAL_ID>",
  "RoleNameStartsWith": "Admin",
  "ServiceName": "orchestrator",
  "ScopeIdentifier": {
    "ScopeType": "Tenant",
    "Value": { "Id": "<TENANT_ID>", "ParentId": "<TENANT_ID>" }
  }
}
```

For Folder scope, `Value.Id` is the folder UUID and `Value.ParentId` is the owning tenant UUID.

```bash
uip admin authorization check-access --file ./check-access.json --output json
```

## Resolving Principal IDs

If you only have a UUID and want to verify the identity exists first, or if you need IDs for non-User principals, see [role-assignment-management.md — Resolving Principal IDs](role-assignment-management.md#resolving-principal-ids).
