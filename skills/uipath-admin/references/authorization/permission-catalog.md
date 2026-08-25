# Permission Catalog

Conceptual guide for the read-only catalog at `uip admin authorization permissions`. For per-command flag tables, output codes, and single-command examples, see [authorization-commands.md](authorization-commands.md).

## Concept

The catalog is the master list of permission definitions. Custom roles reference permissions by `name` (the dotted string, such as `STUDIO.X.Y`); see [role-management.md — Workflow: Create a Custom Role](role-management.md#workflow-create-a-custom-role).

| Field | Example | Used for |
|-------|---------|----------|
| `id` | UUID | Internal; not required for role authoring |
| `name` | `IDENTITY.GROUP.UPDATE` | **Value in `roles create --file ./actions.json`** |
| `namespace` | `IDENTITY` | Grouping / display |
| `serviceDisplayName` | `Identity Service` | Grouping / display |
| `resourceType` | `Group` | Grouping / display |
| `resourceAction` | `Update` | Grouping / display |
| `resourceGroup` | `Identity` | Grouping / display |
| `scopeType` | `ORGANIZATION` / `TENANT` / `PROJECT` / `ANY` | Determines the role-scope mode |

> The `--file` payload for `roles create`/`roles update` is a **JSON array of permission `name` strings**, not UUIDs. The CLI resolves names to ids server-side.

## Scope Behavior

Each service registers permissions at a specific scope:

- Studio registers at `Tenant`; `--service studio` therefore infers `Tenant`.
- Apps registers at `Organization`.
- Document Understanding registers Project-shape permissions; query them with `--scope Project --service documentunderstanding`.

`--scope <TYPE>` may surface or hide entries according to service registration.

## `--service` Infers Scope

With `--service <NAME>` and no `--scope`, `permissions list` consults the service registry and applies the inferred scope. Override it by passing both flags, as required for Project-shape services such as Document Understanding and Reinfer.

```bash
uip admin authorization permissions list --service studio --output json
uip admin authorization permissions list --service documentunderstanding --scope Project --output json
```

### `--service` serviceNames and How to Re-Derive Them

Use `--service <NAME>` when the caller names the service. When the owning service is unknown, use [Find the Permission Governing an Action](#workflow-find-the-permission-governing-an-action).

`--service` takes a **`serviceName`**: the API filter equal to catalog `Namespace` lowercased and to `lowercase(OwnerServiceName)` from `roles list`. All 22, verified against `uip` 1.201.0:

```
apps  audit  authz  automationops  casemanagement  communicationsmining  cx
dataservice  documentunderstanding  governedinference  identity  insights
licensing  oms  orchestrator  platform  processmining  reinfer  relay  studio
taskmining  testmanager
```

`centralizedaccess` is the only namespace without a usable `serviceName`. Reach `CENTRALIZEDACCESS` permissions, including the platform Administration page, only with `--scope Tenant` or an unfiltered list.

Derive `serviceName` from `Namespace` or `OwnerServiceName`, never `ServiceDisplayName`: `reinfer` works and `ixp` does not (`REINFER` / `Reinfer` displays as “IXP”); `casemanagement` works and `maestro` does not (displays as “Maestro”).

#### Re-derive the List When a `serviceName` Is Rejected

Never guess a replacement `serviceName`, and never trust the `Known services:` roster from `check-access --help`; it is a stale 18-entry mirror omitting `audit`, `communicationsmining`, `cx`, `governedinference`, and `relay`. Run the catalog query, choose a real `serviceName`, and retry the original command:

```bash
uip admin authorization permissions list --output plain --output-filter "[].Namespace" \
  | tr '[:upper:]' '[:lower:]' | sort -u | grep -v '^centralizedaccess$'
```

`--output plain` emits one bare value per line, so no `jq` is needed and the approximately 210 KB catalog does not reach the transcript.

## Cross-Cutting `authz` Permissions

`AUTHZ` has 14 permissions: 10 at `ScopeType: ANY`—the only `ANY` rows in the catalog—and 4 at `ORGANIZATION`. `ANY` matches every scope filter, so every `--service` slice includes those 10 alongside that service's rows: `--service studio` yields `STUDIO` + `AUTHZ`; `--service identity` yields `IDENTITY` + `AUTHZ`; `--service authz` adds the 4 `ORGANIZATION` rows.

A slice is a **role-shape slice**, not a namespace filter, and never returns another namespace's rows:

1. A slice containing only the 10 `AUTHZ` rows means the `--service` / `--scope` pair matched none of that service—for example, `--service apps --scope Project`. This floor, not `Data: []`, signals the wrong slice.
2. A valid `serviceName` at the wrong scope hides real permissions. `--service documentunderstanding` returns 17 rows at its inferred `Tenant` scope and 49 at `--scope Project`. Never rule out a permission from one slice; remove `--service` and re-query.

## Workflow: Find the Permission Governing an Action

Use this for a 403 or to map a UI surface, such as an Administration page or Studio settings tab, to its permission name. Search the **whole** catalog; do not pre-filter by `--service`. Run:

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

1. **Always filter when searching.** An unfiltered list is approximately 500 records / 210 KB of JSON and may exceed tool-output limits, so truncation can hide the needed record. Never conclude “not found” from truncated output. For handing over the whole catalog or a named service's complete slice, list unfiltered or with `--service` and save it complete; see [Find Permission Names for Role Authoring](#workflow-find-permission-names-for-role-authoring).
2. **`--output-filter` JMESPath `contains` is case-sensitive.** `Name` is UPPERCASE; `Description`, `ResourceType`, and `ResourceGroup` use sentence/Pascal case. `contains(Description, 'Administration')` returns `[]`; `contains(Description, 'administration')` matches.
3. Search `Name` with an UPPERCASE keyword first, then widen to lowercase `Description`. Run:
   ```bash
   uip admin authorization permissions list --output json \
     --output-filter "[?contains(Name, 'ADMIN') || contains(Description, 'admin')]"
   ```
4. Narrow by role shape with `--scope`, never with a guessed `--service`. Scope matters: `--scope Tenant` surfaces the Administration page permission, while `--scope Organization` does not. Try the unfiltered catalog before ruling out a permission.
5. Read `ScopeType` from the hit; it determines the role scope needed to grant it (`TENANT` → a `Tenant`- or `TenantGlobal`-shape role). See [role-management.md](role-management.md).

## Workflow: Find Permission Names for Role Authoring

To build a custom role actions file:

1. List candidate permissions for the target service. Run:
   ```bash
   uip admin authorization permissions list --service <SERVICE> --output json
   ```
2. Extract `name` values for the actions the role should grant, such as `STUDIO.X.Y` or `IDENTITY.GROUP.READ`.
3. Write a flat string array to `actions.json`:
   ```json
   ["STUDIO.X.Y", "STUDIO.A.B", "IDENTITY.GROUP.READ"]
   ```
4. Pass it with `--file ./actions.json` to `roles create` or `roles update`. See [role-management.md](role-management.md).

For interactive selection, present one numbered table grouped by `serviceDisplayName`, with columns `# | Service | Permission | Scope | Description`; see [role-management.md — Step 3](role-management.md#step-3--present-permissions-as-a-numbered-menu). Map selected numbers to permission `name` strings internally; never ask the user to copy UUIDs.