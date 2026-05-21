# Grant Permission(s) to a Principal

Workflow for the ad-hoc **"grant me X"** / **"give <PRINCIPAL> permissions Y, Z"** request — a shortcut over the full Create-Role + Create-Assignment pair, optimized for the common case where the user names *permissions*, not a role shape.

For per-command flag tables and output codes, see [authorization-commands.md](authorization-commands.md). For shared role-shape concepts (Centralized Access, service-inference rules, scope modes), see [role-management.md](role-management.md).

## When to Use This Workflow

The user names **one or more permissions** without naming a role or a scope. Examples:

- *"grant me DOCUMENTUNDERSTANDING.PROJECTS.READ"*
- *"give alice DU projects read and update"*
- *"what's the minimal grant for licensing reads?"*

If the user names a **role shape first** (e.g., *"create a tenant role for DU"*, *"make a custom role with DU permissions"*), use [role-management.md — Workflow: Create a Custom Role](role-management.md#workflow-create-a-custom-role) instead — those Step 1a-1d substeps cover the role-first entry path.

> **Sibling workflow.** [Step 1b of Workflow: Create a Custom Role](role-management.md#step-1b--hoist-check-prefer-the-umbrella-when-permissions-overlap) is the binary (service vs. umbrella) form of the same scope-selection problem this workflow solves with a full N-scope intersection (Steps G2-G3). Keep them in sync if either changes.

> **Never skip the scope menu.** The same permission name (e.g., `DOCUMENTUNDERSTANDING.PROJECTS.UPDATE`) almost always appears in *both* the service catalog *and* the Tenant / TenantGlobal umbrella catalogs. Defaulting to `--service <svc>` silently locks the role to one service and loses the multi-service reuse the umbrella offers. Always probe every applicable scope and let the user pick.

## Step G1 — Identify the permission(s)

Resolve the user's wording to one or more concrete permission `name` values (e.g., "DU projects update" → `DOCUMENTUNDERSTANDING.PROJECTS.UPDATE`; "DU projects read and update" → `[…PROJECTS.READ, …PROJECTS.UPDATE]`). If any token is ambiguous (no exact match), grep the catalog:

```bash
uip admin authorization permissions list --output json \
  --output-filter "Data[?contains(name, '<TOKEN>')].{name:name,resourceType:resourceType,scopeType:scopeType}"
```

If multiple candidates remain for any token, render a numbered Markdown menu and stop until disambiguated. End of this step: a confirmed list of one or more permission `name` strings.

## Step G2 — Probe which scopes admit each permission

Always run the Tenant and TenantGlobal probes; gate the other two on the permission set. The CLI tells you which scopes each permission is valid in:

| Probe | Run when |
|---|---|
| `permissions list --scope Tenant` | Always |
| `permissions list --scope TenantGlobal` | Always |
| `permissions list --service <SERVICE>` | Every selected permission shares the same service prefix (one probe per distinct prefix) |
| `permissions list --scope Organization` | Any selected permission has an org-scope service prefix (e.g., `APPS.*`, `IDENTITY.*`) |

```bash
uip admin authorization permissions list --scope Tenant --output json > tenant.json
uip admin authorization permissions list --scope TenantGlobal --output json > tg.json
uip admin authorization permissions list --service <SERVICE> --output json > svc-<SERVICE>.json    # conditional
uip admin authorization permissions list --scope Organization --output json > org.json            # conditional
```

Membership rule: a permission is "valid in scope X" iff its `name` appears in the catalog returned for that scope. Many tenant-services share the same catalog between `--scope Tenant` and `--scope TenantGlobal` — treat them as two distinct menu options.

## Step G2.5 — Compute the intersection of valid scopes/services across all selected permissions

A role can hold a permission only if **every** permission in the set is valid at that role shape. Build the intersection across **five** candidate shapes — four umbrella scopes (Tenant, TenantGlobal, Organization, Project) **plus** the Service shape (`--service <SERVICE>`, scope inferred). The Service shape is always a row in the matrix when every selected permission shares one service prefix — never drop it silently just because an umbrella also admits the perm.

1. For each candidate permission, record the set of shapes where it appears: e.g., `DOCUMENTUNDERSTANDING.PROJECTS.UPDATE = {Tenant, TenantGlobal, Service:documentunderstanding}`.
2. **Intersect** the shape-sets across all candidates. The result is the set of role shapes the role can take.

Branch on the intersection:

| Intersection | Action |
|--------------|--------|
| **Empty** (no shape holds all candidates) | The permissions cannot live on one role. Surface the per-permission scope matrix to the user and offer: (a) split into multiple roles by scope group, (b) drop the outliers, (c) reconsider the set. Do not silently downshift to a single role that omits permissions. |
| **One shape** | Skip the menu — proceed to Step G4 with that shape. State the resolution in the summary. |
| **≥2 shapes** | Render the matrix and menu in Step G3. |

> **Project-scope-only permissions** (e.g., `DOCUMENTUNDERSTANDING.DOCUMENTTYPE.*`) have **no umbrella** — they appear *only* in `permissions list --scope Project --service <svc>`. If every candidate is Project-scope and they share the same service, the intersection is `{Project:<service>}`; skip the menu and use `--scope Project --service <svc>`. If the set mixes Project with Tenant/Org, the intersection is empty — apply the split rule above.

## Step G3 — Render the intersection matrix and scope menu (Tenant Recommended when present)

When the intersection has ≥2 shapes, render **two artifacts**: a presence matrix (so the user sees why each option is offered) followed by a numbered menu (so the user replies with a digit). Mark **Tenant** as Recommended when present. Show only shapes that survived the intersection — never list an option the role can't take.

**Decide which rows to render before drafting either artifact:**

| Row in `Scope/Service` column | Owning service for the created role | Render when |
|---|---|---|
| Tenant | `CentralizedAccess` | Intersection includes `Tenant`. Mark **Recommended**. |
| TenantGlobal | `CentralizedAccess` | Intersection includes `TenantGlobal`. |
| Organization | `CentralizedAccess` | Intersection includes `Organization` (i.e., every selected permission has an org-scope service prefix). |
| Service | `<SERVICE>` (e.g., `DocumentUnderstanding`) | Intersection includes the service catalog AND every selected permission shares one service prefix. Omit when permissions span multiple services or are cross-cutting (e.g., `AUTHZ.*`). |
| Project | `<SERVICE>` | Intersection is `{Project:<service>}` only — handled by the project-only branch in Step G2.5; usually not shown alongside umbrella rows. |

> **Owning Service** is the value `roles get` will return as `ownerServiceName` after creation — umbrella scopes (no `--service`) resolve to `CentralizedAccess`; a service-shape role resolves to the named service. See [role-management.md — Step 6](role-management.md#step-6--summarize-highlight-the-resolved-service).

**Artifact 1 — Intersection matrix.** First column is `Scope/Service`; second column is `Owning Service`; third column is presence (✅ for shapes in the intersection, ❌ for shapes that were probed but excluded). Always include the **Service** row when every selected permission shares one service prefix — its absence was the gap that motivated this column layout. Example for `DOCUMENTUNDERSTANDING.PROJECTS.UPDATE` (single perm, single service):

```
| Scope/Service | Owning Service        | Perm present? |
|---------------|-----------------------|---------------|
| Tenant        | CentralizedAccess     | ✅            |
| TenantGlobal  | CentralizedAccess     | ✅            |
| Service       | DocumentUnderstanding | ✅            |
| Organization  | CentralizedAccess     | ❌            |
| Project       | DocumentUnderstanding | ❌            |
```

**Artifact 2 — Numbered menu** built from the ✅ rows above, renumbered from `1`:

```
`<PERMISSION_NAME_1>` (+ N more) are valid in multiple role shapes. Pick:

1. **Tenant** (Recommended) — multi-service role bound to one tenant. Owning service: `CentralizedAccess`. Built with `--scope Tenant` and no `--service`. Reusable across every tenant-service in this tenant.
2. TenantGlobal — multi-service template visible/assignable in every tenant of the org. Owning service: `CentralizedAccess`. Built with `--scope TenantGlobal` and no `--service`.
3. Organization — multi-service org-scope role. Owning service: `CentralizedAccess`. Built with `--scope Organization` and no `--service`.
4. Service — bound to `<SERVICE>` only. Owning service: `<SERVICE>` (e.g., `DocumentUnderstanding`). Built with `--service <SERVICE>` (scope inferred).

Reply with the digit of your choice.
```

**Why Tenant is the default recommendation:** the Tenant-shape role can bundle additional tenant-scope permissions from any other service later (`LICENSING.*`, `IDENTITY.*`, etc.) without re-authoring; the service-shape role cannot. The Service option is still listed (with its `Owning Service` made explicit) so the user can deliberately pick strict service isolation when that's what they want.

## Step G4 — Map the pick to the create-call shape

| Pick | `roles create` flags |
|------|----------------------|
| Tenant | `--scope Tenant` (no `--service`; `--tenant-id` defaults to login) |
| TenantGlobal | `--scope TenantGlobal` (no `--service`) |
| Organization | `--scope Organization` (no `--service`) |
| Service | `--service <SERVICE>` (no `--scope`; registry infers) |
| Project | `--scope Project --service <SERVICE>` |

Author `actions.json` as a JSON array containing **every** permission `name` confirmed in Step G1 — not just one. Then run [Steps 2-5 of Workflow: Create a Custom Role](role-management.md#step-2--suggest-a-role-name) (name suggestion, action-file authoring, create, verify). After the role exists, run [Workflow: Create a Single Assignment](role-assignment-management.md#workflow-create-a-single-assignment) — including the [Echo-before-mutate protocol](role-assignment-management.md#echo-before-mutate-protocol) for the principal.

## Step G5 — Summarize: state the resolved scope, service, and full permission list

In the post-create / post-assign summary, include:

- The scope path the assignment landed on.
- The resolved `--service` value (or "no `--service` — multi-service <scope> role" when omitted).
- The **full list of permissions** in the role — not just the one the user named first. This matters when the role bundles several permissions; silently omitting some from the summary hides the actual grant scope.

Same rule as [Step 6 of Workflow: Create a Custom Role](role-management.md#step-6--summarize-highlight-the-resolved-service).
