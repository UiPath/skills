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
| `Robot` | `uip admin robot-accounts list --search "<NAME>" --output json` ([robot-account-management.md](../robot-account-management.md)) | `--identity-type Robot` |
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

`roles assignments list --service <svc>` accepts all services, including service-managed (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`) and platform-level (`authz`, `oms`, `platform`, `identity`, `licensing`). The endpoint may return `403 Forbidden` without the service's read permission; the CLI does not filter these services client-side.

For `orchestrator`, `dataservice`, `testmanager`, and `taskmining`, the list does not return the assignments of their roles. With `--service`, it fails with 403. If the error `Message` says that the service manages its own role assignments, this 403 is not about the permissions of the caller. Handle any other 403 as a permission or token-scope failure. [Services and role ownership](role-management.md#services-and-role-ownership) tells how to tell the two 403s apart, and which tool to use for these services.

Authoring with `assignments create --service <svc>` is rejected for those services. Never use `--scope-path` to get past this refusal for `orchestrator`, `dataservice`, `testmanager`, or `taskmining`. Such an assignment goes into the Authorization Service only, and the next sync from the owning service can overwrite it. For the other services, use `--scope-path` only when the registry refuses the service. You must also have the scope path of the role from another source. Tell the user that the next sync from a service-managed service can overwrite such an assignment.

### Data Fabric role assignments

Data Fabric (`dataservice`) manages its own roles. Use `uip df roles` and `uip df directory` for Data Fabric roles, not `uip admin authorization`. These commands do not show in `uip df --help`, but they work.

| Task | Command |
|---|---|
| Show the Data Fabric roles of one principal | `uip admin authorization check-access "<PRINCIPAL>" --service dataservice --output json` |
| List the Data Fabric roles (system and user-defined) with their IDs | `uip df roles list --output json`. Add `--no-stats` to skip the counts. |
| List the principals (users, groups, applications) with their Data Fabric roles, for example "who has Data Fabric Admin?" | `uip df directory list --limit <LIMIT> --offset <OFFSET> --output json` |
| Add roles to principals | `uip df directory assign-roles <PRINCIPAL_ID> --type <User\|Group\|Application> --role-ids <DF_ROLE_ID_1>,<DF_ROLE_ID_2> --output json` |
| Remove all direct Data Fabric roles of principals | `uip df directory revoke-roles <PRINCIPAL_ID> --yes --reason "<REASON>" --output json` |

`assign-roles` and `revoke-roles` accept more than one `<PRINCIPAL_ID>`. `uip df directory list` returns a page of 50 principals by default. Page with `--limit` and `--offset` to the end before you decide that a principal is not in the list.

1. **Get `--role-ids` from `uip df roles list` only.** The Authorization Service and Data Fabric use different IDs for the same role. A role ID from `check-access` or `uip admin authorization roles list` does not work with `assign-roles`. Match the role by name, then copy its ID from `uip df roles list`.
2. **Confirm every write with the user first.** Resolve the principal under [Resolve Principals Before Mutation](#resolve-principals-before-mutation). Show the principal, the `--type`, the role names, and the UI access. Run `assign-roles` or `revoke-roles` only after the user confirms.
3. **`assign-roles` adds roles and keeps the existing roles.** `--replace` replaces the full Data Fabric role set of the principal.
4. **`assign-roles` also turns on Data Fabric UI access, unless you pass `--no-ui-access`.** Before the write, read `IsUIEnabled` for the principal in `uip df directory list`. If it is `false`, pass `--no-ui-access`. If the principal is not in the list, pass `--no-ui-access` unless the user approves UI access. Turn on UI access only when the user approves it.
5. **`revoke-roles` removes all direct Data Fabric roles of each principal.** It cannot remove only one role. To remove only some roles, run `assign-roles --replace` with the roles to keep. Roles that come from a group stay until the group membership changes.
6. **Use the `Type` that `uip df directory list` shows for the principal as `--type`.** Robot accounts appear in that list as `Type: "User"` (`ObjectType: "DirectoryRobotUser"`). If the principal is not in the list, tell the user which `--type` you will use before the write.
7. **`<PRINCIPAL_ID>` is the identity ID of the user, group, or robot account.** `uip df directory list` shows this ID as `ExternalId`.

After a write, run `check-access "<PRINCIPAL>" --service dataservice` again to confirm the result.
