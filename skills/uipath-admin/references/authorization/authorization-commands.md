# Authorization CLI Command Reference

Complete reference for all `uip admin authorization` commands — custom-role CRUD, role assignments, permission catalog, and effective-access lookups (Authorization service).

For workflow-level guidance, see [role-management.md](role-management.md), [role-assignment-management.md](role-assignment-management.md), [permission-catalog.md](permission-catalog.md), and [check-access.md](check-access.md).

## Global Flags

Every command accepts these flags (omitted from per-command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath expression to filter output |
| `--log-level <level>` | Log level: `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs to file instead of stderr |
| `--login-validity <minutes>` | Override token validity — forces refresh if token expires within this window |

Organization is resolved automatically from the active login session.

## Prerequisites

```bash
uip login status --output json
```

If not logged in: `uip login`.

## Concepts

- **PAP vs PDP.** Roles and role assignments live at the Policy Administration Point. `check-access` is the Policy Decision Point — it computes effective access for a principal at a scope, including services that don't expose assignments via `roles assignments list`.
- **Role shape values** (`--scope` on `roles create/update`): `Organization`, `TenantGlobal`, `Tenant`, `Project`. **No `Folder`** — folder-level scoping is expressed only on assignments, not on the role definition.
- **`TenantGlobal` vs `Tenant`.** `Tenant` = role is bound to one specific tenant UUID. `TenantGlobal` = role is a reusable template, available in every tenant of the org.
- **Service-managed roles.** `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining` own their role catalogs server-side. `roles list --service <svc>` and `roles assignments list --service <svc>` **do** surface their roles and assignments; only `roles create / update / delete` is blocked against these services. Mutate them via the service's own CLI (e.g. `uip or roles ...` for Orchestrator). Use `check-access` for *effective* access (PDP — includes server-side rules not visible via the catalog).
- **Platform-level services** — `authz`, `oms`, `platform`, `identity`, `licensing` — reject custom-role authoring (same as service-managed). Listing works.
- **`--service` infers scope** on `roles create/update/list` and `permissions list`. E.g. `--service studio` resolves to `Tenant`; `--service apps` to `Organization`. Combine `--service` with `--scope` only to override the registry default.
- **No `--service centralizedaccess`.** The CLI rejects this value on `roles create/list`, `roles assignments list`, and `permissions list` with `'centralizedaccess' is not a valid --service value`. For the multi-service "Centralized Access" tenant/org role and the matching listings, **omit `--service`** and use `--scope <Tenant|Organization|TenantGlobal>` alone.
- **PUT-style upsert.** `roles create` and `roles update` share an endpoint. The CLI assembles the full role body from your inline flags + the `--file` actions array; submitting `update` with only some inline flags still rewrites the entire role (re-fetch first).
- **Built-in roles** (`type: BuiltIn`) cannot be created, updated, or deleted.
- **Principal types** (`--identity-type` on assignments): `User | Group | Robot | ExternalApplication`.

---

## Roles — `uip admin authorization roles`

### `roles list`

List roles in the organization.

```bash
uip admin authorization roles list --output json
uip admin authorization roles list --scope Organization --output json
uip admin authorization roles list --scope Tenant --output json                     # multi-service tenant roles (no --service)
uip admin authorization roles list --service studio --filter Admin --output json
uip admin authorization roles list --role-type Custom --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Substring match on role name |
| `--service <name>` | No | Restrict to one service's role definitions; sets `--scope` from registry when used alone. See Concepts → no `--service centralizedaccess` |
| `--scope <type>` | No | Filter by role shape: `Organization`, `TenantGlobal`, `Tenant`, `Project`, or `Folder` (case-insensitive). Optional when `--service` is provided |
| `--role-type <BuiltIn\|Custom>` | No | Restrict by type |
| `--tenant-id <guid>` | No | Restrict to roles scoped to a specific tenant. Resolve via `uip admin tenants list --filter <name>` |
| `-l, --limit <number>` | No | Items per page |
| `--offset <number>` | No | Items to skip |

**Output code:** `AuthzRolesList`.

### `roles get`

Fetch a role by id. Response includes `ownerServiceId` + **`ownerServiceName`** — the role's permanent service binding (e.g., `Reinfer`, `DocumentUnderstanding`, `CentralizedAccess`). Read these before creating assignments — see [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-roles-owning-service-vs-assignment-scope-path).

```bash
uip admin authorization roles get <ROLE_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<ROLE_ID>` | Yes | Role UUID. Obtain from `roles list` |

**Output code:** `AuthzRoleGet`.

### `roles create`

Create a custom role. Inline flags carry the role metadata; `--file` carries the granted actions as a JSON string array.

```bash
# Multi-service tenant role ("Centralized Access") — NO --service, omit it
uip admin authorization roles create \
  --scope Tenant \
  --tenant-id <TENANT_ID> \
  --name "Tenant Reader" \
  --file ./actions.json --output json

# Organization-shape role — multi-service org role (no --service)
uip admin authorization roles create \
  --scope Organization \
  --name "Org Reader" \
  --description "Read-only org admin" \
  --file ./actions.json --output json

# Service-specific role — scope inferred from the service registry (studio → Tenant)
uip admin authorization roles create \
  --service studio \
  --name "Studio Author" \
  --file ./actions.json --output json

# Tenant-global template — reusable across every tenant in the org (no --service)
uip admin authorization roles create \
  --scope TenantGlobal \
  --name "Tenant Reader Template" \
  --file ./actions.json --output json

# Project-scope role for a service that registers Project-shape permissions
uip admin authorization roles create \
  --scope Project \
  --service documentunderstanding \
  --name "DU Project Editor" \
  --file ./actions.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes | Role display name |
| `--description <text>` | No | Human-readable description |
| `--service <name>` | Conditional | Owning service; required for `--scope Project`. Used alone, infers scope from the registry. See Concepts → no `--service centralizedaccess` |
| `--scope <type>` | Conditional | Role shape: `Organization`, `TenantGlobal`, `Tenant`, `Project` (case-insensitive). Optional when `--service` is provided |
| `--tenant-id <guid>` | No | Tenant UUID. Only valid when the resolved scope is `Tenant` or `Project`. Defaults to the login tenant |
| `--file <path>` | Yes | Path to a JSON file containing the granted actions as a string array |

> **Summary etiquette:** when reporting `roles create` results to the user, always state the resolved service explicitly — `service: <name>` if `--service` was passed, or `service: none — multi-service <scope> role` if omitted.

`./actions.json`:

```json
["STUDIO.X.Y", "STUDIO.A.B", "STUDIO.NUGET.LIST"]
```

Each string is a permission `name` resolved via `permissions list`. **Permission names, not UUIDs.**

**Output code:** `AuthzRoleCreated`.

### `roles update`

Update an existing custom role. Same endpoint as `create` (PUT-style upsert). The CLI assembles the full body from the positional `<ID>` + your inline flags + the `--file` actions array — re-fetch the role first, edit, then submit, so you don't lose fields.

```bash
uip admin authorization roles update <ROLE_ID> \
  --scope Tenant \
  --name "Tenant Reader v2" \
  --file ./actions.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ROLE_ID>` | Yes | Role UUID. Positional id always wins over any body-side id |
| `--name <name>` | No | Role display name |
| `--description <text>` | No | New description |
| `--service <name>` | Conditional | Owning service; required for `--scope Project`. See Concepts → no `--service centralizedaccess` |
| `--scope <type>` | Conditional | Role shape: `Organization`, `TenantGlobal`, `Tenant`, `Project` |
| `--tenant-id <guid>` | No | Tenant UUID. Valid only for `Tenant`/`Project` scopes |
| `--file <path>` | No | Replacement actions array (string array). Omitting it preserves the current action set |

**Output code:** `AuthzRoleUpdated`.

### `roles delete`

Delete a custom role. Only `type: Custom` roles can be deleted.

```bash
uip admin authorization roles delete <ROLE_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<ROLE_ID>` | Yes | Role UUID |

The CLI pre-fetches and refuses service-managed / platform-owned roles with a redirect.

**Output code:** `AuthzRoleDeleted`.

---

## Role Assignments — `uip admin authorization roles assignments`

An assignment is the triple **(principal, role, scope)**.

### `roles assignments list`

List assignments grouped by identity.

```bash
uip admin authorization roles assignments list --output json
uip admin authorization roles assignments list --scope Organization --output json
uip admin authorization roles assignments list --scope Tenant --tenant-id <TENANT_ID> --output json
uip admin authorization roles assignments list --scope Folder --scope-id Insights --output json
uip admin authorization roles assignments list --scope Project --scope-id <PROJECT_ID> --output json
uip admin authorization roles assignments list --scope Tenant --output json    # multi-service tenant assignments (no --service)
uip admin authorization roles assignments list --identity-id <PRINCIPAL_ID> --output json
uip admin authorization roles assignments list --include-inherited --output json
uip admin authorization roles assignments list --scope-path "/tenant/<TID>/Reinfer" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--identity-id <id>` | No | Filter by principal UUID (server-side) |
| `--service <name>` | No | Filter by service (server-side); combines with `--scope` or sets the scope path from the registry. See Concepts → no `--service centralizedaccess` |
| `--scope <type>` | No | `Organization`, `Tenant`, `Project`, `Folder`, or `App`. Default: `Tenant`. **`TenantGlobal` is not valid here.** Project/Folder/App require `--service` and `--scope-id` |
| `--scope-id <id>` | Conditional | Project id / folder name or id / app id when `--scope` is Project/Folder/App. Combined with `--service` to build the sub-scope path |
| `--scope-path <path>` | No | Advanced: send the exact path verbatim. Overrides `--scope`, `--tenant-id`, `--scope-id` |
| `--tenant-id <guid>` | No | Tenant UUID. Defaults to the login tenant when scope is Tenant/Project/Folder/App |
| `--include-inherited` | No | Also surface assignments inherited from parent scopes (default: direct only) |
| `-l, --limit <number>` | No | Server caps at 10 assignment groups per page |
| `--offset <number>` | No | Items to skip |

**Output code:** `AuthzAssignmentsList`.

### `roles assignments create`

Create one (inline) or many (`--file`) assignments.

> **Pre-flight required: role-service must match scope-path service segment.** Before submitting, fetch the role via `roles get <ROLE_ID>` and validate that the scope-path you're about to send matches the role's `ownerServiceName` (case-insensitive `lowercase(ownerServiceName) == <svc>` segment in the path). For `ownerServiceName == "CentralizedAccess"`, the path must NOT include a service segment. Full procedure: [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-roles-owning-service-vs-assignment-scope-path).

```bash
# Inline — tenant id auto-fills from the login session
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <PRINCIPAL_ID> \
  --identity-type User --output json

# Specific tenant
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <PRINCIPAL_ID> \
  --identity-type User \
  --tenant-id <TENANT_ID> --output json

# Folder / Project / App scope — pass the exact scope path
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <GROUP_ID> \
  --identity-type Group \
  --scope-path "/tenant/<TID>/Reinfer/project/<PID>" --output json

# Batch — array of AddRoleAssignmentRequest
uip admin authorization roles assignments create --file ./assignments.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--role-id <id>` | Yes (inline) | Role UUID |
| `--identity-id <id>` | Yes (inline) | Principal UUID |
| `--identity-type <type>` | Yes (inline) | `User`, `Group`, `Robot`, `ExternalApplication` |
| `--service <name>` | No | Owning service; combines with `--scope`, or used alone sets the scope path from the registry |
| `--scope <type>` | No | `Organization`, `TenantGlobal`, `Tenant`, `Project`, `Folder`, or `App`. Project/Folder/App require `--service` and `--scope-id` |
| `--scope-id <id>` | Conditional | Project id / folder name or id / app id for `--scope Project|Folder|App` |
| `--scope-path <path>` | No | Advanced: send the exact path verbatim. Overrides `--scope`, `--service`, `--scope-id`, `--tenant-id` |
| `--tenant-id <guid>` | No | Tenant UUID for Tenant / TenantGlobal / Project / Folder / App scopes. Defaults to the login tenant |
| `--file <path>` | Alternative | Batch — JSON array of `AddRoleAssignmentRequest` |

Inline auto-fills scope path from the role's `scopeType` when no `--scope`/`--scope-path` is given:

| Role scope | Auto-filled path |
|------------|------------------|
| `Organization` | `/` |
| `Tenant` / `TenantGlobal` | `/tenant/<TENANT_ID>` (defaults to login tenant) |
| `Project` / `Folder` / `App` | **Not auto-filled** — pass `--scope` + `--service` + `--scope-id`, or use `--scope-path` |

Batch `assignments.json`:

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

The bulk endpoint is atomic — partial failure rolls back the whole batch.

**Output code:** `AuthzAssignmentCreated`.

### `roles assignments delete`

Delete one (positional) or many (`--file`) assignments.

```bash
uip admin authorization roles assignments delete <ASSIGNMENT_ID> --output json
uip admin authorization roles assignments delete --file ./assignment-ids.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<ASSIGNMENT_ID>` | No (with `--file`) | Single assignment UUID |
| `--file <path>` | Alternative | JSON array of UUID strings |

Batch `assignment-ids.json`:

```json
["0fae98e1-0f2e-4f8d-bdab-7ce1cf475676", "1aab33cf-..."]
```

**Idempotency caveat:** the bulk endpoint silently no-ops on unknown / already-deleted ids and still returns Success. To confirm a deletion took effect, list before and after.

**Output code:** `AuthzAssignmentDeleted`.

---

## Permissions — `uip admin authorization permissions`

### `permissions list`

Read-only catalog of permission definitions across services. Each record carries `id`, `name`, `namespace`, `serviceDisplayName`, `resourceType`, `resourceAction`, `resourceGroup`, `scopeType`.

```bash
uip admin authorization permissions list --output json
uip admin authorization permissions list --scope Organization --output json
uip admin authorization permissions list --scope Tenant --output json                       # multi-service tenant catalog (no --service)
uip admin authorization permissions list --service studio --output json
uip admin authorization permissions list --scope Project --service documentunderstanding --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--service <name>` | No | Restrict to one service. Combines with `--scope`, or used alone sets the scope from the service registry. Known: `apps, authz, automationops, casemanagement, dataservice, documentunderstanding, identity, insights, licensing, oms, orchestrator, platform, processmining, reinfer, studio, taskmining, testmanager`. Other names accepted free-form. See Concepts → no `--service centralizedaccess` |
| `--scope <type>` | No | Filter by role shape: `Organization`, `TenantGlobal`, `Tenant`, or `Project` (case-insensitive). Optional when `--service` is provided |

`authz` cross-cutting permissions are filtered out by default — pass `--service authz` to surface them.

**Output code:** `AuthzPermissionsList`.

> Permission `name` strings (e.g., `STUDIO.X.Y`) — not UUIDs — are what go into `roles create --file ./actions.json`.

---

## Check Access — `uip admin authorization check-access`

Compute the effective permissions a principal has at a scope (Policy Decision Point). Includes services that manage their own roles and do NOT surface via `roles assignments list`.

```bash
# Default scope = Tenant, defaults to login tenant
uip admin authorization check-access <USER_GUID> --output json

# Resolve the user by email substring — the identity API does the lookup
uip admin authorization check-access alice@example.com --output json

# Non-login tenant
uip admin authorization check-access <USER_GUID> --tenant-id <TENANT_ID> --output json

# Restrict to one service
uip admin authorization check-access <USER_GUID> --service orchestrator --output json

# Folder scope
uip admin authorization check-access <USER_GUID> --scope Folder --folder-id <FOLDER_ID> --output json

# Advanced — file body for filters not exposed inline (e.g. RoleNameStartsWith)
uip admin authorization check-access --file ./check-access.json --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<identity>` | Yes (inline) | User UUID, name, or email. Positional. Required unless `--file` is supplied |
| `--scope <type>` | No | Scope at which to evaluate access. Accepts **`Tenant`** (default) or **`Folder`** only — no `Organization` / `Project` |
| `--tenant-id <guid>` | No | Tenant UUID. Defaults to login tenant. For `Tenant` scope it is used as both `Id` and `ParentId`; for `Folder` scope it is the `ParentId` |
| `--folder-id <guid>` | Conditional | Folder UUID. Required when `--scope Folder`. Used as the scope `Id` |
| `--service <name>` | No | Restrict to a specific service (useful for services that manage their own roles) |
| `--file <path>` | Alternative | Full request body. Mutually exclusive with the positional identity and scope flags |

`--file ./check-access.json`:

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

Returned `Data`:
- `roleAssignments` — paginated effective assignments
- `grantedServicesMetadata` — services the principal has any access to
- `grantedRolesMetadata` — roles contributing to the result

**Output code:** `AuthzCheckAccess`.

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `cannot create roles for service X` | Service is service-managed or platform-level | Use the service's own CLI (e.g., `uip or roles create` for Orchestrator) |
| `role not found` | Invalid role id | Run `roles list` to find the correct id |
| `cannot delete built-in role` | Target is `BuiltIn` | Only `Custom` roles can be deleted |
| Updated role lost actions | `--file` omitted on update | Re-run `update` with `--file ./actions.json` populated, or fetch + edit + resubmit |
| `invalid action name` | Permission name not in catalog | Re-resolve via `permissions list --service <SERVICE>` and copy the `name` value verbatim |
| `principal not found` | Invalid identity id / email | Resolve via `uip admin users list --search <EMAIL>` or the matching identity command |
| `scope path required` | Folder/Project/App role with no `--scope-path` and no `--scope`/`--service`/`--scope-id` triple | Pass `--scope Folder --service <svc> --scope-id <id>`, or pass `--scope-path` explicitly |
| `folder-id required` | `check-access --scope Folder` without `--folder-id` | Pass the folder UUID; `--tenant-id` defaults to login tenant for the ParentId |
| Empty `roleAssignments` | Principal has no effective access at this scope | Confirm via `roles assignments list --identity-id <ID>` |
| Auth error | Login expired | `uip login status`, then `uip login` |

---

## Provenance contract for completion output

Authz entitlements are anchored to a specific **organization**, **tenant** (or `TenantGlobal` template), and **service**. Every authz result the agent surfaces must show those three coordinates with UUIDs resolved to human-readable names — never leave a raw `tenantId` or `roleId` in user-facing output.

| Verb | Always surface alongside the result |
|---|---|
| `roles list` / `roles get` | role name; `scopeType` (`Organization` / `TenantGlobal` / `Tenant` / `Project`); **owning service** read directly as `ownerServiceName`; **display name** for user-facing output (see mapping below); **tenant binding** (`tenantId` → tenant name; zero-GUID → "TenantGlobal / unbound") |
| `roles create` / `roles update` | the role summary above, plus permission count, derived from a follow-up `roles get <id>` |
| `roles assignments list` | role name; principal type + name (resolve UUIDs); **scope path with names**, not UUIDs (e.g., `/tenant/Prod-East/IXP/project/Invoices-AP`, not `/tenant/abc.../Reinfer/project/def...`) |
| `roles assignments create` / `delete` | the assignment summary above; for batch, summarize per role + scope |
| `permissions list` | group rows by `serviceDisplayName`; show `name`, `scopeType`, and a per-service row-count summary up front (e.g., "Studio (24), Identity (12), Apps (8)") |
| `check-access` | the **tenant** the check ran against (login tenant or `--tenant-id` override); group `roleAssignments.results[]` rows **by `serviceName`** (which is already the display name) with a one-line "spans N services: A, B, C" summary up front; **for each role, label as `direct` or `inherited from <Group name>`** by inspecting the nested `roleAssignments[].securityPrincipalType` — `User` (with id matching the query) → direct; `Group` → inherited (resolve the `securityPrincipalId` to its `displayName` via `uip admin groups get <id>`) |

### Service display-name mapping (CLI `ownerServiceName` → user-facing label)

`ownerServiceName` returns a slug-like value; the user-facing **display name** is different for several services. Always translate before surfacing:

| `ownerServiceName` (response) | Display name (use in user-facing output) | Slug for `--service` / scope-path |
|---|---|---|
| `Reinfer` | **IXP** | `reinfer` |
| `DocumentUnderstanding` | Document Understanding | `documentunderstanding` |
| `ProcessMining` | Process Mining | `processmining` |
| `AutomationOps` | Automation Ops | `automationops` |
| `CentralizedAccess` | Centralized Access | (omit `--service` — CLI rejects this slug) |
| `Orchestrator`, `Insights`, `Apps`, `AuthZ`, `OMS`, `Platform`, etc. | (same as `ownerServiceName`) | `lowercase(ownerServiceName)` |

The `serviceName` field on `check-access` `roleAssignments.results[]` already returns the display-name form (e.g., `"Data Service"`, `"IXP"`) — surface it verbatim. Use this mapping when the field you have is `ownerServiceName` instead.

After any authz **mutation**: (1) show the command result + new resource id; (2) apply the contract above to the post-mutation state by re-fetching via `roles get` / `roles assignments list --identity-id <ID>`; (3) offer a next step ("assign this role?", "run `check-access` to verify?").
