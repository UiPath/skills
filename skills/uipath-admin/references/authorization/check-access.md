# Check Access (Effective Permissions)

Conceptual guide and scope-specific workflows for `uip admin authorization check-access`. For the full flag/argument table and output code, see [authorization-commands.md — Check Access](authorization-commands.md#check-access--uip-admin-authorization-check-access).

## Concept

`check-access` is the **Policy Decision Point (PDP)**. It answers: *"What can this principal actually do at this scope, right now?"*

Unlike `roles assignments list` (which reads stored assignments from the PAP), `check-access` evaluates effective access — it includes **service-managed roles** (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager` manage their own role catalogs server-side) that do NOT surface via `roles list` or `roles assignments list`.

Returned `Data`:

- `roleAssignments` — paginated list of effective assignments.
- `grantedServicesMetadata` — services the principal has any access to.
- `grantedRolesMetadata` — roles contributing to the result.

## Identity Argument

The principal is the **positional** first argument — UUID, name, or email. The CLI resolves names and emails via the identity API.

```bash
uip admin authorization check-access <USER_GUID>
uip admin authorization check-access alice@example.com
uip admin authorization check-access "Alice Smith"
```

There is no `--identity-id` flag. With `--file`, the identity is set in the request body (`SecurityPrincipalId`) and the positional argument is omitted.

## Choosing the Scope

| Scope | When to use | Required flags beyond identity |
|-------|-------------|--------------------------------|
| `Tenant` (default if omitted) | Per-tenant access | `--tenant-id <GUID>` optional (defaults to login tenant) |
| `Organization` | Org-wide entitlement check | `--scope Organization` |
| `Folder` | Folder-scoped access | `--scope Folder --folder-id <FOLDER_ID>`. `--tenant-id` becomes the owning tenant ParentId (defaults to login tenant) |
| `Project` | Project-scoped access (requires the owning service) | `--scope Project --service <SERVICE>` |

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

Especially useful for services that manage their own roles, where stored assignments don't surface via `roles assignments list`:

```bash
uip admin authorization check-access <USER_GUID> --service orchestrator --output json
```

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
