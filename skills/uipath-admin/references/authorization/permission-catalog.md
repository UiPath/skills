# Permission Catalog

Conceptual guide for the read-only catalog at `uip admin authorization permissions`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Concept

The catalog is the master list of permission definitions across all services. Permissions are referenced **by `name`** (the dotted string, e.g. `STUDIO.X.Y`) when authoring custom roles — see [role-management.md — Workflow: Create a Custom Role](role-management.md#workflow-create-a-custom-role).

Each permission record:

| Field | Example | Used for |
|-------|---------|----------|
| `id` | UUID | Internal — not required for role authoring |
| `name` | `IDENTITY.GROUP.UPDATE` | **What goes into `roles create --file ./actions.json`** |
| `namespace` | `IDENTITY` | Grouping / display |
| `serviceDisplayName` | `Identity Service` | Grouping / display |
| `resourceType` | `Group` | Grouping / display |
| `resourceAction` | `Update` | Grouping / display |
| `resourceGroup` | `Identity` | Grouping / display |
| `scopeType` | `ORGANIZATION` / `TENANT` / `PROJECT` / `ANY` | Determines which role-scope mode the permission belongs in |

> The `--file` payload for `roles create`/`roles update` is a **JSON array of permission `name` strings**, not UUIDs. The CLI resolves names to ids server-side.

## Scope Behavior

Each service registers its permissions at a specific scope. Examples:

- Studio permissions register at `Tenant` (per the service registry — `--service studio` infers `Tenant`).
- Apps permissions register at `Organization`.
- Document Understanding registers Project-shape permissions (queryable with `--scope Project --service documentunderstanding`).

Passing `--scope <TYPE>` may surface or hide service-specific entries depending on where the service registered.

## `--service` Infers Scope

When you call `permissions list` with `--service <NAME>` and **no `--scope`**, the CLI consults the service registry and applies the inferred scope automatically. To override, pass both `--service` and `--scope` explicitly (used by Project-shape services like Document Understanding and Reinfer).

```bash
uip admin authorization permissions list --service studio --output json
uip admin authorization permissions list --service documentunderstanding --scope Project --output json
```

## Cross-Cutting `authz` Permissions

`authz` permissions appear alongside every service's permissions and are filtered out of `permissions list` by default. Pass `--service authz` to surface them.

## Workflow: Find Permission Names for Role Authoring

To build a custom role's actions file:

1. List candidate permissions for the target service:
   ```bash
   uip admin authorization permissions list --service <SERVICE> --output json
   ```
2. Extract `name` values for the actions the role should grant (e.g. `STUDIO.X.Y`, `IDENTITY.GROUP.READ`).
3. Write them to `actions.json` as a flat string array:
   ```json
   ["STUDIO.X.Y", "STUDIO.A.B", "IDENTITY.GROUP.READ"]
   ```
4. Pass via `--file ./actions.json` to `roles create` or `roles update`. See [role-management.md](role-management.md).

When the user is selecting permissions interactively, present them as a **single numbered table grouped by `serviceDisplayName`** with columns `# | Service | Permission | Scope | Description` — see [role-management.md — Step 3](role-management.md#step-3--present-permissions-as-a-numbered-menu). Map the user's picked numbers to permission `name` strings internally; never ask the user to copy UUIDs.
