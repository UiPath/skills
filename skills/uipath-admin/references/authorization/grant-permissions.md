# Grant Permission(s) to a Principal

Workflow for ad-hoc **"grant me X"** / **"give <PRINCIPAL> permissions Y, Z"** requests: a shortcut over Create-Role + Create-Assignment when the user names permissions rather than a role shape.

For per-command flag tables and output codes, see [authorization-commands.md](authorization-commands.md). For shared role-shape concepts (Centralized Access, service-inference rules, scope modes), see [role-management.md](role-management.md).

## When to Use This Workflow

Use when the user names permissions without naming a role or scope, such as *"grant me DOCUMENTUNDERSTANDING.PROJECTS.READ"*, *"give alice DU projects read and update"*, or *"what's the minimal grant for licensing reads?"* If the user names a role shape first, use [role-management.md — Workflow: Create a Custom Role](role-management.md#workflow-create-a-custom-role); its Step 1a-1d substeps cover the role-first path.

> **Sibling workflow.** [Step 1b of Workflow: Create a Custom Role](role-management.md#step-1b--hoist-check-prefer-the-umbrella-when-permissions-overlap) is the binary service-versus-umbrella form of the scope-selection problem solved here with a full N-scope intersection (Steps G2-G3). Keep them synchronized.
>
> **Never skip the scope menu.** A permission may appear in both service and Tenant / TenantGlobal umbrella catalogs. Do not default to `--service <svc>`; probe every applicable scope and let the user choose.

## Step G1 — Identify the permission(s)

Resolve the wording to exact permission `name` values. If any token is ambiguous or has no exact match, run:

```bash
uip admin authorization permissions list --output json \
  --output-filter "Data[?contains(name, '<TOKEN>')].{name:name,resourceType:resourceType,scopeType:scopeType}"
```

If multiple candidates remain for any token, render a numbered Markdown menu and stop until the user disambiguates. End with one or more confirmed permission `name` strings.

## Step G2 — Probe which scopes admit each permission

Run the Tenant and TenantGlobal probes always; run the other probes conditionally:

| Probe | Run when |
|---|---|
| `permissions list --scope Tenant` | Always |
| `permissions list --scope TenantGlobal` | Always |
| `permissions list --service <SERVICE>` | Every selected permission shares one service prefix; run one per distinct prefix |
| `permissions list --scope Organization` | Any selected permission has an org-scope service prefix, such as `APPS.*` or `IDENTITY.*` |

Run:

```bash
uip admin authorization permissions list --scope Tenant --output json > tenant.json
uip admin authorization permissions list --scope TenantGlobal --output json > tg.json
uip admin authorization permissions list --service <SERVICE> --output json > svc-<SERVICE>.json    # conditional
uip admin authorization permissions list --scope Organization --output json > org.json            # conditional
```

A permission is valid in scope X iff its `name` appears in that scope's catalog. Treat Tenant and TenantGlobal as distinct menu options even when their catalogs match.

## Step G2.5 — Compute the intersection of valid scopes/services

Build each permission's shape-set and intersect the five candidate shapes: Tenant, TenantGlobal, Organization, Project, and Service (`--service <SERVICE>`, scope inferred). Include Service whenever all selected permissions share one service prefix, even if an umbrella also admits them. Record shapes such as `{Tenant, TenantGlobal, Service:documentunderstanding}`; the intersection is the permissible role-shape set.

| Intersection | Action |
|---|---|
| **Empty** | Show the per-permission scope matrix and offer (a) split into multiple roles by scope group, (b) drop outliers, or (c) reconsider the set. Never silently omit permissions or downshift to one incomplete role. |
| **One shape** | Skip the menu, proceed to Step G4, and state the resolved shape. |
| **≥2 shapes** | Render the matrix and menu in Step G3. |

**Project-scope-only permissions** (for example, `DOCUMENTUNDERSTANDING.DOCUMENTTYPE.*`) have no umbrella and appear only in `permissions list --scope Project --service <svc>`. If all candidates are Project-scope and share a service, the intersection is `{Project:<service>}`; skip the menu and use `--scope Project --service <svc>`. If Project is mixed with Tenant or Organization, the intersection is empty and the split rule applies.

## Step G3 — Render the intersection matrix and scope menu

When the intersection has ≥2 shapes, render the presence matrix first, then a numbered menu. Show only intersection survivors; never offer an invalid shape. Mark Tenant **Recommended** when present. Decide rows as follows:

| Row in `Scope/Service` column | Owning service for the created role | Render when |
|---|---|---|
| Tenant | `CentralizedAccess` | Intersection includes `Tenant`; mark **Recommended** |
| TenantGlobal | `CentralizedAccess` | Intersection includes `TenantGlobal` |
| Organization | `CentralizedAccess` | Intersection includes `Organization`, meaning every selected permission has an org-scope service prefix |
| Service | `<SERVICE>` (for example, `DocumentUnderstanding`) | Intersection includes the service catalog and every selected permission shares one service prefix; omit for multi-service or cross-cutting permissions such as `AUTHZ.*` |
| Project | `<SERVICE>` | Intersection is `{Project:<service>}` only; normally handled by the Project-only branch in Step G2.5 rather than shown with umbrella rows |

**Owning Service** is the `ownerServiceName` returned by `roles get`: umbrella scopes without `--service` resolve to `CentralizedAccess`; service-shape roles resolve to the named service. See [role-management.md — Step 6](role-management.md#step-6--summarize-highlight-the-resolved-service).

**Artifact 1 — Intersection matrix.** Use columns `Scope/Service`, `Owning Service`, and `Perm present?`; use ✅ for intersection shapes and ❌ for probed but excluded shapes. Always include the Service row when all selected permissions share one service prefix:

```markdown
| Scope/Service | Owning Service        | Perm present? |
|---------------|-----------------------|---------------|
| Tenant        | CentralizedAccess     | ✅            |
| TenantGlobal  | CentralizedAccess     | ✅            |
| Service       | DocumentUnderstanding | ✅            |
| Organization  | CentralizedAccess     | ❌            |
| Project       | DocumentUnderstanding | ❌            |
```

**Artifact 2 — Numbered menu.** Build it from the ✅ rows and renumber from `1`. Identify the permission(s), explain that they are valid in multiple role shapes, state each shape's binding, owning service, and create flags, and end with “Reply with the digit of your choice.” Use this structure:

```markdown
`<PERMISSION_NAME_1>` (+ N more) are valid in multiple role shapes. Pick:

1. **Tenant** (Recommended) — multi-service role bound to one tenant. Owning service: `CentralizedAccess`. Built with `--scope Tenant` and no `--service`. Reusable across every tenant-service in this tenant.
2. TenantGlobal — multi-service template visible/assignable in every tenant of the org. Owning service: `CentralizedAccess`. Built with `--scope TenantGlobal` and no `--service`.
3. Organization — multi-service org-scope role. Owning service: `CentralizedAccess`. Built with `--scope Organization` and no `--service`.
4. Service — bound to `<SERVICE>` only. Owning service: `<SERVICE>` (e.g., `DocumentUnderstanding`). Built with `--service <SERVICE>` (scope inferred).

Reply with the digit of your choice.
```

Recommend Tenant because it can later bundle tenant-scope permissions from other services (`LICENSING.*`, `IDENTITY.*`, etc.) without re-authoring; still list Service for deliberate isolation.

## Step G4 — Map the pick to the create-call shape

| Pick | `roles create` flags |
|---|---|
| Tenant | `--scope Tenant` (no `--service`; `--tenant-id` defaults to login) |
| TenantGlobal | `--scope TenantGlobal` (no `--service`) |
| Organization | `--scope Organization` (no `--service`) |
| Service | `--service <SERVICE>` (no `--scope`; registry infers) |
| Project | `--scope Project --service <SERVICE>` |

Author `actions.json` as a JSON array containing **every** permission `name` confirmed in Step G1. Then run [Steps 2-5 of Workflow: Create a Custom Role](role-management.md#step-2--suggest-a-role-name): name suggestion, action-file authoring, create, and verify. After the role exists, run [Workflow: Create a Single Assignment](role-assignment-management.md#workflow-create-a-single-assignment), including the [Echo-before-mutate protocol](role-assignment-management.md#echo-before-mutate-protocol) for the principal.

## Step G5 — Summarize: state the resolved scope, service, and full permission list

In the post-create / post-assign summary, include:

- The scope path where the assignment landed.
- The resolved `--service` value, or “no `--service` — multi-service <scope> role” when omitted.
- The **full list of permissions** in the role, not only the first named permission.

Apply the same rule as [Step 6 of Workflow: Create a Custom Role](role-management.md#step-6--summarize-highlight-the-resolved-service).