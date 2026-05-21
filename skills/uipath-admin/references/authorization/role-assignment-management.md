# Role Assignment Management

Multi-step workflows for managing **who has what role at what scope** via `uip admin authorization roles assignments`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Concept

An assignment is the triple **(principal, role, scope)**:

- **Principal** — User, Group, Robot, or ExternalApplication (UUID).
- **Role** — id of a role visible via `roles list`.
- **Scope** — where the role applies: `Organization`, `Tenant`, `TenantGlobal`, `Project`, `Folder`, `App`.

Assignments live at the Policy Administration Point (PAP). Effective access at a scope is computed by `check-access` (the Policy Decision Point) — see [check-access.md](check-access.md).

> **Scope vocab difference** between roles and assignments:
> - `roles create --scope` accepts: `Organization`, `TenantGlobal`, `Tenant`, `Project`. (No `Folder`, no `App`.)
> - `roles assignments create --scope` accepts: `Organization`, `TenantGlobal`, `Tenant`, `Project`, `Folder`, `App`.
> - `roles assignments list --scope` accepts: `Organization`, `Tenant`, `Project`, `Folder`, `App`. (No `TenantGlobal`.)

## Resolving Principal IDs

**Mandatory:** before any `assignments create` or `assignments delete`, search the directory for the named principal and echo the resolved identity back to the user. Never accept a name-only request and silently substitute a UUID — `--identity-id` is a raw GUID the CLI does not validate against the human-readable name in the prompt. Granting a role to the wrong principal is a security incident (SKILL.md → *"Resolve every named principal before high-risk ops"* Critical Rule — covers zero-match-stop, multi-match-menu, and the no-silent-fallback-to-login-user requirement).

| Principal Type | Search command | Identity flag |
|----------------|----------------|---------------|
| `User` | `uip admin users list --search "<NAME_OR_EMAIL>" --output json` ([user-management.md](../user-management.md)) | `--identity-type User` |
| `Group` | `uip admin groups list --filter "<NAME>" --output json` ([group-management.md](../group-management.md)) | `--identity-type Group` |
| `Robot` | `uip admin robot-accounts list --filter "<NAME>" --output json` ([robot-account-management.md](../robot-account-management.md)) | `--identity-type Robot` |
| `ExternalApplication` | `uip admin external-apps list --output json` (filter client-side) ([external-app-management.md](../external-app-management.md)) | `--identity-type ExternalApplication` |

### Echo-before-mutate protocol

1. Run the search command above for the name in the user's request.
2. Branch on hit count:
   - **0 hits** → stop. Tell the user the name didn't match and ask them to confirm spelling or provide a UUID. Do not fall back to the current login user. Do not guess at fuzzy matches.
   - **>1 hits** → present a numbered list (`displayName — userName — id`) and stop. Wait for the user's digit.
   - **1 hit** → proceed.
3. Echo a line of the form `Principal: <displayName> (<userName>) — <id>` to the user before running the assignment mutation.
4. Only then run `assignments create` / `assignments delete` with the verified `--identity-id`.

This protocol is required even when the user explicitly disables clarifying questions — security verification is a safety floor, not a clarification.

## Validate Role's Owning Service vs. Assignment Scope-Path

`roles list` and `roles get` return `ownerServiceId` and `ownerServiceName` on every role. The **`ownerServiceName`** is the role's permanent service binding — set when the role was authored (`roles create --service <svc>` or `--scope <Org|Tenant|TenantGlobal>` without `--service` → `CentralizedAccess`). When creating an assignment, the role's `ownerServiceName` must align with the scope-path:

| Role `ownerServiceName` | Required scope-path shape | How to build it |
|---|---|---|
| `CentralizedAccess` (multi-service umbrella) | Path **must not** include a service segment: `/` (Organization) or `/tenant/<tid>` (Tenant / TenantGlobal) | Omit `--service`; use `--scope Organization` or `--scope Tenant` |
| Anything else (e.g., `Reinfer`, `DocumentUnderstanding`, `Apps`, `Orchestrator`) | Path **must include** the service segment matching `lowercase(ownerServiceName)`: `/tenant/<tid>/<svc>[/...]` for tenant-services, `/<svc>` for org-services | Pass `--service <slug>` (slug = `lowercase(ownerServiceName)`) — or use `--scope-path` verbatim |

**Slug mapping rule:** `slug = lowercase(ownerServiceName)`. Empirical examples: `Reinfer` → `reinfer`, `DocumentUnderstanding` → `documentunderstanding`, `ProcessMining` → `processmining`, `AutomationOps` → `automationops`, `AuthZ` → `authz`. The CLI rejects `--service centralizedaccess` — for the umbrella, omit `--service` entirely.

**User-facing display-name mapping:** the `ownerServiceName` slug is for the CLI; user-facing summaries must use the display name. Most-common rewrites: `Reinfer` → **IXP**, `DocumentUnderstanding` → **Document Understanding**, `ProcessMining` → **Process Mining**, `AutomationOps` → **Automation Ops**, `CentralizedAccess` → **Centralized Access**. When surfacing a role to the user (e.g., echoing `Role: <name> — ownerServiceName: <X>`), translate `<X>` to the display name; keep the slug in any scope-path you echo for clarity. Full mapping: [authorization-commands.md — Service display-name mapping](authorization-commands.md#service-display-name-mapping-cli-ownerservicename--user-facing-label).

### Pre-flight check (mandatory before `assignments create`)

1. Fetch the role: `uip admin authorization roles get <ROLE_ID> --output json`. Extract `ownerServiceName` and `scopeType`.
2. Compute the expected scope-path:
   - `ownerServiceName == "CentralizedAccess"` → path is `/` (if role `scopeType == Organization`) or `/tenant/<tid>` (if `Tenant` / `TenantGlobal`). No `<svc>` segment.
   - Otherwise → path must include `lowercase(ownerServiceName)` as the segment immediately after `/tenant/<tid>` (or as the root for org-services).
3. If the user's intended assignment scope-path doesn't match, **stop and surface the mismatch** — never silently substitute a different service or coerce the path. Example: a role with `ownerServiceName: "Reinfer"` cannot be assigned at `/tenant/<tid>/documentunderstanding/project/<pid>`; offer to (a) target the correct service, (b) pick a different role that owns the intended service, or (c) reauthor the role under the correct service.
4. Echo the resolved role binding alongside the principal echo: `Role: <name> — ownerServiceName: <ownerServiceName> (scopeType: <scopeType>)` so the user sees the binding before the mutation runs.

## Scope Path Construction

Inline `assignments create` auto-fills the scope path from the role's `scopeType`:

| Role scope | Auto-filled path | Override |
|------------|------------------|----------|
| `Organization` | `/` | — |
| `Tenant` / `TenantGlobal` | `/tenant/<TENANT_ID>` (defaults to login tenant) | `--tenant-id <GUID>` |
| `Project` / `Folder` / `App` | **Not auto-filled** | Either `--scope` + `--service` + `--scope-id`, OR `--scope-path <PATH>` |

Two ways to specify a sub-scope assignment:

1. **Structured** — let the CLI build the path from the registry: `--scope Project --service reinfer --scope-id <PROJECT_ID>`.
2. **Verbatim** — pass the exact path: `--scope-path /tenant/<TID>/Reinfer/project/<PID>`. Overrides `--scope`, `--service`, `--scope-id`, `--tenant-id`.

Platform scope-path shape: `/tenant/<TENANT_ID>/<SERVICE_OR_FOLDER>/project/<PROJECT_ID>` — e.g. `/tenant/aaa.../Reinfer/project/bbb...`.

## Workflow: Create a Single Assignment

1. **Resolve and echo the principal id** following the [Echo-before-mutate protocol](#echo-before-mutate-protocol) above. Do not skip — the assignment endpoint takes a raw UUID and will happily grant the role to the wrong identity if the lookup is wrong.
2. Resolve role id:
   ```bash
   uip admin authorization roles list --filter "<ROLE_NAME>" --output json
   ```
3. **Fetch the role and validate its service binding** per [Validate Role's Owning Service vs. Assignment Scope-Path](#validate-roles-owning-service-vs-assignment-scope-path) — extract `ownerServiceName` + `scopeType`, derive the expected scope-path, and confirm the intended assignment matches. Echo `Role: <name> — ownerServiceName: <X> (scopeType: <Y>)` before the create call.
4. Create inline. Pick the shape that matches the role's `scopeType`:

   **Organization / Tenant / TenantGlobal roles** — scope path auto-fills:
   ```bash
   uip admin authorization roles assignments create \
     --role-id <ROLE_ID> \
     --identity-id <PRINCIPAL_ID> \
     --identity-type User --output json
   ```

   **Tenant role on a non-login tenant**:
   ```bash
   uip admin authorization roles assignments create \
     --role-id <ROLE_ID> \
     --identity-id <PRINCIPAL_ID> \
     --identity-type User \
     --tenant-id <TENANT_ID> --output json
   ```

   **Project / Folder / App role — structured form**:
   ```bash
   uip admin authorization roles assignments create \
     --role-id <ROLE_ID> \
     --identity-id <GROUP_ID> \
     --identity-type Group \
     --scope Project \
     --service reinfer \
     --scope-id <PROJECT_ID> --output json
   ```

   **Project / Folder / App role — verbatim path** (advanced):
   ```bash
   uip admin authorization roles assignments create \
     --role-id <ROLE_ID> \
     --identity-id <GROUP_ID> \
     --identity-type Group \
     --scope-path "/tenant/<TID>/Reinfer/project/<PID>" --output json
   ```

## Workflow: Create Assignments in Batch

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

**The bulk endpoint is atomic** — partial failure rolls back the whole batch.

## Workflow: Delete Assignments in Batch

`assignment-ids.json` is a JSON array of UUID strings:

```json
["0fae98e1-0f2e-4f8d-bdab-7ce1cf475676", "1aab33cf-..."]
```

```bash
uip admin authorization roles assignments delete --file ./assignment-ids.json --output json
```

**Idempotency caveat:** the bulk endpoint silently no-ops on unknown / already-deleted ids and still returns Success. To confirm a deletion took effect, list before and after.

Discover assignment ids via `roles assignments list`.

## Pagination & Filter Caveats

- Server caps `--limit` at 10 assignment groups per page.
- With `--scope Folder|Project|App --scope-id`, results are filtered client-side after the page is fetched. Post-filter count can be smaller than `--limit` even when more matches exist on later pages. Use `--scope-path` for strict server-side pagination math.
- When client-side filtering is active, `totalCount` reflects the post-filter group count, not the org-wide total.
- `--scope TenantGlobal` is **not valid on list** (only on create). Use `--scope Tenant` to surface tenant-scope assignments; the role's TenantGlobal vs Tenant binding is recorded on the role itself.
- `--include-inherited` walks up the scope tree (Org → Tenant → sub-scope). Default is **direct only** (`noInheritance=true`) — pass this flag when the question is "what does this principal effectively have here, including inherited grants?".

## Listing Service-Managed and Platform Services

`roles assignments list --service <svc>` works for every service — including service-managed (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`) and platform-level (`authz`, `oms`, `platform`, `identity`, `licensing`). The endpoint may return `403 Forbidden` when the caller lacks the service's read permission, but the CLI does **not** filter these services client-side.

Authoring (`assignments create` with `--service <svc>`) **is** rejected for those services. Use `--scope-path` to bypass the registry check when you need to assign roles against a service the registry won't accept — but only do so if you already have the role's scope path from another source.
