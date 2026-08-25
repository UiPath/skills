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

### `--service` serviceNames and How to Re-Derive Them

`--service <NAME>` is right when the caller names the service ("which permissions does Orchestrator contribute?"). It is wrong for locating a permission whose owning service you do not know — use [Find the Permission Governing an Action](#workflow-find-the-permission-governing-an-action) instead.

The value `--service` takes is a **`serviceName`** — the API filter this flag sets, equal to the catalog `Namespace` lowercased and to `lowercase(OwnerServiceName)` from `roles list`. All 22 (verified against `uip` 1.201.0):

```
apps  audit  authz  automationops  casemanagement  communicationsmining  cx
dataservice  documentunderstanding  governedinference  identity  insights
licensing  oms  orchestrator  platform  processmining  reinfer  relay  studio
taskmining  testmanager
```

`centralizedaccess` is the one namespace with **no** usable `serviceName`. `CENTRALIZEDACCESS` permissions (the platform Administration page) are reachable only via `--scope Tenant` or an unfiltered list.

Derive the `serviceName` from `Namespace` or `OwnerServiceName`, never from `ServiceDisplayName`: `reinfer` works and `ixp` does not (`REINFER` / `Reinfer` displays as "IXP"); `casemanagement` works and `maestro` does not (displays as "Maestro").

#### Re-derive the List When a `serviceName` Is Rejected

Never guess a replacement `serviceName`, and never trust the `Known services:` roster printed by `check-access --help` — it is a stale 18-entry mirror that omits `audit`, `communicationsmining`, `cx`, `governedinference`, and `relay`. Ask the catalog:

```bash
uip admin authorization permissions list --output plain --output-filter "[].Namespace" \
  | tr '[:upper:]' '[:lower:]' | sort -u | grep -v '^centralizedaccess$'
```

`--output plain` emits one bare value per line, so this needs no `jq` and the ~210 KB catalog never reaches the transcript. Run it, pick the real `serviceName`, retry the original command.

## Cross-Cutting `authz` Permissions

`AUTHZ` holds 14 permissions: 10 at `ScopeType: ANY` — the only `ANY` rows in the whole catalog — plus 4 at `ORGANIZATION`. `ANY` matches every scope filter, so **every** `--service` slice returns those 10 alongside the service's own rows: `--service studio` yields `STUDIO` + `AUTHZ`, `--service identity` yields `IDENTITY` + `AUTHZ`. `--service authz` adds the 4 `ORGANIZATION` rows.

A slice is a **role-shape slice**, never a namespace filter, and never returns another namespace's rows. Two consequences:

1. **A slice returning only those 10 `AUTHZ` rows means the `--service` / `--scope` pair matched nothing of that service** — e.g. `--service apps --scope Project`. That floor, not `Data: []`, is the "wrong slice" signal.
2. **A valid `serviceName` at the wrong scope hides real permissions.** `--service documentunderstanding` returns 17 rows at its inferred `Tenant` scope; `--scope Project` returns 49. Never rule a permission out from one slice — drop `--service` and re-query.

## Workflow: Find the Permission Governing an Action

Use this when diagnosing a 403 or mapping a UI surface ("the Administration page", "the Studio settings tab") to its permission name. Search the **whole** catalog — do not pre-filter by `--service`:

```bash
uip admin authorization permissions list --output json \
  --output-filter "[?contains(Name, 'ADMINISTRATION')]"
```

```json
{ "Name": "CENTRALIZEDACCESS.ADMINISTRATIONPAGE.VIEW", "Namespace": "CENTRALIZEDACCESS",
  "ResourceType": "AdministrationPage", "ResourceAction": "View",
  "Description": "View the administration page", "ScopeType": "TENANT" }
```

Rules:

1. **When searching, always filter.** An unfiltered list is ~500 records / ~210 KB of JSON — past most agents' tool-output limit, so it truncates and the record you need can be present but unread. Never conclude "not found" from a truncated list. (Filtering is for *finding* one permission. When the goal is to hand over the whole catalog, or one named service's slice, list it unfiltered or with `--service` and save it complete — see [Find Permission Names for Role Authoring](#workflow-find-permission-names-for-role-authoring).)
2. **`--output-filter` JMESPath `contains` is case-sensitive.** `Name` is UPPERCASE; `Description`, `ResourceType`, and `ResourceGroup` are sentence/Pascal case. `contains(Description, 'Administration')` returns `[]` while `contains(Description, 'administration')` matches.
3. Search `Name` on an UPPERCASE keyword first, then widen to `Description` in lowercase:
   ```bash
   uip admin authorization permissions list --output json \
     --output-filter "[?contains(Name, 'ADMIN') || contains(Description, 'admin')]"
   ```
4. Narrow by role shape with `--scope`, never a guessed `--service`. Scope matters: `--scope Tenant` surfaces the Administration page permission, `--scope Organization` does not — so try the unfiltered catalog before ruling a permission out.
5. Read `ScopeType` off the hit — it dictates the role scope needed to grant it (`TENANT` → a `Tenant`- or `TenantGlobal`-shape role). See [role-management.md](role-management.md).

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
