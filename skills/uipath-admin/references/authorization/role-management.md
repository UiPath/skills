# Role Management

Multi-step workflows for managing custom role definitions via `uip admin authorization roles`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Services That Manage Their Own Roles

The Authorization service does NOT own roles for these services — `roles list` will not return them and `roles create` rejects them:

- **Service-managed:** `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager` — these services manage roles server-side. Use that service's CLI (e.g., `uip or roles create` for Orchestrator).
- **Platform-level:** `authz`, `oms`, `platform`, `identity`, `licensing`.

To see effective roles for a principal across all services (including the service-managed ones above), use [check-access.md](check-access.md).

## Role Shape (Scope) Modes

`roles create --scope <type>` accepts:

| Mode | When | `--service` semantics | `--tenant-id` semantics |
|------|------|----------------------|--------------------------|
| `Organization` | Role grants org-wide access (typical for `apps`, `studio`, `identity` permissions) | Optional. Used alone, infers `Organization` from the registry | Ignored |
| `TenantGlobal` | Reusable template — visible/assignable inside every tenant in the org | Optional | Ignored |
| `Tenant` | Bound to one specific tenant — only assignable there | Optional. Used alone with a tenant-shape service, infers `Tenant` | Defaults to login tenant; pass explicitly for a non-login tenant |
| `Project` | Project-shape role (Document Understanding, Reinfer) | **Required** | Defaults to login tenant |

**`Folder` is not a valid `--scope` for `roles create/update`.** Folder-level scoping is expressed on the *assignment* (see [role-assignment-management.md](role-assignment-management.md)).

> `--service` infers the scope from the service registry when `--scope` is omitted. Example: `roles create --service studio --name "..."` resolves to `Tenant`. Combine `--service` with `--scope` only to override the registry default (e.g., `--service documentunderstanding --scope Project`).

## Workflow: Create a Custom Role

This is an interactive flow. Do NOT prompt the user with empty `<ROLE_NAME>` / `<PERMISSION_NAMES>` placeholders. Propose a name and a numbered permission menu, then confirm.

### Step 1 — Gather intent and pick a scope mode

Ask the user (free-form) what the role is for: target service(s) and the kind of access (read-only, operator, admin, etc.).

#### Step 1a — Service-bound role (the common case)

If the role wraps **one** service's permissions, do not ask the user about org vs tenant scope. Probe the catalog:

```bash
uip admin authorization permissions list --service <SERVICE> --output json
```

The catalog response includes `scopeType` per record. Use it to pick the mode for Step 4:

| Records' `scopeType` | Service shape | Use this for the rest of the flow |
|----------------------|---------------|-----------------------------------|
| All `ORGANIZATION` (e.g., `apps`, `studio`, `identity`) | Org-level service | **Organization** mode |
| All `TENANT` (e.g., `documentunderstanding`, most Orchestrator-adjacent) | Tenant-level service | **Tenant** mode — then ask: bound to current tenant vs `TenantGlobal` template |
| All `PROJECT` | Project-shape service | **Project** mode (requires `--service`) |
| Mixed | Multi-scope service | Ask the user which scope to target; only show permissions for the chosen scope |

> **Casing quirk** — the *response field* `scopeType` returns ALL CAPS (`ORGANIZATION`, `TENANT`, `PROJECT`, `ANY`). The matching `--scope` *flag value* uses PascalCase (`Organization`, `Tenant`, `Project`, `TenantGlobal`). Map response → flag when constructing the create call: `ORGANIZATION` → `--scope Organization`, `TENANT` → `--scope Tenant` (or `TenantGlobal`), `PROJECT` → `--scope Project`.

#### Step 1b — Tenant-bound vs TenantGlobal

When Step 1a returns Tenant-shape permissions, follow up: should the role be **bound to a single tenant** (`--scope Tenant --tenant-id <UUID>`) or **available across every tenant** (`--scope TenantGlobal`)?

- **Tenant** = bound to one tenant UUID. Assignable only inside that tenant.
- **TenantGlobal** = reusable template. Visible/assignable in every tenant.

> Resolving the current tenant UUID: `uip login status --output json` gives the tenant *name*; map it to a UUID with `uip admin tenants list --filter <name> --output json`.

### Step 2 — Suggest a role name

Propose **one** name derived from the intent. Pattern: `<Service><Scope>-<Capability>` in PascalCase or kebab-case, e.g. `OrchestratorTenant-ReadOnly`, `IdentityOrg-GroupAdmin`. Check for collisions before presenting:

```bash
uip admin authorization roles list --role-type Custom --filter "<SUGGESTED_NAME>" --output json
```

If the filter returns a match, append a numeric suffix (`-2`, `-3`) and re-check until unique. Present the final suggestion to the user and let them accept or override with a single reply.

### Step 3 — Present permissions as a numbered menu

Pull the catalog for each service named in Step 1, using the `--scope` from Step 1's mode:

```bash
# Organization mode
uip admin authorization permissions list --service <SERVICE> --scope Organization --output json

# Tenant (or TenantGlobal — same catalog)
uip admin authorization permissions list --service <SERVICE> --scope Tenant --output json

# Project mode (service required)
uip admin authorization permissions list --service <SERVICE> --scope Project --output json
```

Render **one Markdown table grouped by `serviceDisplayName`**, with a global running number so the user can reply with digits (`"1, 4, 7-9"`). Columns:

| # | Service | Permission | Scope | Description |
|---|---------|------------|-------|-------------|

- `#` — global 1-based index across all rows.
- `Service` — `serviceDisplayName`. Repeat the value only on the first row of each group; leave blank on continuation rows so groups are visually distinct.
- `Permission` — the `name` field (e.g., `IDENTITY.GROUP.UPDATE`). **This is the string that goes into `actions.json`.**
- `Scope` — `scopeType` from the record.
- `Description` — the record's `description` field verbatim. If missing, fall back to `<resourceAction> <resourceType>`.

Sort rows by `serviceDisplayName`, then `resourceType`, then `resourceAction`. Keep the table to one screen where possible — if a single service exceeds ~30 entries, ask the user which `resourceType`(s) to narrow to before rendering.

After the table, prompt: *"Reply with the numbers to include (e.g. `1, 3, 5-7`)."* Map the selection back to permission **`name` strings** internally — never ask the user to copy UUIDs.

### Step 4 — Author the actions file (`actions.json`)

The `--file` for `roles create` is a **flat JSON array of permission `name` strings** — not a full role body. The CLI assembles the role envelope from `--name` / `--description` / `--service` / `--scope` / `--tenant-id`; you only supply the action set.

```json
["STUDIO.X.Y", "STUDIO.A.B", "IDENTITY.GROUP.READ"]
```

### Step 5 — Create and verify

Pick the inline shape that matches Step 1's mode:

```bash
# Organization
uip admin authorization roles create \
  --scope Organization \
  --name "<CONFIRMED_NAME>" \
  --description "<DESCRIPTION>" \
  --file ./actions.json --output json

# Tenant — bound to a specific tenant
uip admin authorization roles create \
  --scope Tenant \
  --tenant-id <TENANT_ID> \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# TenantGlobal — reusable template across every tenant
uip admin authorization roles create \
  --scope TenantGlobal \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Service-inferred — let the registry pick scope (studio → Tenant)
uip admin authorization roles create \
  --service studio \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Project — service required
uip admin authorization roles create \
  --scope Project \
  --service documentunderstanding \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json
```

Verify:

```bash
uip admin authorization roles get <NEW_ROLE_ID> --output json
```

The endpoint is a PUT-style upsert. The CLI carries the role identity in the positional `<ID>` (on update) or generates one (on create); you never put `id` in the actions file.

## Workflow: Update a Custom Role

The endpoint is the same upsert. The CLI assembles the body from the positional `<ID>` + inline flags + `--file` actions array. Re-fetch before editing — otherwise inline flags overwrite fields you didn't intend to change.

1. Fetch the current role to see `name`, `description`, `scopeType`, `tenantId`, and the current actions:
   ```bash
   uip admin authorization roles get <ROLE_ID> --output json
   ```
2. Decide what to change. If you're only changing the action set, regenerate `actions.json` from a fresh `permissions list` query (Step 3 above) and skip the metadata flags:
   ```bash
   uip admin authorization roles update <ROLE_ID> --file ./actions.json --output json
   ```
3. If you're changing metadata too, **pass the metadata flags you want to keep along with the ones you're changing** — the CLI does not merge the current role's fields back in automatically:
   ```bash
   uip admin authorization roles update <ROLE_ID> \
     --scope Tenant \
     --tenant-id <TENANT_ID> \
     --name "<NEW_NAME>" \
     --description "<NEW_DESC>" \
     --file ./actions.json --output json
   ```

## Workflow: Delete a Custom Role

1. Confirm the role is custom:
   ```bash
   uip admin authorization roles get <ROLE_ID> --output json
   ```
   Verify `type` is `Custom`. The CLI also pre-fetches and refuses service-managed / platform-owned roles with a redirect.
2. Confirm with user.
3. Run `roles delete <ROLE_ID>`.
