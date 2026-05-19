---
name: uipath-admin
description: "UiPath Admin via `uip admin` — Identity Server (users, groups, robot accounts, external OAuth2 apps, secrets), Authorization (custom roles, role assignments, permission catalog, effective-access via check-access PDP), OMS (organization/tenant lifecycle, service provisioning, regions, async operation polling), APMS (IP allowlist, enforcement, bypass rules, lockout safety), Audit (event sources, paginated queries, ZIP exports — login history, compliance dumps, who-did-what-when-where on a resource). For Orchestrator-specific roles/permissions/folders/jobs→uipath-platform. For RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Admin

> **Preview** — Under active development. Command coverage will expand.

Administrative operations on UiPath via `uip admin` — Identity Server (users, groups, robot accounts, external OAuth2 apps), Authorization service (custom roles, role assignments, permission catalog, effective-access lookups), OMS (organization + tenant lifecycle, service provisioning), APMS (IP allowlisting, enforcement, bypass rules), and Audit Service (event sources, event queries, long-term-store ZIP exports).

## When to Use This Skill

### Identity

- **Manage identity users** — list, create, invite, update, delete
- **Manage groups** — CRUD + add/remove members
- **Manage robot accounts** — create, update, delete unattended robot identities
- **Manage external apps** — OAuth2 clients, generate/rotate secrets
- **Onboard human user** — invite, assign to groups
- **Onboard robot account** — create account, assign to groups
- **Identity concepts** — partitions, organizations, OAuth2 scopes
- **Generate Client ID/Secret** — credentials for API or robot authentication

### Authz

- **Manage custom roles** — CRUD on Authorization service role definitions (scope shapes: `Organization`, `TenantGlobal`, `Tenant`, `Project`)
- **Manage role assignments** — assign roles to users/groups/robot accounts at `Organization`, `Tenant`, `TenantGlobal`, `Project`, `Folder`, or `App` scope
- **List permission definitions** — read-only catalog of permissions across services
- **Check effective access** — compute what a principal can actually do at a given scope (Policy Decision Point)

### OMS

- **Inspect / update / soft-delete the current organization** — `uip admin organizations`
- **Manage tenant lifecycle** — create, enable, disable, delete tenants in the caller's org
- **Provision org-level or tenant-level services** — `services list`, `list-available`, `add`, `enable`, `disable`, `remove`
- **Poll async OMS operations** — `organizations`/`tenants` mutations return `operationId`; poll via `organizations operation get <id>`
- **List available regions** — discover provisioning regions before creating an org or tenant

### APMS (IP restriction)

- **Manage IP allowlisting** — add / update / delete CIDR entries that gate inbound access
- **Toggle IP-restriction enforcement** — turn the org-wide allowlist switch on or off (with lockout safety)
- **Manage bypass rules** — URL-pattern exceptions to IP allowlisting
- **Look up the caller's public IP** — sanity check before enabling enforcement

### Audit

- **Query audit events** — list event sources, filter events by source / target / type / user / status / time window at org or tenant scope
- **Export audit events** — chunked ZIP download from the long-term store, per UTC day, with atomic abort on any chunk failure

## Critical Rules

### Cross-cutting

1. **Route Orchestrator-specific roles/permissions to `uip or roles`.** If the user explicitly asks to create, list, or manage **Orchestrator** roles or permissions, redirect to the `uipath-platform` skill and use `uip or roles ...`. The Authorization service in `uip admin authorization` does NOT own Orchestrator's role catalog — it's service-managed. Authz commands here cover only cross-service / platform roles. When in doubt (e.g., the user says only "role" without naming a service), assume `uip admin authorization` and proceed.
2. **Verify login first.** Run `uip login status --output json`. If not logged in: `uip login`.
3. **Organization ID is resolved automatically from login.** CLI reads org ID from active session.
4. **Use `--output json` on all commands.** Parse programmatically. Present results conversationally.
5. **Stop on error (interactive use).** If any command fails, show error to user. Do not retry auth failures — ask user to run `uip login`.

### Identity

6. **Discover before creating.** `list` before `create` to avoid duplicates. Applies to robot accounts, groups, and external apps — not to `users invite`.
7. **Secrets shown only once.** When creating external apps or generating secrets, the secret value appears only in the creation response. Warn user to save immediately.
8. **External apps require scopes at creation.** `--scope` is required. Common scopes: `OR.Folders`, `OR.Assets`, `OR.Queues`, `OR.Jobs`, `OR.Machines`.
9. **Group membership uses user IDs, not usernames.** Resolve IDs via `users list` before `groups members add` or `groups members revoke`.
10. **Confirm before delete.** Always confirm with user before running `delete` on users, groups, robot accounts, or external apps.

### Authz

11. **Built-in roles are read-only.** Only `Custom` roles can be created, updated, or deleted. Verify `type: "Custom"` (PascalCase, matching `--role-type`) before any mutation. The CLI also rejects authoring roles for services that manage their own roles (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`) and platform-level (`authz`, `oms`, `platform`, `identity`, `licensing`) services.
12. **`roles create` / `roles update` are PUT-style upserts.** The CLI assembles the full role body from inline flags (`--name`, `--description`, `--service`, `--scope`, `--tenant-id`) plus `--file ./actions.json` (a JSON array of permission `name` strings). Omitted inline flags overwrite that field on update — always `roles get` first and pass through every field you want to preserve.
13. **`--service` infers scope.** On `roles create/update/list` and `permissions list`, passing `--service <name>` alone resolves `--scope` from the service registry (e.g., `--service studio` → `Tenant`, `--service apps` → `Organization`). Combine `--service` with `--scope` only to override the registry default (e.g., `--service documentunderstanding --scope Project`).
14. **Service-managed roles do not appear in `roles list` or `roles assignments list`.** Services that manage their own roles (`orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager`) are not surfaced via the Authorization service catalog. Use `check-access` to see effective roles for a principal in those services.
15. **Scope vocab differs between roles and assignments.** `roles create --scope` accepts `Organization | TenantGlobal | Tenant | Project` (no `Folder`). `roles assignments create --scope` accepts those plus `Folder | App`. `roles assignments list --scope` excludes `TenantGlobal`. `check-access --scope` accepts `Organization | Tenant | Folder | Project`.

### OMS

16. **Tenant lifecycle and `organizations create/delete` are async.** `organizations create/delete` and `tenants create/update/delete/enable/disable` return `operationId`. Poll via `uip admin organizations operation get <OPERATION_ID>` until terminal status before treating the change as done. `organizations update`, `regions list`, and all `services` reads/mutations are **synchronous** — no polling needed.
17. **`delete` is soft-only.** Neither `organizations delete` nor `tenants delete` exposes a hard-delete flag. Confirm with user; restoration goes through the support flow.
18. **Tenant commands default to the login tenant.** All `tenants get/update/delete/enable/disable` and `tenants services *` commands take `--tenant-id` as optional (defaults to login tenant). Always pass an explicit `<TENANT_ID>` for destructive ops (`delete`, `disable`, `services remove`) to avoid accidentally targeting the wrong tenant.
19. **Resolve region before create.** Run `uip admin organizations regions list --output json` before `organizations create` or `tenants create` — `--region` is required. Tenant service catalog is region-aware: `tenants services list-available --region <REGION>`.

### APMS

20. **IP restriction is lockout-sensitive.** `ip-ranges delete` and `enforcement enable` both require `--confirm`. Before `enforcement enable`, run `ip-restriction my-ip` and verify the caller's IP is covered by an entry in `ip-ranges list`. The CLI also runs a server-side pre-flight on `enforcement enable` and on `ip-ranges delete` when enforcement is on, but never rely on it alone — confirm with the user explicitly first.
21. **Recovery from IP lockout requires platform-side action.** There is no CLI bypass once the caller is locked out. Either access from an in-allowlist IP and run `enforcement disable`, or use the UiPath Portal recovery flow / support.

## What NOT to Do

1. **Never delete built-in groups.** `type: "BuiltIn"` groups cannot be deleted. Only custom groups.
2. **Never pass IDs as flags.** Resource IDs and names are positional arguments: `groups members add <GROUP_ID> --user-ids ...`, NOT `--group-id <GROUP_ID>`. Same for all `get`, `update`, `delete`, `create` subcommands.
3. **Do NOT assume audit `events` returns a bare array.** It's `{auditEvents, next, previous}`.
4. **Do NOT loop on `--from-date`/`--to-date` to "paginate".** Bump `--limit` and the CLI handles cursor pagination internally.
5. **Do NOT silently default audit scope** to `tenant` or `org` when the prompt is ambiguous. Ask once, then proceed.
6. **Do NOT invent audit source/target/type GUIDs.** Always discover via `sources` first.
7. **Do NOT call audit `events` with no time bound** on a noisy tenant — default to a bounded window.
8. **Do NOT pass `--tenant-id` to `org`-scoped audit commands** — it's silently ignored. If you find yourself doing this, you probably meant `tenant` scope.
9. **Do NOT retry on 401 auth errors.** The token is missing the required scope (`Audit.Read` for audit). Tell the user to `uip logout && uip login` so the new scope is included.
10. **Do NOT call `authorization roles update` with only the flag you want to change.** The CLI assembles a full body from inline flags + `--file ./actions.json`; an omitted `--description` or `--file` overwrites that field with empty. Always `roles get` first and pass every field you want to preserve.
11. **Do NOT enable IP-restriction enforcement without `my-ip` verification.** Skipping the pre-flight is the canonical way to lock yourself out.

## Quick Start — Identity

The most common identity flow is **user management** — inviting users, assigning them to groups, and managing access.

### Step 0 — Verify login

```bash
uip login status --output json
```

If not logged in: `uip login`. The CLI reads org ID from the active session automatically.

### Step 1 — Invite a user

```bash
uip admin users invite \
  --email "<USER_EMAIL>" \
  --name "<FIRST_NAME>" \
  --surname "<LAST_NAME>" \
  --output json
```

### Step 2 — Find the user once they accept

```bash
uip admin users list \
  --search "<USER_EMAIL>" --output json
```

### Step 3 — Assign to a group

```bash
uip admin groups list --output json
uip admin groups members add <GROUP_ID> \
  --user-ids "<USER_ID>" \
  --output json
```

## Quick Start — Audit

For the canonical "find events in a window then export" flow. For specific scenarios jump to the [Task Navigation](#task-navigation) table.

### Audit scope disambiguation

The `org` vs `tenant` choice matters — they hit different basePaths and surface different events.

| User says... | Likely scope | Why |
|---|---|---|
| "who joined / left the organization", "who was made an admin", "license changes", "cross-tenant audit", **"failed/successful logins"**, **"login history for user X"**, **"who's been signing in"** | **org** | Org-level events (memberships, license, tenant lifecycle, **Identity Server / IdP authentication including User Login**) live under `/orgaudit_`. |
| "what happened on tenant X", "asset/queue/folder edits", "queue items processed", "job failures", "Action Center task changes", "Apps / AgentHub / Document Understanding / Integration Service / Test Manager activity" | **tenant** | Tenant-scoped events (Orchestrator, Action Center, Apps, AgentHub, Document Understanding, Integration Service, Test Manager, Data Fabric, Process Mining, Relay, Hypervisor, tenant-side Admin) live under `/{tenantId}/tenantaudit_`. Note: governance/AOps policies, source control, and pipelines are **org**-scoped despite the AOps name. |
| "everything everywhere" | **both** — run the same flow once per scope and present combined results. |

If the prompt is **vague about scope** AND no prior turn has established it, **stop and ask** (one yes/no question, two clarifications max). Don't assume `tenant` just because it's the more common case.

### Step 1 — Verify scope, then discover sources

```bash
# Tenant-scoped (most common)
uip admin audit tenant sources --output json > sources.json

# Org-scoped (admin events: tenant lifecycle, license, memberships)
uip admin audit org sources --output json > sources-org.json
```

Each entry has `id` (a GUID — pass to `events --source`), `name` (human-readable), and `eventTargets[]` (each with their own GUIDs and `eventTypes[]`).

### Step 2 — Query events with filters

```bash
uip admin audit tenant events \
  --source <SOURCE_GUID_FROM_STEP_1> \
  --from-date 2026-04-22T00:00:00Z \
  --to-date   2026-04-29T00:00:00Z \
  --limit 50 \
  --output json
```

The response is `{ "auditEvents": [...], "next": null, "previous": "..." }`. For more than 200 events, pass `--limit 500` (or larger) — the tool paginates internally. Do **not** write a manual loop in the agent.

### Step 3 — Export for compliance / sharing

```bash
uip admin audit tenant export \
  --from-date 2026-01-01 \
  --to-date   2026-02-01 \
  --output-file ./audit-jan.zip
```

One HTTP call per UTC day inside the window, aggregated into a single flat ZIP at `--output-file`. The result envelope reports `{Path, Bytes, Format: "zip", Days, NonEmptyDays}`. On any chunk failure (e.g. HTTP 504), no file is written and the error identifies which day failed.

## Quick Start — Authz, OMS, APMS

These flows are command-dense — drive them from the per-area reference files in [Task Navigation](#task-navigation). High-level entry points:

| Goal | Entry command |
|---|---|
| Create a custom role | `uip admin authorization roles create --scope <Organization\|TenantGlobal\|Tenant\|Project> --name "<NAME>" --file ./actions.json --output json` where `actions.json` is `["STUDIO.X.Y", ...]` |
| Assign a role to a user | `uip admin authorization roles assignments create --role-id <ROLE_ID> --identity-id <USER_ID> --identity-type User --output json` |
| See what a principal can do | `uip admin authorization check-access <USER_GUID_OR_EMAIL> --scope <Organization\|Tenant\|Folder\|Project> --output json` |
| Create a tenant | `uip admin organizations regions list` → `uip admin tenants create --name <NAME> --region <REGION> --output json` → poll `organizations operation get <OP_ID>` |
| Add a tenant service | `uip admin tenants services list-available --region <REGION>` → `uip admin tenants services add --tenant-id <TENANT_ID> --service <SERVICE> --output json` |
| Enable IP allowlist enforcement | `uip admin ip-restriction my-ip` → verify covered by `ip-ranges list` → `uip admin ip-restriction enforcement enable --confirm --output json` |

## Key Concepts

### Organization Hierarchy

```
Organization (org)
  └── Partition (= org in most cases)
        ├── Users           ← human identities
        ├── Groups          ← role containers (BuiltIn + Custom)
        ├── Robot Accounts  ← unattended automation identities
        └── External Apps   ← OAuth2 clients (Client ID + Secret)
```

### Robot Accounts vs External Apps

These are separate concepts — do not conflate them.

| Concept | Purpose | Managed By |
|---------|---------|------------|
| **Robot account** | Identity — who the robot is | Identity Server (`uip admin`) |
| **Robot credentials** | Per-robot Client ID + Secret for machine auth | Orchestrator (machine connection) |
| **External app** | OAuth2 client for API integrations, CI/CD | Identity Server (`uip admin`) |

Robot credentials are provisioned automatically by Orchestrator when connecting a robot to a machine — not by creating external apps.

### Authz vs Orchestrator roles

`uip admin authorization` only owns **cross-service / platform** custom roles. Services that manage their own roles — `orchestrator`, `dataservice`, `insights`, `taskmining`, `testmanager` — are not surfaced via the Authorization service catalog. Use `check-access` to see effective roles for a principal in those services, and `uip or roles ...` (uipath-platform skill) to mutate Orchestrator roles directly.

### OMS sync vs async

| Operation | Sync/Async | How to confirm completion |
|---|---|---|
| `organizations create`, `organizations delete` | **Async** — returns `operationId` | Poll `uip admin organizations operation get <OP_ID>` |
| `organizations update` | **Sync** | Response carries final state |
| `tenants create`, `update`, `delete`, `enable`, `disable` | **Async** — returns `operationId` | Poll `organizations operation get <OP_ID>` (single poll endpoint for all OMS async ops) |
| `tenants services add`, `enable`, `disable`, `remove` | **Sync** | Response carries final state |
| All `*list*`, `get`, `regions list`, `services list-available` | **Sync** | — |

### Audit scope → basePath

- `org`    → `{baseUrl}/{orgId}/orgaudit_/api/Query/...`
- `tenant` → `{baseUrl}/{orgId}/{tenantId}/tenantaudit_/api/Query/...`

Same `QueryApi` underneath; the only difference is which segment the SDK puts in the URL.

### Audit `Data` shape varies by verb

| Verb | `Data` shape |
|---|---|
| `audit <scope> sources` | array of `AuditEventSourceDto` |
| `audit <scope> events` | object `{auditEvents, next, previous}` |
| `audit <scope> export` | object `{Path, Bytes, Format, Days, NonEmptyDays}` |

`events` is the one verb that legitimately returns an object — pagination cursors live alongside the rows.

## Completion Output

### After identity mutations (create, update, delete, invite, members add/revoke, generate-secret)

1. Show the command result (success or failure)
2. For creates: display the new resource ID
3. For external-app create or generate-secret: **highlight the secret value and warn user to save it**
4. Offer logical next steps:
   - After creating a robot account → "Assign to a group for role-based access?"
   - After creating an external app → "Generate an additional secret?"
   - After inviting a user → "Check user list to see when they accept?"

### After an authz mutation (role create/update/delete, role assignments create/delete)

1. Show the command result and resource ID.
2. For role mutations: re-fetch the role and present a one-line summary (name, scope type, permission count) so the user can verify the upsert landed.
3. Offer next step: "Assign this role to a user/group/robot?" or "Run `check-access` for a principal to verify the new permissions resolve?"

### After an OMS mutation (organizations / tenants / services)

1. Show the command result.
2. For async operations: print the `operationId` and the polling command.
3. Loop `organizations operation get <OP_ID>` until terminal status, then report final state.
4. For tenant services (sync): show the post-mutation status from the response itself.

### After an APMS mutation (ip-ranges / enforcement / bypass-rules)

1. Show the command result.
2. After `enforcement enable`: explicitly confirm the caller's IP is still covered (re-run `my-ip` + `ip-ranges list` for sanity).
3. Offer next step: "Add a bypass rule for <URL>?" or "List current ip-ranges to verify?"

### After an audit query or export

1. **Operation & result** — e.g. `Found 47 audit events on tenant T in the last 7 days` or `Wrote 123,456 bytes to /path/to/audit.zip (3 days, 2 non-empty)`.
2. **Scope used** (`org` or `tenant`) and any `--tenant-id` override.
3. **Time window** — explicit ISO bounds, even if they came from a relative phrase ("last 7 days").
4. **Filters applied** — sources, types, users, status.
5. **Cursor state** — for `events`, mention whether `Data.previous` is null (start of audit history) or populated (more older events available — re-run with a larger `--limit`).
6. **Next step** — "Want me to widen the window?", "Want me to export this slice?", "Want me to filter by user X?". Wait for the user's choice; do not chain mutations.

## Task Navigation

| I need to... | Read first |
|---|---|
| **Identity CLI reference** (full flags + args + output codes) | [references/identity-commands.md](references/identity-commands.md) |
| **Manage users** (list, create, invite, update, delete) | [references/user-management.md](references/user-management.md) |
| **Manage groups** (CRUD + membership) | [references/group-management.md](references/group-management.md) |
| **Manage robot accounts** | [references/robot-account-management.md](references/robot-account-management.md) |
| **Manage external apps** (OAuth2 + secrets) | [references/external-app-management.md](references/external-app-management.md) |
| **Authorization CLI reference** (full flags + args + output codes) | [references/authorization/authorization-commands.md](references/authorization/authorization-commands.md) |
| **Manage custom roles** | [references/authorization/role-management.md](references/authorization/role-management.md) |
| **Manage role assignments** (who has what role where) | [references/authorization/role-assignment-management.md](references/authorization/role-assignment-management.md) |
| **List permission definitions** | [references/authorization/permission-catalog.md](references/authorization/permission-catalog.md) |
| **Check effective access** for a principal | [references/authorization/check-access.md](references/authorization/check-access.md) |
| **Organizations CLI reference** (full flags + args + output codes) | [references/organizations-commands.md](references/organizations-commands.md) |
| **Tenants CLI reference** (full flags + args + output codes) | [references/tenants-commands.md](references/tenants-commands.md) |
| **Manage the organization** (workflow: get / create / update / delete + async polling + regions + services) | [references/organization-management.md](references/organization-management.md) |
| **Manage tenants** (workflow: list, CRUD, enable/disable, tenant services) | [references/tenant-management.md](references/tenant-management.md) |
| **IP-restriction CLI reference** (full flags + args + output codes) | [references/ip-restriction/ip-restriction-commands.md](references/ip-restriction/ip-restriction-commands.md) |
| **Manage IP allowlist entries** (CIDR + ranges + expiry) | [references/ip-restriction/ip-range-management.md](references/ip-restriction/ip-range-management.md) |
| **Toggle enforcement** (and the my-ip safety check) | [references/ip-restriction/enforcement-management.md](references/ip-restriction/enforcement-management.md) |
| **Manage bypass rules** (URL-pattern exceptions) | [references/ip-restriction/bypass-rule-management.md](references/ip-restriction/bypass-rule-management.md) |
| **Audit CLI command reference** (full flags + args + output codes) | [references/audit-commands.md](references/audit-commands.md) |
| **Audit investigation workflows** (find → query → export, common gotchas) | [references/audit-workflow-guide.md](references/audit-workflow-guide.md) |

## References

### Identity

- **[identity-commands.md](references/identity-commands.md)** — Complete CLI reference for all `uip admin` identity commands with flags, arguments, and output codes
- **[user-management.md](references/user-management.md)** — User lifecycle workflows: discover, create, invite, update, delete, pagination, sorting
- **[group-management.md](references/group-management.md)** — Group CRUD, membership management (add/remove members), built-in vs custom groups
- **[robot-account-management.md](references/robot-account-management.md)** — Robot account lifecycle, relationship to external apps
- **[external-app-management.md](references/external-app-management.md)** — OAuth2 client management, secret generation/rotation, scope reference

### Authorization service

- **[authorization/authorization-commands.md](references/authorization/authorization-commands.md)** — Full CLI reference for `uip admin authorization` (roles, assignments, permissions, check-access) with flags, arguments, output codes
- **[authorization/role-management.md](references/authorization/role-management.md)** — Custom-role CRUD (inline `--name`/`--scope`/`--service` + `--file ./actions.json`, `BuiltIn` vs `Custom`, scope modes Organization / TenantGlobal / Tenant / Project)
- **[authorization/role-assignment-management.md](references/authorization/role-assignment-management.md)** — Role assignments: principal types, scope paths, inline + batch create/delete
- **[authorization/permission-catalog.md](references/authorization/permission-catalog.md)** — Read-only permission definitions catalog, role-authoring inputs
- **[authorization/check-access.md](references/authorization/check-access.md)** — Effective access lookup (PDP), tenant/folder scopes, coverage of services that manage their own roles

### OMS (organizations + tenants)

- **[organizations-commands.md](references/organizations-commands.md)** — Full CLI reference for `uip admin organizations` (lifecycle, async polling, regions, org services) with flags, arguments, output codes
- **[tenants-commands.md](references/tenants-commands.md)** — Full CLI reference for `uip admin tenants` (lifecycle, tenant services) with flags, arguments, output codes
- **[organization-management.md](references/organization-management.md)** — Org lifecycle workflows, async operation polling, region catalog, org-level service catalog
- **[tenant-management.md](references/tenant-management.md)** — Tenant CRUD workflows, enable/disable, tenant-service provisioning (add/enable/disable/remove)

### APMS (IP restriction)

- **[ip-restriction/ip-restriction-commands.md](references/ip-restriction/ip-restriction-commands.md)** — Full CLI reference for `uip admin ip-restriction` (ip-ranges, enforcement, bypass-rules, my-ip) with flags, arguments, output codes
- **[ip-restriction/ip-range-management.md](references/ip-restriction/ip-range-management.md)** — Allowlist entry CRUD (CIDR, start/end IP range, expiry, idempotent create, lockout-safe delete)
- **[ip-restriction/enforcement-management.md](references/ip-restriction/enforcement-management.md)** — Enforcement switch + `my-ip` pre-flight, lockout-recovery guidance
- **[ip-restriction/bypass-rule-management.md](references/ip-restriction/bypass-rule-management.md)** — URL-pattern bypass rules (server-compiled regex, file-based create)

### Audit

- **[audit-commands.md](references/audit-commands.md)** — Complete CLI reference for `uip admin audit` (org/tenant sources, events with envelope + cursors, ZIP export with atomic per-day chunking)
- **[audit-workflow-guide.md](references/audit-workflow-guide.md)** — End-to-end investigation flows: scope disambiguation, time-window bounds, cursor pagination, common gotchas
