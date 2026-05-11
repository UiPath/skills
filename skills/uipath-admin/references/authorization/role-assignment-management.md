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

| Principal Type | Source |
|----------------|--------|
| `User` | [user-management.md](../user-management.md) — `uip admin users list --search <NAME>` |
| `Group` | [group-management.md](../group-management.md) — `uip admin groups list` |
| `Robot` | [robot-account-management.md](../robot-account-management.md) — `uip admin robot-accounts list` |
| `ExternalApplication` | [external-app-management.md](../external-app-management.md) — `uip admin external-apps list` |

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

1. Resolve principal id (see "Resolving Principal IDs").
2. Resolve role id:
   ```bash
   uip admin authorization roles list --filter "<ROLE_NAME>" --output json
   ```
3. Create inline. Pick the shape that matches the role's `scopeType`:

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
