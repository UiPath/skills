# Check Access (Effective Permissions)

Guide for `uip admin authorization check-access`. See [authorization-commands.md — Check Access](authorization-commands.md#check-access--uip-admin-authorization-check-access) for the complete flag/argument table and output codes.

## Purpose and Output

`check-access` is the Policy Decision Point (PDP): it reports what a principal can do at a scope now. Unlike `roles assignments list`, which reads PAP catalog assignments, it evaluates effective access, including server-side role catalogs managed by `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, and `processmining`. The catalog still exposes those roles and assignments through `roles list --service <svc>` and `roles assignments list --service <svc>`, but the PDP is authoritative for resolved permissions.

Returned `Data` includes `roleAssignments.results[]` effective roles. Each row contains `roleId`, `roleName`, `serviceName` (display-name form), `roleType`, and nested `roleAssignments[]` entries for underlying grants. It also includes `grantedServicesMetadata` (services with any access) and `grantedRolesMetadata` (roles contributing to the result).

Inspect every nested `roleAssignments[]` entry; do not collapse paths:

| Entry | Report label |
|---|---|
| `securityPrincipalType: "User"` and `securityPrincipalId == queried-user-id` | `direct` |
| `securityPrincipalType: "Group"` | `inherited from <Group displayName>` |
| `securityPrincipalType: "Robot"` or `"ExternalApplication"` | `via <Robot\|ExternalApplication> <name>` |

For group entries, resolve `securityPrincipalId` with `uip admin groups get <id> --output json`, cache lookups within one report, and treat the entry as a group of which the user is a member. Explain that revoking a direct grant targets the user’s assignment; revoking an inherited grant requires changing group membership or the group’s role binding.

Group roles by the response’s `serviceName`, verbatim. When only `ownerServiceName` is available from `roles get`, translate it using [authorization-commands.md — Service display-name mapping](authorization-commands.md#service-display-name-mapping). Include scope and service span where useful:

```text
Effective access for <user> at tenant <tenant> — spans <N> services: <service labels>

<service label>
  • <role> — direct
  • <role> — inherited from <group>
```

## Identity and Scope

The principal is the positional first argument: UUID, name, or email. The CLI resolves names and emails through the identity API; there is no `--identity-id` flag. Run:

```bash
uip admin authorization check-access <USER_GUID>
uip admin authorization check-access alice@example.com
uip admin authorization check-access "Alice Smith"
```

With `--file`, omit the positional argument and set the identity in the request body as `SecurityPrincipalId`.

`--scope` accepts only `Tenant` (default) or `Folder`:

| Scope | Use | Required flags beyond identity |
|---|---|---|
| `Tenant` | Per-tenant access | `--tenant-id <GUID>` optional; defaults to the login tenant |
| `Folder` | Folder-scoped access | `--scope Folder --folder-id <FOLDER_ID>`; `--tenant-id` is the owning tenant’s `ParentId` and defaults to the login tenant |

`--folder-id` replaces the older `--scope-id` / `--parent-folder-id` pair. For Folder scope, `--folder-id` is the folder’s `Id` and `--tenant-id` is its owning tenant’s `ParentId`. Do not use `Organization` or `Project` scope.

For org-wide entitlement, run `check-access <USER> --tenant-id <TID>` for every tenant from `tenants list` and aggregate `grantedRolesMetadata` per service. For project-level access, use `--scope Folder` with the owning folder, or filter the default `Tenant` result to the owning service with `--service documentunderstanding` (or the relevant service).

## Workflows

Run the following for login-tenant access; the default scope is `Tenant` and the default tenant is the login tenant:

```bash
uip admin authorization check-access <USER_GUID> --output json
```

Run the following for another tenant:

```bash
uip admin authorization check-access <USER_GUID> --tenant-id <OTHER_TENANT_ID> --output json
```

Run the following to restrict evaluation to one service, especially when server-side service roles may not appear in the PAP catalog:

```bash
uip admin authorization check-access <USER_GUID> --service orchestrator --output json
```

Use these known service names: `apps, authz, automationops, casemanagement, dataservice, documentunderstanding, identity, insights, licensing, oms, orchestrator, platform, processmining, reinfer, studio, taskmining, testmanager`. Other names are accepted free-form and passed verbatim as `ServiceName`.

Do not use `--service centralizedaccess`: although arbitrary values pass through, the PDP has no separate `centralizedaccess` service and returns no useful access information. Omit `--service` for the multi-service / Centralized Access view.

Run the following for Folder scope:

```bash
uip admin authorization check-access <USER_GUID> \
  --scope Folder \
  --folder-id <FOLDER_ID> \
  --output json
```

`--tenant-id` defaults to the login tenant’s `ParentId`; override it only for a folder in another tenant.

## File-Based Request

Run `--file <PATH>` when using filters not exposed inline, such as `RoleNameStartsWith`. Omit the positional identity and inline scope flags; put them in the body.

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

For Folder scope, `Value.Id` is the folder UUID and `Value.ParentId` is the owning tenant UUID. Run:

```bash
uip admin authorization check-access --file ./check-access.json --output json
```

## Resolving Principal IDs

To verify a UUID or obtain IDs for non-User principals, see [role-assignment-management.md — Resolving Principal IDs](role-assignment-management.md#resolve-principals-before-mutation).
