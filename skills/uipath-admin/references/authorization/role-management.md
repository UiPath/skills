# Role Management

Multi-step workflows for managing custom role definitions via `uip admin authorization roles`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Services That Manage Their Own Roles

Listing always works; authoring is what's blocked.

- **Service-managed:** `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`, `automationops`, `casemanagement`, `processmining`. The Authorization service surfaces their roles in `roles list --service <svc>` and their assignments in `roles assignments list --service <svc>`, but `roles create / update / delete` against these services is rejected. Mutate them via the service's own CLI (e.g., `uip or roles create` for Orchestrator).
- **Platform-level:** `authz`, `oms`, `platform`, `identity`, `licensing`. Same shape — listing works, authoring is rejected.

For *effective* access on a principal (PDP — includes server-side rules not visible via the catalog), use [check-access.md](check-access.md).

## Role Shape (Scope) Modes

`roles create --scope <type>` accepts:

| Mode | When | `--service` semantics | `--tenant-id` semantics |
|------|------|----------------------|--------------------------|
| `Organization` | Role grants org-wide access (typical for `apps`, `studio`, `identity` permissions) | Optional. Used alone, infers `Organization` from the registry. **Omit** for a multi-service org role | Ignored |
| `TenantGlobal` | Reusable template — visible/assignable inside every tenant in the org | Optional. **Omit** for a multi-service template | Ignored |
| `Tenant` | Bound to one specific tenant — only assignable there | Optional. Used alone with a tenant-shape service, infers `Tenant`. **Omit** for a multi-service "Centralized Access" tenant role | Defaults to login tenant; pass explicitly for a non-login tenant |
| `Project` | Project-shape role (Document Understanding, Reinfer) | **Required** | Defaults to login tenant |

**`Folder` is not a valid `--scope` for `roles create/update`.** Folder-level scoping is expressed on the *assignment* (see [role-assignment-management.md](role-assignment-management.md)).

> `--service` infers the scope from the service registry when `--scope` is omitted. Example: `roles create --service studio --name "..."` resolves to `Tenant`. Combine `--service` with `--scope` only to override the registry default (e.g., `--service documentunderstanding --scope Project`).

### Centralized Access — the "no --service" tenant role

When the user asks for a **"tenant role"** or **"create role in Tenant scope"** without naming a specific service, the correct shape is `--scope Tenant` **with no `--service` flag**. This is the multi-service "Centralized Access" tenant role and can carry any `TENANT`-scope permission across services in the catalog.

- **CLI rejects `--service centralizedaccess`** with `'centralizedaccess' is not a valid --service value`. The same rejection applies on `roles list`, `roles assignments list`, and `permissions list`. Drop the flag entirely.
- Same rule for `Organization` and `TenantGlobal`: omit `--service` for the multi-service variant; pass it only when the role wraps one specific service's catalog.
- `Project` is the one exception — `--service` is **required**.

### Service inference — split

| User intent | Resolution |
|-------------|------------|
| Names a service, or asks for a permission only one service registers (e.g., "DU documents delete") | Pass `--service <svc>`. The registry infers `--scope` unless overridden. |
| Says "tenant role" / "tenant scope" / "centralized access" with no service named | **Omit `--service`.** Pass `--scope Tenant` (or `Organization` / `TenantGlobal`) alone. |
| Project-shape service (Document Understanding, Reinfer) | `--scope Project` + `--service <svc>` (required). |

> **Always highlight the resolved service when summarizing a `roles create` call.** Quote the exact `--service <name>` you used, or state "no `--service` — multi-service tenant role" when it was omitted. Never silently swap services or scopes.

## Workflow: Grant Permission(s) to a Principal (shortcut)

When the user names *permissions* without naming a role or scope (*"grant me X"*, *"give alice Y, Z"*), use [grant-permissions.md](grant-permissions.md) — a multi-step intersection-and-menu flow that picks the right role shape across the service catalog and umbrella scopes. This page covers the **role-first** entry path: user names a role shape, then we author the role and assignments.

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

> **Override:** if the user explicitly says "Tenant scope" / "tenant role" / "centralized access" — even when the permission's catalog `scopeType` is `PROJECT` — switch to the **no-`--service`** Tenant path (Step 1d). Do not silently substitute a different permission to satisfy a service-bound shape. Surface the mismatch and let the user choose.

> **Casing quirk** — the *response field* `scopeType` returns ALL CAPS (`ORGANIZATION`, `TENANT`, `PROJECT`, `ANY`). The matching `--scope` *flag value* uses PascalCase (`Organization`, `Tenant`, `Project`, `TenantGlobal`). Map response → flag when constructing the create call: `ORGANIZATION` → `--scope Organization`, `TENANT` → `--scope Tenant` (or `TenantGlobal`), `PROJECT` → `--scope Project`.

#### Step 1b — Hoist check: prefer the umbrella when permissions overlap

> **Sibling workflow.** This is the binary (service vs. umbrella) form of the same scope-selection problem the [Grant Permission(s) shortcut](grant-permissions.md) solves with a full N-scope intersection (Steps G2-G3). Use Step 1b when the user named the role shape first; use the Grant shortcut when the user named permissions only. Keep them in sync if either changes.

**Run this between Step 1a and Step 1c** unless the candidate shape is `Project` (which has no umbrella). When the permissions a user wants are available at **both** the service-bound catalog AND the umbrella scope (`Tenant` / `TenantGlobal` for tenant-services, `Organization` for org-services), the umbrella role is the better default — it can carry permissions from any other service in the same scope, so it's reusable beyond the single service the user originally named.

1. Probe the umbrella catalog at the umbrella scope (no `--service`):
   ```bash
   # Tenant-service candidate (Step 1a returned `TENANT` scopeType)
   uip admin authorization permissions list --scope Tenant --output json > umbrella.json

   # Org-service candidate (Step 1a returned `ORGANIZATION` scopeType)
   uip admin authorization permissions list --scope Organization --output json > umbrella.json
   ```
2. Compare the candidate's permission `name` values (from `permissions list --service <SERVICE>` in Step 1a) against the umbrella's `name` values:
   - **No overlap** — candidate permissions live only in the service catalog. Lock in the service-bound shape (`--service <SERVICE>`); go to Step 1c if the candidate is Tenant-shape, else Step 2.
   - **Full overlap** — every candidate permission also exists in the umbrella. Surface the menu below and let the user pick.
   - **Partial overlap** — some candidate permissions appear in the umbrella, others don't. Stop and show the user the split; do not silently drop the service-only permissions to fit the umbrella, and do not silently expand into umbrella-only permissions.

3. On full overlap, render a numbered next-step menu and **recommend the umbrella** (numbered Markdown list so the user replies with a digit):

   **Tenant-service candidate** (umbrella is Tenant):
   ```
   The permissions you picked are available at both the service level AND the umbrella Tenant scope. The umbrella role can carry permissions from any tenant-service, so it's more reusable. Pick:

   1. **Tenant level** (Recommended) — multi-service role bound to one tenant. Reusable across every tenant-service in this tenant.
   2. Service level — bound to <SERVICE> only. Use when you want strict service isolation.
   3. Tenant Global scope — multi-service template visible in every tenant of the org.

   Reply with 1, 2, or 3.
   ```

   **Org-service candidate** (umbrella is Organization):
   ```
   The permissions you picked are available at both the service level AND the umbrella Organization scope. The umbrella role can carry permissions from any org-service, so it's more reusable. Pick:

   1. **Org level** (Recommended) — multi-service role at organization scope. Reusable across every org-service.
   2. Service level — bound to <SERVICE> only. Use when you want strict service isolation.

   Reply with 1 or 2.
   ```

4. Map the user's pick to the create-call shape:

   | Pick | Create-call shape | Continue at |
   |------|--------------------|--------------|
   | Tenant level | `--scope Tenant` **without** `--service` (`--tenant-id` defaults to login) | Step 2 — Tenant binding is already decided, skip Step 1c |
   | Org level | `--scope Organization` **without** `--service` | Step 2 |
   | Service level | `--service <SERVICE>` (registry infers `--scope`) | Step 1c if Tenant-shape; else Step 2 |
   | Tenant Global scope | `--scope TenantGlobal` **without** `--service` | Step 2 |

> **Project-scope permissions have no umbrella.** `--scope Project` requires `--service` (see the "Centralized Access — the no --service tenant role" section above). Skip Step 1b entirely when Step 1a's `scopeType` is `PROJECT`.

#### Step 1c — Tenant-bound vs TenantGlobal

When Step 1a (or Step 1b's "Service level" pick on a Tenant-shape service) lands on Tenant-shape permissions, follow up: should the role be **bound to a single tenant** (`--scope Tenant --tenant-id <UUID>`) or **available across every tenant** (`--scope TenantGlobal`)?

> Step 1b's "Tenant level" and "Tenant Global scope" picks **bypass** this step — they have already chosen the binding.

- **Tenant** = bound to one tenant UUID. Assignable only inside that tenant.
- **TenantGlobal** = reusable template. Visible/assignable in every tenant.

> Resolving the current tenant UUID: `uip login status --output json` gives the tenant *name*; map it to a UUID with `uip admin tenants list --filter <name> --output json`.

#### Step 1d — Multi-service tenant role ("Centralized Access")

If the user said **"tenant role"** / **"tenant scope"** / **"centralized access"** without naming a service — or pivoted into Tenant scope from a service-bound flow — drop `--service` entirely and probe the multi-service catalog:

```bash
uip admin authorization permissions list --scope Tenant --output json
```

This is the umbrella the UI calls *Centralized Access*. The resulting role can carry any `TENANT`-scope permission across services (Document Understanding `PROJECTS.*`, Licensing, IXP, Authz, etc.). Render the menu in Step 3 from this catalog.

> If the user previously named a single permission that is `PROJECT`-scope only (e.g., `DOCUMENTUNDERSTANDING.DOCUMENTS.DELETE`) and then asks for "Tenant scope", state the mismatch — the permission cannot live on a Tenant-scope role — and offer:
> 1. Closest TENANT-scope analog (e.g., `DOCUMENTUNDERSTANDING.PROJECTS.DELETE`)
> 2. Keep the existing Project-scope role
> 3. A different permission set
>
> Never silently downshift to a similar-looking permission.

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
# Multi-service tenant role ("Centralized Access") — NO --service
uip admin authorization roles create \
  --scope Tenant \
  --tenant-id <TENANT_ID> \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Service-bound tenant role — scope inferred from the service registry
uip admin authorization roles create \
  --service documentunderstanding \
  --tenant-id <TENANT_ID> \
  --name "<CONFIRMED_NAME>" \
  --file ./actions.json --output json

# Organization — multi-service org role (no --service)
uip admin authorization roles create \
  --scope Organization \
  --name "<CONFIRMED_NAME>" \
  --description "<DESCRIPTION>" \
  --file ./actions.json --output json

# TenantGlobal — reusable template across every tenant (no --service)
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

> **Never pass `--service centralizedaccess`** — the CLI rejects it (`'centralizedaccess' is not a valid --service value`). For the Centralized Access umbrella, omit `--service`.

Verify:

```bash
uip admin authorization roles get <NEW_ROLE_ID> --output json
```

The endpoint is a PUT-style upsert. The CLI carries the role identity in the positional `<ID>` (on update) or generates one (on create); you never put `id` in the actions file.

### Step 6 — Summarize: highlight the resolved service

After `roles create` succeeds, your reply to the user MUST quote the resolved service explicitly so the role's shape is unambiguous. Run a `roles get <NEW_ROLE_ID>` and read `ownerServiceName` directly from the response — that is the canonical service binding the platform will use to validate future assignments. Include a row for `Service` in the summary table:

| Source | Render as |
|---|---|
| `ownerServiceName` from `roles get` | `service: <ownerServiceName>` (e.g., `service: DocumentUnderstanding`) |
| `ownerServiceName == "CentralizedAccess"` | `service: CentralizedAccess — multi-service <scope> role` (any assignment scope-path must omit the service segment) |

This field is what [role-assignment-management.md — Validate Role's Owning Service vs. Assignment Scope-Path](role-assignment-management.md#validate-roles-owning-service-vs-assignment-scope-path) checks against on every `assignments create`. Surface it early to avoid surprises later.

Same applies on `roles update`.

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
