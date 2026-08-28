# Role Management

Use this skill for multi-step workflows managing custom roles with `uip admin authorization roles`. See [authorization-commands.md](authorization-commands.md) for per-command flags, output codes, and single-command examples.

## Services and role ownership

Listing works for all services; authoring does not for service-managed or platform-level roles.

- **Service-managed:** `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`. Run `roles list --service <svc>` and `roles assignments list --service <svc>`; mutate with the service CLI, such as `uip or roles create` for Orchestrator.
- **Platform-level:** `authz`, `oms`, `platform`, `identity`, `licensing`. Listing works; authoring is rejected.

For effective principal access, use PDP via [check-access.md](check-access.md); it includes server-side rules not visible in the catalog.

## Role shape and service resolution

`roles create --scope <type>` accepts:

| Mode | Use | `--service` | `--tenant-id` |
|---|---|---|---|
| `Organization` | Organization-wide access, typically `apps`, `studio`, or `identity` permissions | Optional; omit for a multi-service org role | Ignored |
| `TenantGlobal` | Reusable template visible/assignable in every tenant | Optional; omit for a multi-service template | Ignored |
| `Tenant` | Bound to one tenant and assignable only there | Optional; omit for a multi-service Centralized Access tenant role | Defaults to login tenant; pass explicitly for another tenant |
| `Project` | Project-shaped role, such as Document Understanding or Reinfer | Required | Defaults to login tenant |

`Folder` is invalid for `roles create/update`; express folder scope on the assignment in [role-assignment-management.md](role-assignment-management.md).

`--service` infers scope from the service registry when `--scope` is omitted. For example, `roles create --service studio --name "..."` resolves to `Tenant`; combine them only to override the registry, such as `--service documentunderstanding --scope Project`. Never guess a `serviceName`; use [permission-catalog.md — `--service` serviceNames](permission-catalog.md#--service-servicenames-and-how-to-re-derive-them) to find valid values and re-derive rejected ones.

When the user says **tenant role**, **create role in Tenant scope**, or **centralized access** without naming a service, use `--scope Tenant` and omit `--service`. This multi-service role can carry any `TENANT`-scope catalog permission. Never pass `--service centralizedaccess`; the CLI rejects it with `'centralizedaccess' is not a valid --service value`. Omit the flag for `roles list`, `roles assignments list`, and `permissions list` too. Apply the same omission rule to multi-service `Organization` and `TenantGlobal` roles. `Project` always requires `--service`.

Resolve intent as follows:

| Intent | Resolution |
|---|---|
| Names a service or permission registered by one service | Pass `--service <svc>`; let the registry infer scope unless overriding it |
| Says tenant role, tenant scope, or centralized access without a service | Omit `--service`; pass `--scope Tenant` (or `Organization` / `TenantGlobal`) |
| Names a project-shape service | Pass `--scope Project` and `--service <svc>` |

After `roles create`, highlight the exact service: quote `--service <name>`, or state `no --service — multi-service tenant role` when omitted. Never silently substitute a service or scope.

## Workflow: Grant Permission(s) to a Principal (Shortcut)

If the user names permissions but not a role or scope, such as “grant me X” or “give alice Y, Z,” use [grant-permissions.md](grant-permissions.md). It selects the role shape through intersection and menu steps. This document covers the role-first path: choose the shape, author it, then create assignments.

## Workflow: Create a Custom Role

This workflow is interactive. Do not ask for empty `<ROLE_NAME>` or `<PERMISSION_NAMES>` placeholders. Propose a name, show a numbered permission menu, and confirm.

### Step 1 — Gather intent and choose scope

Ask what the role is for, including target service(s) and access type such as read-only, operator, or admin.

#### Step 1a — Service-bound role

For one service, do not ask about organization versus tenant scope. Run:

```bash
uip admin authorization permissions list --service <SERVICE> --output json
```

`<SERVICE>` must be a real `serviceName`; look it up in [permission-catalog.md — `--service` serviceNames](permission-catalog.md#--service-servicenames-and-how-to-re-derive-them). Use each record’s `scopeType`:

| Records' `scopeType` | Shape | Next action |
|---|---|---|
| All `ORGANIZATION` | Org-level service | `Organization` |
| All `TENANT` | Tenant-level service | `Tenant`, then ask current-tenant binding versus `TenantGlobal` |
| All `PROJECT` | Project-shape service | `Project`, with `--service` |
| Mixed | Multi-scope service | Ask the target scope and show only that scope’s permissions |

If the user explicitly says Tenant scope, tenant role, or centralized access—even for a `PROJECT` permission—use the no-`--service` Tenant path in Step 1d. Do not substitute another permission; explain the mismatch and let the user choose. Catalog `scopeType` values are uppercase (`ORGANIZATION`, `TENANT`, `PROJECT`, `ANY`); CLI values are PascalCase: `ORGANIZATION` → `--scope Organization`, `TENANT` → `--scope Tenant` or `TenantGlobal`, and `PROJECT` → `--scope Project`.

#### Step 1b — Hoist overlapping permissions to the umbrella

Unless the candidate is `Project`, run this service-versus-umbrella check between Steps 1a and 1c:

```bash
# Tenant-service candidate (Step 1a returned `TENANT` scopeType)
uip admin authorization permissions list --scope Tenant --output json > umbrella.json

# Org-service candidate (Step 1a returned `ORGANIZATION` scopeType)
uip admin authorization permissions list --scope Organization --output json > umbrella.json
```

Compare candidate permission `name` values with umbrella `name` values:

- **No overlap:** keep the service-bound shape; continue to Step 1c for Tenant-shape, otherwise Step 2.
- **Full overlap:** show the applicable menu and recommend the umbrella.
- **Partial overlap:** show the split and stop; do not drop service-only permissions or silently add umbrella-only permissions.

For full overlap, render a numbered Markdown menu:

**Tenant-service candidate:**

1. **Tenant level (Recommended)** — multi-service role bound to one tenant and reusable across tenant services.
2. Service level — bound to `<SERVICE>` for strict isolation.
3. Tenant Global scope — multi-service template visible in every tenant.

Ask: `Reply with 1, 2, or 3.`

**Org-service candidate:**

1. **Org level (Recommended)** — multi-service organization role.
2. Service level — bound to `<SERVICE>` for strict isolation.

Ask: `Reply with 1 or 2.`

| Pick | Create-call shape | Continue at |
|---|---|---|
| Tenant level | `--scope Tenant` without `--service`; `--tenant-id` defaults to login | Step 2; binding already chosen |
| Org level | `--scope Organization` without `--service` | Step 2 |
| Service level | `--service <SERVICE>`; registry infers scope | Step 1c if Tenant-shape, otherwise Step 2 |
| Tenant Global scope | `--scope TenantGlobal` without `--service` | Step 2 |

Project permissions have no umbrella; skip Step 1b and use `--scope Project` with required `--service`.

#### Step 1c — Tenant versus TenantGlobal

For Tenant-shape permissions that remain service-bound, ask whether the role is:

- **Tenant:** bound to one tenant UUID with `--scope Tenant --tenant-id <UUID>` and assignable only there.
- **TenantGlobal:** reusable across every tenant with `--scope TenantGlobal`.

The Step 1b Tenant level and Tenant Global choices already decide this. Resolve the current tenant UUID by running `uip login status --output json` for the tenant name, then running `uip admin tenants list --filter <name> --output json` to map it to a UUID.

#### Step 1d — Multi-service tenant role

If the user said tenant role, tenant scope, or centralized access without naming a service—or pivots to Tenant scope—omit `--service` and run:

```bash
uip admin authorization permissions list --scope Tenant --output json
```

This is the UI’s Centralized Access catalog and can include any `TENANT`-scope permission across services, including Document Understanding `PROJECTS.*`, Licensing, IXP, and Authz. Render the Step 3 menu from this catalog.

If a named permission is `PROJECT`-only, explain that it cannot be placed in a Tenant role and offer:

1. The closest `TENANT`-scope analog.
2. Keep the existing Project-scope role.
3. A different permission set.

Never silently downshift to a similar-looking permission.

### Step 2 — Suggest a role name

Propose one intent-derived name using `<Service><Scope>-<Capability>` in PascalCase or kebab-case, such as `OrchestratorTenant-ReadOnly` or `IdentityOrg-GroupAdmin`. Check collisions by running:

```bash
uip admin authorization roles list --role-type Custom --filter "<SUGGESTED_NAME>" --output json
```

If matched, append `-2`, `-3`, and so on, rechecking until unique. Present the final name and let the user accept or override it in one reply.

### Step 3 — Present a numbered permission menu

Run the catalog query for each service and selected scope:

```bash
# Organization mode
uip admin authorization permissions list --service <SERVICE> --scope Organization --output json

# Tenant (or TenantGlobal — same catalog)
uip admin authorization permissions list --service <SERVICE> --scope Tenant --output json

# Project mode (service required)
uip admin authorization permissions list --service <SERVICE> --scope Project --output json
```

For multi-service roles, omit `--service` as required above. Render one Markdown table grouped by `serviceDisplayName`, with one global running number so the user can reply with `1, 4, 7-9`:

| # | Service | Permission | Scope | Description |
|---|---------|------------|-------|-------------|

Use 1-based global indexes. Show `serviceDisplayName` only on the first row of each group. Use the permission `name` (the value placed in `actions.json`), record `scopeType`, and `description` verbatim; if description is missing, use `<resourceAction> <resourceType>`. Sort by `serviceDisplayName`, then `resourceType`, then `resourceAction`. If one service exceeds ~30 entries, ask which `resourceType`(s) to narrow before rendering. Ask: `Reply with the numbers to include (e.g. 1, 3, 5-7).` Map selections internally to permission `name` strings, never UUIDs.

### Step 4 — Author `actions.json`

`--file` takes a flat JSON array of permission `name` strings, not a role body. The CLI builds the envelope from `--name`, `--description`, `--service`, `--scope`, and `--tenant-id`:

```json
["STUDIO.X.Y", "STUDIO.A.B", "IDENTITY.GROUP.READ"]
```

### Step 5 — Create and verify

Run the shape-matching command:

```bash
# Multi-service tenant role (Centralized Access): NO --service
uip admin authorization roles create \
  --scope Tenant \
  --tenant-id <TENANT_ID> \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Service-bound tenant role: scope inferred from registry
uip admin authorization roles create \
  --service documentunderstanding \
  --tenant-id <TENANT_ID> \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Organization: multi-service org role
uip admin authorization roles create \
  --scope Organization \
  --name "<CONFIRMED_NAME>" \
  --description "<DESCRIPTION>" \
  --file ./actions.json --output json

# TenantGlobal: reusable template
uip admin authorization roles create \
  --scope TenantGlobal \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Service-inferred: studio → Tenant
uip admin authorization roles create \
  --service studio \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Project: service required
uip admin authorization roles create \
  --scope Project \
  --service documentunderstanding \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json
```

Never pass `--service centralizedaccess`; omit `--service` for Centralized Access.

Verify by running:

```bash
uip admin authorization roles get <NEW_ROLE_ID> --output json
```

The endpoint is a PUT-style upsert. The positional `<ID>` carries identity on update; create generates it. Never put `id` in `actions.json`.

### Step 6 — Summarize the resolved service

After success, run `roles get <NEW_ROLE_ID>` and read canonical `ownerServiceName`. The response summary must include:

| Source | Render as |
|---|---|
| `ownerServiceName` | `service: <ownerServiceName>` |
| `ownerServiceName == "CentralizedAccess"` | `service: CentralizedAccess — multi-service <scope> role` |

For Centralized Access, any assignment scope-path must omit the service segment. This value is validated by [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-role-service-binding-and-scope-path). Apply the same requirement to `roles update`.

## Workflow: Update a Custom Role

The endpoint is the same upsert. The CLI builds the body from positional `<ID>`, inline flags, and the `--file` actions array. Re-fetch before editing because inline flags overwrite fields that are not supplied.

1. Run:
   ```bash
   uip admin authorization roles get <ROLE_ID> --output json
   ```
   Inspect `name`, `description`, `scopeType`, `tenantId`, and current actions.
2. For action-only changes, regenerate `actions.json` from a fresh `permissions list` query as in Step 3 and run:
   ```bash
   uip admin authorization roles update <ROLE_ID> --file ./actions.json --output json
   ```
3. For metadata changes, pass every metadata field to retain as well as changed fields; the CLI does not merge omitted values:
   ```bash
   uip admin authorization roles update <ROLE_ID> \
     --scope Tenant \
     --tenant-id <TENANT_ID> \
     --name "<NEW_NAME>" \
     --description "<NEW_DESC>" \
     --file ./actions.json --output json
   ```

## Workflow: Delete a Custom Role

1. Run:
   ```bash
   uip admin authorization roles get <ROLE_ID> --output json
   ```
   Verify `type` is `Custom`. The CLI also pre-fetches and refuses service-managed or platform-owned roles with a redirect.
2. Confirm deletion with the user.
3. Run `roles delete <ROLE_ID>`.
