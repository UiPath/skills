# Role Assignment Management

Manage **who has what role at what scope** with `uip admin authorization roles assignments`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Concept and Scope Rules

An assignment is **(principal, role, scope)**:

- **Principal:** User, Group, Robot, or ExternalApplication (UUID).
- **Role:** role id visible via `roles list`.
- **Scope:** `Organization`, `Tenant`, `TenantGlobal`, `Project`, `Folder`, or `App`.

Assignments live at the Policy Administration Point (PAP); `check-access` computes effective access at a scope (Policy Decision Point). See [check-access.md](check-access.md).

Role and assignment scope vocabularies differ:

- `roles create --scope`: `Organization`, `TenantGlobal`, `Tenant`, `Project` only.
- `roles assignments create --scope`: `Organization`, `TenantGlobal`, `Tenant`, `Project`, `Folder`, `App`.
- `roles assignments list --scope`: `Organization`, `Tenant`, `Project`, `Folder`, `App`; `TenantGlobal` is invalid.

## Resolve Principals Before Mutation

**Mandatory:** before any `assignments create` or `assignments delete`, search the directory for every named principal and echo the resolved identity. `--identity-id` is a raw GUID and is not validated against the prompt's name. Never silently substitute a UUID or the current login user. Granting a role to the wrong principal is a security incident (SKILL.md → *"Resolve every named principal before high-risk ops"* Critical Rule — covers zero-match-stop, multi-match-menu, and the no-silent-fallback-to-login-user requirement).

| Principal type | Search command | Identity flag |
|---|---|---|
| `User` | `uip admin users list --search "<NAME_OR_EMAIL>" --output json` ([user-management.md](../user-management.md)) | `--identity-type User` |
| `Group` | `uip admin groups list --filter "<NAME>" --output json` ([group-management.md](../group-management.md)) | `--identity-type Group` |
| `Robot` | `uip admin robot-accounts list --filter "<NAME>" --output json` ([robot-account-management.md](../robot-account-management.md)) | `--identity-type Robot` |
| `ExternalApplication` | `uip admin external-apps list --output json` (filter client-side) ([external-app-management.md](../external-app-management.md)) | `--identity-type ExternalApplication` |

### Echo-before-mutate protocol

1. **Run** the applicable search command for the requested name.
2. Branch on hit count:
   - **0:** stop; say the name did not match and request corrected spelling or a UUID. Do not fall back to the login user or guess fuzzy matches.
   - **More than 1:** present `displayName — userName — id` as a numbered list and stop until the user supplies a digit.
   - **1:** proceed.
3. Echo `Principal: <displayName> (<userName>) — <id>`.
4. Only then run `assignments create` or `assignments delete` with the verified `--identity-id`.

Apply this protocol even when the user disables clarifying questions; security verification is a safety floor.

## Validate Role Service Binding and Scope Path

`roles list` and `roles get` return `ownerServiceId` and `ownerServiceName`. `ownerServiceName` is the permanent service binding, set by `roles create --service <svc>` or by `--scope <Org|Tenant|TenantGlobal>` without `--service` (`CentralizedAccess`). It must match the assignment scope path:

| `ownerServiceName` | Required path | Construction |
|---|---|---|
| `CentralizedAccess` | No service segment: `/` for Organization or `/tenant/<tid>` for Tenant / TenantGlobal | Omit `--service`; use `--scope Organization` or `--scope Tenant` |
| Anything else, such as `Reinfer`, `DocumentUnderstanding`, `Apps`, or `Orchestrator` | Service segment matching `lowercase(ownerServiceName)`: `/tenant/<tid>/<svc>[/...]` for tenant services or `/<svc>` for organization services | Pass `--service <slug>` or use `--scope-path` verbatim |

Use `slug = lowercase(ownerServiceName)`: `Reinfer` → `reinfer`, `DocumentUnderstanding` → `documentunderstanding`, `ProcessMining` → `processmining`, `AutomationOps` → `automationops`, `AuthZ` → `authz`. Never pass `--service centralizedaccess`; omit `--service` for the umbrella. For user-facing summaries, use display names: `Reinfer` → **IXP**, `DocumentUnderstanding` → **Document Understanding**, `ProcessMining` → **Process Mining**, `AutomationOps` → **Automation Ops**, `CentralizedAccess` → **Centralized Access**. Keep CLI slugs in echoed paths. See [authorization-commands.md — Service display-name mapping](authorization-commands.md#service-display-name-mapping).

### Mandatory create pre-flight

1. **Run** `uip admin authorization roles get <ROLE_ID> --output json`; extract `ownerServiceName` and `scopeType`.
2. Compute the expected path:
   - `CentralizedAccess`: `/` for `Organization`, `/tenant/<tid>` for `Tenant` or `TenantGlobal`; no service segment.
   - Otherwise: include `lowercase(ownerServiceName)` immediately after `/tenant/<tid>` or at the organization root.
3. If the intended path mismatches, stop and surface it. Never substitute a service or coerce the path. Offer: target the correct service, choose a role owning the intended service, or reauthor the role under that service.
4. Echo `Role: <name> — ownerServiceName: <ownerServiceName> (scopeType: <scopeType>)` before mutation.

## Scope Path Construction

Inline `assignments create` fills paths as follows:

| Role scope | Auto-filled path | Override |
|---|---|---|
| `Organization` | `/` | — |
| `Tenant` / `TenantGlobal` | `/tenant/<TENANT_ID>` (defaults to login tenant) | `--tenant-id <GUID>` |
| `Project` / `Folder` / `App` | Not auto-filled | `--scope` + `--service` + `--scope-id`, or `--scope-path <PATH>` |

For sub-scopes, use either:

- **Structured:** `--scope Project --service reinfer --scope-id <PROJECT_ID>`.
- **Verbatim:** `--scope-path /tenant/<TID>/Reinfer/project/<PID>`, which overrides `--scope`, `--service`, `--scope-id`, and `--tenant-id`.

Platform shape: `/tenant/<TENANT_ID>/<SERVICE_OR_FOLDER>/project/<PROJECT_ID>`.

## Create One Assignment

1. **Run** the applicable principal search and follow the [Echo-before-mutate protocol](#echo-before-mutate-protocol).
2. **Run**:
   ```bash
   uip admin authorization roles list --filter "<ROLE_NAME>" --output json
   ```
3. **Run** the role pre-flight above; extract `ownerServiceName` and `scopeType`, validate the path, and echo the role binding.
4. **Run** the matching create command.

Organization / Tenant / TenantGlobal:
```bash
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <PRINCIPAL_ID> \
  --identity-type User --output json
```

Tenant role on a non-login tenant:
```bash
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <PRINCIPAL_ID> \
  --identity-type User \
  --tenant-id <TENANT_ID> --output json
```

Project / Folder / App, structured:
```bash
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <GROUP_ID> \
  --identity-type Group \
  --scope Project \
  --service reinfer \
  --scope-id <PROJECT_ID> --output json
```

Project / Folder / App, verbatim:
```bash
uip admin authorization roles assignments create \
  --role-id <ROLE_ID> \
  --identity-id <GROUP_ID> \
  --identity-type Group \
  --scope-path "/tenant/<TID>/Reinfer/project/<PID>" --output json
```

## Batch Create

Use `--file` with a JSON array of `AddRoleAssignmentRequest`:

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

```bash
uip admin authorization roles assignments create --file ./assignments.json --output json
```

The bulk endpoint is atomic; partial failure rolls back the whole batch.

## Batch Delete

Use `assignment-ids.json` as a JSON array of UUID strings:

```json
["<ASSIGNMENT_ID_1>", "<ASSIGNMENT_ID_2>"]
```

```bash
uip admin authorization roles assignments delete --file ./assignment-ids.json --output json
```

The bulk endpoint silently no-ops on unknown or already-deleted ids and still returns Success. To confirm deletion, list before and after. Discover assignment ids via `roles assignments list`.

## Pagination and Filters

- The server caps `--limit` at 10 assignment groups per page.
- With `--scope Folder|Project|App --scope-id`, filtering occurs client-side after page retrieval. Post-filter results can be fewer than `--limit` while later pages contain more matches. Use `--scope-path` for strict server-side pagination math.
- With client-side filtering, `totalCount` is the post-filter group count, not the organization-wide total.
- `--scope TenantGlobal` is invalid on list; use `--scope Tenant` to surface tenant-scope assignments. The role records TenantGlobal versus Tenant.
- `--include-inherited` walks Org → Tenant → sub-scope. Default is direct only (`noInheritance=true`); use the flag when asking what a principal effectively has at a scope, including inherited grants.

## Service-Managed and Platform Services

`roles assignments list --service <svc>` works for all services, including service-managed (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`) and platform-level (`authz`, `oms`, `platform`, `identity`, `licensing`). The endpoint may return `403 Forbidden` without the service's read permission; the CLI does not filter these services client-side.

Authoring with `assignments create --service <svc>` is rejected for those services. Use `--scope-path` only when you already have the role's scope path from another source and need to assign against a service the registry will not accept.
