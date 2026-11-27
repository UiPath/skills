# Authorization CLI Command Reference

Reference for `uip admin authorization` commands: custom-role CRUD, role assignments, permission catalogs, and effective-access lookups in the Authorization service.

For workflow guidance, see [role-management.md](role-management.md), [role-assignment-management.md](role-assignment-management.md), [permission-catalog.md](permission-catalog.md), and [check-access.md](check-access.md).

## Global Flags and Prerequisites

Every command accepts these flags (omitted from command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath expression to filter output |
| `--log-level <level>` | `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs to file instead of stderr |
| `--login-validity <minutes>` | Override token validity; force refresh if the token expires within this window |

Organization is resolved from the active login session. Run:

```bash
uip login status --output json
```

If not logged in, run `uip login`.

## Concepts and Constraints

- Roles and assignments live at the Policy Administration Point (PAP). `check-access` is the Policy Decision Point (PDP): it computes effective access at a principal and scope, including services that do not expose assignments through `roles assignments list`.
- Role-definition `--scope` values are `Organization`, `TenantGlobal`, `Tenant`, and `Project`; there is **no `Folder`** role shape. Folder scoping exists only on assignments.
- `Tenant` binds a role to one tenant UUID. `TenantGlobal` is a reusable template available in every organization tenant.
- Service-managed roles: `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, and `processmining`. `roles list --service <svc>` and `roles assignments list --service <svc>` surface their roles and assignments, but `roles create`, `roles update`, and `roles delete` cannot mutate them. Use the service CLI, such as `uip or roles ...`, and use `check-access` for effective access, including server-side rules absent from the catalog.
- Platform-level services `authz`, `oms`, `platform`, `identity`, and `licensing` reject custom-role authoring; listing works.
- On `roles create/update/list` and `permissions list`, `--service` infers scope from the registry when used alone (for example, `studio` → `Tenant`, `apps` → `Organization`). Combine `--service` and `--scope` only to override the registry default.
- Do not use `--service centralizedaccess`. The CLI rejects it on `roles create/list`, `roles assignments list`, and `permissions list` with `'centralizedaccess' is not a valid --service value`. For Centralized Access multi-service tenant/org roles and listings, omit `--service` and use `--scope <Tenant|Organization|TenantGlobal>`.
- `roles create` and `roles update` share a PUT-style upsert endpoint. The CLI assembles the full role from inline flags and the `--file` actions array. Re-fetch before updating; even a partial inline update rewrites the full role.
- `BuiltIn` roles cannot be created, updated, or deleted.
- Assignment `--identity-type` values are `User | Group | Robot | ExternalApplication`.

## Roles — `uip admin authorization roles`

### `roles list`

Run:

```bash
uip admin authorization roles list --output json
uip admin authorization roles list --scope Organization --output json
uip admin authorization roles list --scope Tenant --output json
uip admin authorization roles list --service studio --filter Admin --output json
uip admin authorization roles list --role-type Custom --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Substring match on role name |
| `--service <name>` | No | Restrict to one service; alone infers scope from the registry. Do not use `centralizedaccess` |
| `--scope <type>` | No | `Organization`, `TenantGlobal`, `Tenant`, `Project`, or `Folder` (case-insensitive); optional with `--service` |
| `--role-type <BuiltIn\|Custom>` | No | Restrict by type |
| `--tenant-id <guid>` | No | Restrict to a tenant-bound role; resolve IDs with `uip admin tenants list --filter <name>` |
| `-l, --limit <number>` | No | Items per page |
| `--offset <number>` | No | Items to skip |

**Output code:** `AuthzRolesList`.

### `roles get`

Run:

```bash
uip admin authorization roles get <ROLE_ID> --output json
```

`<ROLE_ID>` is required and comes from `roles list`. Read `ownerServiceId` and `ownerServiceName` before creating assignments; see [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-role-service-binding-and-scope-path).

**Output code:** `AuthzRoleGet`.

### `roles create`

Create a custom role. Inline flags carry metadata; `--file` is a JSON string array of granted permission names. Run:

```bash
uip admin authorization roles create --scope Tenant --tenant-id <TENANT_ID> --name "Tenant Reader" --file ./actions.json --output json
uip admin authorization roles create --scope Organization --name "Org Reader" --description "Read-only org admin" --file ./actions.json --output json
uip admin authorization roles create --service studio --name "Studio Author" --file ./actions.json --output json
uip admin authorization roles create --scope TenantGlobal --name "Tenant Reader Template" --file ./actions.json --output json
uip admin authorization roles create --scope Project --service documentunderstanding --name "DU Project Editor" --file ./actions.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes | Role display name |
| `--description <text>` | No | Human-readable description |
| `--service <name>` | Conditional | Owning service; required for `--scope Project`; alone infers scope. Do not use `centralizedaccess` |
| `--scope <type>` | Conditional | `Organization`, `TenantGlobal`, `Tenant`, or `Project` (case-insensitive); optional with `--service` |
| `--tenant-id <guid>` | No | Tenant UUID, valid only for resolved `Tenant` or `Project`; defaults to the login tenant |
| `--file <path>` | Yes | JSON file containing granted actions as a string array |

Use permission names, not UUIDs; resolve them with `permissions list`. `./actions.json` may contain:

```json
["STUDIO.X.Y", "STUDIO.A.B", "STUDIO.NUGET.LIST"]
```

When reporting creation, always state the resolved service: `service: <name>` when `--service` was passed, or `service: none — multi-service <scope> role` when omitted.

**Output code:** `AuthzRoleCreated`.

### `roles update`

Re-fetch, edit, and submit the complete role because this is the same PUT-style endpoint as `create`. Run:

```bash
uip admin authorization roles update <ROLE_ID> --scope Tenant --name "Tenant Reader v2" --file ./actions.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ROLE_ID>` | Yes | Role UUID; positional ID wins over any body-side ID |
| `--name <name>` | No | Role display name |
| `--description <text>` | No | New description |
| `--service <name>` | Conditional | Owning service; required for `--scope Project`; do not use `centralizedaccess` |
| `--scope <type>` | Conditional | `Organization`, `TenantGlobal`, `Tenant`, or `Project` |
| `--tenant-id <guid>` | No | Tenant UUID, valid for `Tenant`/`Project` |
| `--file <path>` | No | Replacement string-array actions; omission preserves the current action set |

**Output code:** `AuthzRoleUpdated`.

### `roles delete`

Run:

```bash
uip admin authorization roles delete <ROLE_ID> --output json
```

`<ROLE_ID>` is required. Only `type: Custom` roles can be deleted; the CLI pre-fetches and redirects for service-managed or platform-owned roles.

**Output code:** `AuthzRoleDeleted`.

## Role Assignments — `uip admin authorization roles assignments`

An assignment is `(principal, role, scope)`.

### `roles assignments list`

Run:

```bash
uip admin authorization roles assignments list --output json
uip admin authorization roles assignments list --scope Organization --output json
uip admin authorization roles assignments list --scope Tenant --tenant-id <TENANT_ID> --output json
uip admin authorization roles assignments list --scope Folder --scope-id Insights --output json
uip admin authorization roles assignments list --scope Project --scope-id <PROJECT_ID> --output json
uip admin authorization roles assignments list --identity-id <PRINCIPAL_ID> --output json
uip admin authorization roles assignments list --include-inherited --output json
uip admin authorization roles assignments list --scope-path "/tenant/<TID>/Reinfer" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--identity-id <id>` | No | Server-side principal UUID filter |
| `--service <name>` | No | Server-side service filter; with `--scope`, or alone, builds the registry scope path. Do not use `centralizedaccess` |
| `--scope <type>` | No | `Organization`, `Tenant`, `Project`, `Folder`, or `App`; default `Tenant`. `TenantGlobal` is invalid. Project/Folder/App require `--service` and `--scope-id` |
| `--scope-id <id>` | Conditional | Project ID, folder name or ID, or app ID; used with `--service` |
| `--scope-path <path>` | No | Exact path; overrides `--scope`, `--tenant-id`, and `--scope-id` |
| `--tenant-id <guid>` | No | Tenant UUID; defaults to login tenant for Tenant/Project/Folder/App |
| `--include-inherited` | No | Include parent-scope assignments; default is direct only |
| `-l, --limit <number>` | No | Items per page; server caps at 10 assignment groups |
| `--offset <number>` | No | Items to skip |

For multi-service tenant assignments, omit `--service` and use `--scope Tenant`.

**Output code:** `AuthzAssignmentsList`.

### `roles assignments create`

Before submitting, run `roles get <ROLE_ID>` and validate that the scope-path service segment matches `ownerServiceName` case-insensitively: `lowercase(ownerServiceName) == <svc>` segment. If `ownerServiceName == "CentralizedAccess"`, the path must omit a service segment. Follow [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-role-service-binding-and-scope-path).

Run:

```bash
uip admin authorization roles assignments create --role-id <ROLE_ID> --identity-id <PRINCIPAL_ID> --identity-type User --output json
uip admin authorization roles assignments create --role-id <ROLE_ID> --identity-id <PRINCIPAL_ID> --identity-type User --tenant-id <TENANT_ID> --output json
uip admin authorization roles assignments create --role-id <ROLE_ID> --identity-id <GROUP_ID> --identity-type Group --scope-path "/tenant/<TID>/Reinfer/project/<PID>" --output json
uip admin authorization roles assignments create --file ./assignments.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--role-id <id>` | Yes (inline) | Role UUID |
| `--identity-id <id>` | Yes (inline) | Principal UUID |
| `--identity-type <type>` | Yes (inline) | `User`, `Group`, `Robot`, or `ExternalApplication` |
| `--service <name>` | No | Owning service; combines with `--scope` or alone builds the registry scope path |
| `--scope <type>` | No | `Organization`, `TenantGlobal`, `Tenant`, `Project`, `Folder`, or `App`; Project/Folder/App require `--service` and `--scope-id` |
| `--scope-id <id>` | Conditional | Project ID, folder name or ID, or app ID for `--scope Project\|Folder\|App` |
| `--scope-path <path>` | No | Exact path; overrides `--scope`, `--service`, `--scope-id`, and `--tenant-id` |
| `--tenant-id <guid>` | No | Tenant UUID for Tenant / TenantGlobal / Project / Folder / App; defaults to login tenant |
| `--file <path>` | Alternative | JSON array of `AddRoleAssignmentRequest` |

When neither `--scope` nor `--scope-path` is supplied, inline path defaults from the role `scopeType`:

| Role scope | Auto-filled path |
|------------|------------------|
| `Organization` | `/` |
| `Tenant` / `TenantGlobal` | `/tenant/<TENANT_ID>`; defaults to login tenant |
| `Project` / `Folder` / `App` | Not auto-filled; pass `--scope` + `--service` + `--scope-id`, or `--scope-path` |

`assignments.json` is an array of `AddRoleAssignmentRequest` objects:

```json
[
  {
    "roleId": "<ROLE_ID>",
    "securityPrincipalId": "<PRINCIPAL_ID>",
    "securityPrincipalType": "User",
    "scope": "/tenant/<TENANT_ID>"
  }
]
```

The bulk endpoint is atomic; partial failure rolls back the whole batch.

**Output code:** `AuthzAssignmentCreated`.

### `roles assignments delete`

Run:

```bash
uip admin authorization roles assignments delete <ASSIGNMENT_ID> --output json
uip admin authorization roles assignments delete --file ./assignment-ids.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ASSIGNMENT_ID>` | No (with `--file`) | Single assignment UUID |
| `--file <path>` | Alternative | JSON array of UUID strings |

`assignment-ids.json` is a JSON array of UUID strings. The bulk endpoint silently no-ops on unknown or already-deleted IDs and still returns Success; list before and after to confirm deletion.

**Output code:** `AuthzAssignmentDeleted`.

## Permissions — `uip admin authorization permissions`

### `permissions list`

Read the permission catalog. Records contain `id`, `name`, `namespace`, `serviceDisplayName`, `resourceType`, `resourceAction`, `resourceGroup`, and `scopeType`.

Run:

```bash
uip admin authorization permissions list --output json
uip admin authorization permissions list --scope Organization --output json
uip admin authorization permissions list --scope Tenant --output json
uip admin authorization permissions list --service studio --output json
uip admin authorization permissions list --scope Project --service documentunderstanding --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--service <name>` | No | Restrict to one service; combines with `--scope` or alone infers scope. Known: `apps, authz, automationops, casemanagement, dataservice, documentunderstanding, identity, insights, licensing, oms, orchestrator, platform, processmining, reinfer, studio, taskmining, testmanager`; other names are accepted free-form. Do not use `centralizedaccess` |
| `--scope <type>` | No | `Organization`, `TenantGlobal`, `Tenant`, or `Project` (case-insensitive); optional with `--service` |

`authz` cross-cutting permissions are filtered out by default; pass `--service authz` to show them. Permission `name` strings, not UUIDs, go in `roles create --file ./actions.json`.

**Output code:** `AuthzPermissionsList`.

## Check Access — `uip admin authorization check-access`

Compute effective permissions at a scope through the PDP, including service-managed roles not surfaced by `roles assignments list`.

Run:

```bash
uip admin authorization check-access <USER_GUID> --output json
uip admin authorization check-access alice@example.com --output json
uip admin authorization check-access <USER_GUID> --tenant-id <TENANT_ID> --output json
uip admin authorization check-access <USER_GUID> --service orchestrator --output json
uip admin authorization check-access <USER_GUID> --scope Folder --folder-id <FOLDER_ID> --output json
uip admin authorization check-access --file ./check-access.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<identity>` | Yes (inline) | User UUID, name, or email; required unless `--file` is supplied |
| `--scope <type>` | No | `Tenant` (default) or `Folder` only; no `Organization` / `Project` |
| `--tenant-id <guid>` | No | Tenant UUID, defaulting to login tenant. For Tenant, it is both `Id` and `ParentId`; for Folder, it is `ParentId` |
| `--folder-id <guid>` | Conditional | Required for `--scope Folder`; used as scope `Id` |
| `--service <name>` | No | Restrict to a service |
| `--file <path>` | Alternative | Full request body; mutually exclusive with positional identity and scope flags |

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

For Folder scope, `Value.Id` is the folder UUID and `Value.ParentId` is the owning tenant UUID. Returned `Data` contains `roleAssignments` — paginated effective assignments, `grantedServicesMetadata` — services where the principal has access, and `grantedRolesMetadata` — contributing roles.

**Output code:** `AuthzCheckAccess`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `cannot create roles for service X` | Service-managed or platform-level service | Use the service CLI, such as `uip or roles create` for Orchestrator |
| `role not found` | Invalid role ID | Run `roles list` |
| `cannot delete built-in role` | Target is `BuiltIn` | Delete only `Custom` roles |
| Updated role lost actions | `--file` omitted on update | Re-run `update` with populated `--file ./actions.json`, or fetch, edit, and resubmit |
| `invalid action name` | Permission name absent from catalog | Re-resolve with `permissions list --service <SERVICE>` and copy `name` verbatim |
| `principal not found` | Invalid identity ID or email | Resolve with `uip admin users list --search <EMAIL>` or the matching identity command |
| `scope path required` | Folder/Project/App role lacks `--scope-path` or the `--scope`/`--service`/`--scope-id` triple | Pass `--scope Folder --service <svc> --scope-id <id>`, or pass `--scope-path` |
| `folder-id required` | `check-access --scope Folder` lacks `--folder-id` | Pass the folder UUID; `--tenant-id` defaults to login tenant for `ParentId` |
| Empty `roleAssignments` | No effective access at the requested scope | Confirm with `roles assignments list --identity-id <ID>` |
| Auth error | Login expired | Run `uip login status`, then run `uip login` |

## Provenance contract for completion output

Authz entitlements are anchored to an **organization**, **tenant** (or `TenantGlobal` template), and **service**. Every surfaced result must show these coordinates with UUIDs resolved to human-readable names; never expose a raw `tenantId` or `roleId` in user-facing output.

| Verb | Always surface alongside the result |
|---|---|
| `roles list` / `roles get` | Role name; `scopeType` (`Organization` / `TenantGlobal` / `Tenant` / `Project`); owning service read directly as `ownerServiceName`; display name using the mapping below; tenant binding (`tenantId` → tenant name; zero-GUID → `TenantGlobal / unbound`) |
| `roles create` / `roles update` | The role summary above plus permission count, derived from a follow-up `roles get <id>` |
| `roles assignments list` | Role name; principal type and name (resolve UUIDs); scope path with names, not UUIDs, such as `/tenant/Prod-East/IXP/project/Invoices-AP` |
| `roles assignments create` / `delete` | Assignment summary; for batch, summarize per role and scope |
| `permissions list` | Group rows by `serviceDisplayName`; show `name`, `scopeType`, and a per-service row-count summary up front, such as `Studio (24), Identity (12), Apps (8)` |
| `check-access` | Tenant used by the check (login tenant or `--tenant-id` override); group `roleAssignments.results[]` by `serviceName` with a one-line `spans N services: A, B, C` summary; label each role `direct` or `inherited from <Group name>` by inspecting nested `roleAssignments[].securityPrincipalType`: `User` with an ID matching the query is direct, while `Group` is inherited; resolve `securityPrincipalId` with `uip admin groups get <id>` to obtain `displayName` |

### Service display-name mapping

Translate slug-like `ownerServiceName` values before user-facing output:

| `ownerServiceName` (response) | Display name | Slug for `--service` / scope-path |
|---|---|---|
| `Reinfer` | **IXP** | `reinfer` |
| `DocumentUnderstanding` | Document Understanding | `documentunderstanding` |
| `ProcessMining` | Process Mining | `processmining` |
| `AutomationOps` | Automation Ops | `automationops` |
| `CentralizedAccess` | Centralized Access | Omit `--service`; the CLI rejects this slug |
| `Orchestrator`, `Insights`, `Apps`, `AuthZ`, `OMS`, `Platform`, etc. | Same as `ownerServiceName` | `lowercase(ownerServiceName)` |

`check-access` `roleAssignments.results[]` already returns display names in `serviceName` (for example, `Data Service` and `IXP`); surface that field verbatim. Use the mapping when only `ownerServiceName` is available.

After every authz mutation: (1) show the command result and new resource ID; (2) re-fetch with `roles get` or `roles assignments list --identity-id <ID>` and apply this contract to the post-mutation state; (3) offer a next step, such as assigning the role or running `check-access` to verify.
