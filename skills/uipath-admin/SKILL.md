---
name: uipath-admin
description: "UiPath Admin via `uip admin` — Identity Server (users, groups, robot accounts, external OAuth2 apps, secrets), Authorization (custom roles, role assignments, permission catalog, effective-access via check-access PDP), OMS (org read/update, tenant lifecycle, service provisioning, regions, async operation polling), IP Restriction (allowlist, enforcement switch, bypass rules, lockout safety), Audit (event sources, paginated queries, ZIP or single-CSV exports — login history, compliance dumps, who-did-what-when-where on a resource). For Orchestrator-specific roles/permissions/folders/jobs→uipath-platform. For RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Admin

Administrative operations on UiPath via `uip admin` — Identity Server, Authorization, OMS, IP Restriction, Audit. Per-area workflows, command references, and procedures are in the linked files below — this file is the entry contract.

## When to Use This Skill

### Identity

- **Manage identity users** — list, create, invite, update, delete
- **Manage groups** — CRUD + add/remove members
- **Manage robot accounts** — create, update, delete unattended robot identities
- **Manage external apps** — OAuth2 clients, secrets, federated credentials
- **Manage personal access tokens (PATs)** — create, list, revoke, regenerate
- **Configure SMTP** — get, update, test, delete email settings
- **Browse OAuth2 scopes** — list available scopes for external apps and PATs
- **Onboard human user** — invite, assign to groups
- **Onboard robot account** — create account, assign to groups

### Authz

- **Manage custom roles** — CRUD on Authorization service role definitions (scope shapes: `Organization`, `TenantGlobal`, `Tenant`, `Project`)
- **Manage role assignments** — assign roles to users/groups/robot accounts at `Organization`, `Tenant`, `TenantGlobal`, `Project`, `Folder`, or `App` scope
- **List permission definitions** — read-only catalog of permissions across services
- **Check effective access** — compute what a principal can actually do at a given scope (Policy Decision Point)
- **Grant permission(s) to a principal** — ad-hoc "grant me X" / "give <user> Y, Z" requests resolved via the scope/service intersection flow

### OMS

- **Inspect / update the current organization** — `uip admin organizations` (read + update only; no CLI create/delete)
- **Manage tenant lifecycle** — create, enable, disable, delete tenants in the caller's org
- **Provision org-level or tenant-level services** — `services list`, `list-available`, `add`, `enable`, `disable`, `remove`
- **Poll async OMS operations** — `tenants` mutations return `operationId`; poll via `organizations operation get <id>` (the canonical poll endpoint)
- **List available regions** — discover provisioning regions before `tenants create`

### IP Restriction

- **Manage IP allowlisting** — add / update / delete CIDR entries that gate inbound access
- **Toggle IP-restriction enforcement** — turn the org-wide allowlist switch on or off (with lockout safety)
- **Manage bypass rules** — URL-pattern exceptions to IP allowlisting
- **Look up the caller's public IP** — sanity check before enabling enforcement

### Audit

Activate on both **explicit audit requests** and **natural-language investigation intent** — users rarely say "audit events" by name.

- **Explicit** — `uip admin audit` commands; list sources / targets / types; query, filter, paginate, or export events; CSV/ZIP dump of audit history for a window.
- **Query audit events** — list event sources, filter events by source / target / type / user / status / time window at org or tenant scope
- **Export audit events** — chunked download from the long-term store (one call per UTC day, atomic abort on any chunk failure) as a ZIP of day-wise JSON files (default) or a single merged CSV via `--file-format csv`
- **Membership / license phrasings** — "who joined / left the organization", "who was made an admin", "license changes", "cross-tenant audit"
- **Sign-in / authentication phrasings** — "failed/successful logins", "login history for user X", "who's been signing in"
- **Tenant-activity phrasings** — "what happened on tenant X", "asset/queue/folder edits", "queue items processed", "job failures", "Action Center task changes", "Apps / AgentHub / Document Understanding / Integration Service / Test Manager activity"
- **Cross-scope phrasings** — "everything everywhere" (run the flow once per scope and present combined)
- **Investigation intent** (full-sentence form) — "Who deleted the X folder last Tuesday?", "Show me failed logins for user Y this month.", "What changed on tenant Z between Jan 1 and Feb 1?", "Give me the audit log for the last 30 days.", "Was the API key rotated by someone in our org?", "Export everything for compliance for Q4."

> **Scope routing** (which phrasing → `org` vs `tenant`, and why) lives in [audit-workflow-guide.md → Audit scope disambiguation](references/audit-workflow-guide.md#audit-scope-disambiguation--route-by-user-phrasing). Critical Rule 23 governs the stop-and-ask requirement when scope is ambiguous.

## Critical Rules

Each rule is the agent contract. Per-area detail is in the linked reference files.

### Universal

1. **Route Orchestrator-specific role/permission requests to `uip or roles`** (`uipath-platform` skill). `uip admin authorization` does NOT own Orchestrator's role catalog.
2. **Verify login first.** `uip login status --output json`. If not logged in: `uip login`. Org id is resolved from the active session.
3. **Use `--output json` on every command.** Parse programmatically; present conversationally.
4. **Stop on error.** Show the error verbatim. Never retry auth failures — ask the user to `uip login`.
5. **Resolve every named principal before high-risk ops.** Any command that touches a named user / group / robot account / external app — `roles assignments create/delete`, `users delete`, `groups delete`, `groups members add/revoke`, `robot-accounts delete`, `external-apps delete`, `external-apps generate-secret` — MUST first search the directory and echo `Principal: <displayName> (<userName>) — <id>` back before the mutation runs. Zero matches → stop and ask; never fall back to the current login user. Multiple matches → numbered list, wait for a digit. Procedure: [role-assignment-management.md → Resolving Principal IDs](references/authorization/role-assignment-management.md#resolving-principal-ids).

### Identity

6. **Discover before creating.** `list` before `create` to avoid duplicates (robot accounts, groups, external apps — `users invite` excepted).
7. **Secrets shown only once** on external-app create and `generate-secret` — warn the user to save immediately.
8. **External apps require scopes at creation** — `--app-scope` or `--user-scope` is required (e.g., `--app-scope "OR.Folders"`).
9. **Group membership uses user IDs.** Resolve via `users list` per Rule 5, then `groups members add/revoke`.
10. **Confirm before delete** on users / groups / robot accounts / external apps — after resolving the named target per Rule 5.

### Authz

11. **Built-in roles are read-only.** Only `Custom` roles can be created / updated / deleted. CLI also rejects authoring against service-managed and platform-level services. Service lists: [role-management.md → Services That Manage Their Own Roles](references/authorization/role-management.md#services-that-manage-their-own-roles).
12. **`roles create` / `roles update` are PUT-style upserts.** Body is assembled from inline flags + `--file ./actions.json`. Always `roles get` first before updating — omitted flags overwrite that field.
13. **`--service` infers scope** (e.g., `--service studio` → `Tenant`; `--service apps` → `Organization`). Combine with `--scope` only to override.
14. **Listing works for every service; authoring is what's blocked.** `roles list --service <svc>` and `roles assignments list --service <svc>` accept every service. For effective access on a principal use `check-access` (PDP).
15. **Scope vocab differs across verbs.** `roles create --scope`: `Organization|TenantGlobal|Tenant|Project`. `roles assignments create --scope`: those + `Folder|App`. `roles assignments list --scope`: excludes `TenantGlobal`. `check-access --scope`: only `Tenant|Folder`.
16. **`roles assignments create/delete` MUST resolve the principal first** per Rule 5 — `--identity-id` is a raw UUID the CLI does not name-check.
17. **`roles assignments create` MUST match the role's `ownerServiceName` to the scope-path service segment.** `CentralizedAccess` → no service segment (`/` or `/tenant/<tid>`); anything else → path must include `lowercase(ownerServiceName)`. Display-name mapping (e.g., `Reinfer` → "IXP") + full procedure: [role-assignment-management.md → Validate Role's Owning Service](references/authorization/role-assignment-management.md#validate-roles-owning-service-vs-assignment-scope-path).

### OMS

18. **Async lifecycle: auto-poll, then hand off.** `tenants create/update/delete/enable/disable` return `operationId`. Auto-poll `organizations operation get <OP_ID>` 3× at 5 s; on terminal status stop and report; still in-progress after 3 polls → numbered menu, never indefinite loop. **`organizations create` and `organizations delete` are not exposed by the CLI** — Portal / support flow only. Procedure: [organization-management.md → Polling procedure](references/organization-management.md#polling-procedure-auto-poll-then-hand-off).
19. **`tenants delete` is soft-only.** No hard-delete flag; restoration is via support.
20. **Tenant commands default to the login tenant.** Always pass an explicit `<TENANT_ID>` for destructive ops (`tenants delete`, `tenants disable`, `tenants services remove`).
21. **Resolve region before tenant create.** `--region` is required on `tenants create` — run `organizations regions list` first. Tenant service catalog is region-aware.
22. **`services disable` / `remove` may no-op despite Success** on certain services. Always re-list after mutating. Gap list: [tenants-commands.md → Concepts](references/tenants-commands.md#concepts).

### Audit

23. **Disambiguate `org` vs `tenant` scope before querying.** If the prompt is vague AND no prior turn fixed the scope, **stop and ask once** — never silently default to `tenant`. **Scope is a positional subgroup, NOT a flag:** write `uip admin audit org sources` / `uip admin audit tenant events` — there is no `--scope` option (`audit sources --scope organization` is invalid). Routing table (user-phrasing → scope + why it lives where) and investigation playbooks: [audit-workflow-guide.md → Audit scope disambiguation](references/audit-workflow-guide.md#audit-scope-disambiguation--route-by-user-phrasing).
24. **`audit <scope> events` returns an object, not a bare array.** Shape is `{auditEvents, next, previous}`. Do not index `Data[0]`; read `Data.auditEvents[]`. **Cursor semantics are chronological**: `next` = newer events, `previous` = older events. The default newest-backward walk follows `previous`.
25. **`--limit` paginates internally — never loop on `--from-date` / `--to-date` to "paginate".** The server clamps `maxCount` to `[10, 200]` per request; when the user wants more than 200, the CLI fetches `ceil(N/200)` pages under the hood. Pass `--limit 500` (or larger) — do NOT re-implement pagination in the agent.
26. **Discover via `audit <scope> sources` first — never invent source / target / type GUIDs.** The catalog response gives the GUIDs you pass to `events --source / --target / --type`.
27. **Bound the time window, ISO 8601 in UTC.** Don't call `audit <scope> events` without `--from-date` and `--to-date` on a noisy tenant. Accepted formats: date-only (`2026-04-01`) or with time (`2026-04-01T14:30:00Z`). **`--to-date` is inclusive of the exact instant** — to capture a full final day, pass the start of the next day or `T23:59:59.999Z`.
28. **`--tenant-id` is silently ignored on `org`-scoped audit commands.** If you find yourself reaching for it on `audit org events`, switch to `audit tenant` instead.
29. **On 401 from audit, do NOT retry.** The token is missing the `Audit.Read` scope; tell the user to `uip logout && uip login`.
30. **`audit <scope> export` writes a ZIP (default) or a single merged CSV from the long-term store.** `--from-date`, `--to-date`, and `--output-file` are all required; dates per Rule 27. **`--file-format <zip|csv>`** selects the shape: `zip` (default) is one JSON file per UTC day; `csv` merges every event into one CSV — pick `csv` when the user wants a flat spreadsheet/Excel-friendly dump and `zip` for archival or per-day JSON. Match the `--output-file` extension to the format (`.zip` / `.csv`). **Never overwrite a path the user did not explicitly approve** — surface the resolved `--output-file` and confirm before running.

### IP Restriction

31. **`enforcement enable` is lockout-sensitive — prompt + impact statement required.** Run `ip-restriction my-ip` and verify the caller's IP is covered by an entry in `ip-ranges list`. **Then prompt the user with the impact** before flipping: *"After enabling IP restriction, any caller (Portal, CLI, robot, external app) whose source IP is not in `ip-ranges list` will be blocked from this org. Misconfiguration locks you out and requires platform-side recovery. Proceed?"* `--confirm` is required; `ip-ranges delete` while enforcement is on also requires `--confirm`. Procedure: [enforcement-management.md](references/ip-restriction/enforcement-management.md).
32. **Recovery from IP lockout requires platform-side action.** No CLI bypass — either access from an in-allowlist IP and `enforcement disable`, or use the Portal recovery flow.
33. **"APMS" is internal — never expose to the user.** "APMS" (Access Policy Management Service) is the platform's internal name for IP Restriction. Use "IP Restriction" in every user-facing surface.

## What NOT to Do

1. **Never delete built-in groups.** `type: "BuiltIn"` groups cannot be deleted. Only custom groups.
2. **Never pass IDs as flags.** Resource IDs and names are positional arguments: `groups members add <GROUP_ID> --user-ids ...`, NOT `--group-id <GROUP_ID>`. Same for all `get`, `update`, `delete`, `create` subcommands.
3. **Do NOT assume audit `events` returns a bare array.** It's `{auditEvents, next, previous}`.
4. **Do NOT loop on `--from-date`/`--to-date` to "paginate".** Bump `--limit` and the CLI handles cursor pagination internally.
5. **Do NOT silently default audit scope** to `tenant` or `org` when the prompt is ambiguous. Ask once, then proceed.
6. **Do NOT invent audit source/target/type GUIDs.** Always discover via `sources` first.
7. **Do NOT call audit `events` with no time bound** on a noisy tenant — default to a bounded window.
8. **Do NOT pass `--tenant-id` to `org`-scoped audit commands** — it's silently ignored.
9. **Do NOT retry on 401 auth errors.** The token is missing the required scope (`Audit.Read` for audit). Tell the user to `uip logout && uip login`.
10. **Do NOT call `roles update` with only the flag you want to change.** Re-fetch first; the upsert body overwrites omitted fields (Rule 12).
11. **Do NOT present authz results without provenance** — role name, `scopeType`, `ownerServiceName`, tenant-binding (names not UUIDs). Detail: [authorization-commands.md → Provenance contract](references/authorization/authorization-commands.md#provenance-contract-for-completion-output).
12. **Do NOT conflate provisioned services with the available catalog.** `services list` returns provisioned with status; `services list-available` is the catalog. Present them as separate sections.
13. **Do NOT run an OMS mutation without naming the target.** Echo org name / tenant name + UUID / service type + region before running.

## Quick Start

One row per common goal. Per-area workflows are in the reference files.

| Goal | Entry command(s) |
|---|---|
| **Invite a user → assign to group** | [user-management.md](references/user-management.md) + [group-management.md](references/group-management.md) |
| **Create a custom role** | `uip admin authorization roles create --scope <Organization\|TenantGlobal\|Tenant\|Project> --name "<NAME>" --file ./actions.json --output json` (actions.json = `["STUDIO.X.Y", ...]`) |
| **Grant permission(s) to a principal** ("grant me X", "give alice Y, Z") | [grant-permissions.md](references/authorization/grant-permissions.md) — intersection-and-menu flow |
| **Assign a role to a principal** | (1) Resolve principal per Rule 5. (2) `roles get <ROLE_ID>` → echo `ownerServiceName` + verify scope-path service segment matches (Rule 17). (3) `roles assignments create --role-id <ROLE_ID> --identity-id <ID> --identity-type <User\|Group\|Robot\|ExternalApplication> --output json` |
| **See what a principal can do** | `uip admin authorization check-access <USER_GUID_OR_EMAIL> --scope <Tenant\|Folder> --output json` (Rule 15) |
| **Create a tenant** | [tenant-management.md](references/tenant-management.md) — region + default-services resolution, file-body shape, operation polling (Rule 18) |
| **Add a tenant service** | `tenants services list-available --region <R>` → `tenants services add --tenant-id <TID> --service <SVC>` (verify post-state per Rule 22) |
| **Enable IP allowlist enforcement** | `ip-restriction my-ip` → verify covered by `ip-ranges list` → `ip-restriction enforcement enable --confirm` (Rule 31) |
| **Query audit events / export** | [audit-workflow-guide.md](references/audit-workflow-guide.md) — scope disambiguation + 4 investigation playbooks (who-did-X, login history, date-range dump, overview) |

## Key Concepts

### Organization hierarchy

```
Organization (org)
  └── Partition (= org in most cases)
        ├── Users           ← human identities
        ├── Groups          ← role containers (BuiltIn + Custom)
        ├── Robot Accounts  ← unattended automation identities
        └── External Apps   ← OAuth2 clients (Client ID + Secret)
```

### Robot accounts vs external apps

| Concept | Purpose | Managed by |
|---|---|---|
| **Robot account** | Identity — who the robot is | Identity Server (`uip admin`) |
| **Robot credentials** | Per-robot Client ID + Secret for machine auth | Orchestrator (machine connection) |
| **External app** | OAuth2 client for API integrations, CI/CD | Identity Server (`uip admin`) |

Robot credentials are provisioned automatically by Orchestrator on machine connect — not by creating external apps.

## Output Etiquette

What to surface after each verb. Per-area detail in the reference files; this is the contract.

| Area | Always surface |
|---|---|
| **Identity** mutations | Result + new resource id; for external-app create / `generate-secret`, **highlight the secret + warn to save**; offer a next step (assign to group, generate another secret, etc.). |
| **Authz** reads + mutations | Provenance: role name, `scopeType`, `ownerServiceName` (read directly from response — translate to display name per Rule 17, e.g., `Reinfer`→"IXP"), tenant binding (resolve UUID → name). **`check-access`: label each row as `direct` or `inherited from <Group name>`** by inspecting the nested `roleAssignments[].securityPrincipalType`. Full contract: [authorization-commands.md → Provenance contract](references/authorization/authorization-commands.md#provenance-contract-for-completion-output). |
| **OMS** reads | Separate **provisioned** (with status) from **available catalog** (no status). Lead with `Organization: <ORG_NAME>` (and tenant name + UUID + lifecycle status for tenant reads). |
| **OMS** mutations | Echo the resolved target before running (Anti-pattern 13). Async: auto-poll 3× at 5 s, then numbered menu (Rule 18). Sync services: re-list to verify post-state (Rule 22). |
| **Audit** queries | Disambiguate `org` vs `tenant` first (Rule 23). Discover via `sources` (Rule 26). Bound the window (Rule 27). Operation summary (count, scope, time window, filters, cursor state). Wait for the user's next-step choice; do not chain mutations. Investigation playbooks: [audit-workflow-guide.md](references/audit-workflow-guide.md). |
| **IP Restriction** mutations | Before `enforcement enable`: state the impact, require explicit user confirmation (Rule 31). After: confirm caller's IP is still covered (re-run `my-ip` + `ip-ranges list`). Never use the internal name "APMS" in user-facing output. |

For per-area full checklists, follow the table's inline links: Identity → [identity-commands.md](references/identity-commands.md#output-etiquette--after-any-identity-mutation); Authz → [authorization-commands.md](references/authorization/authorization-commands.md#provenance-contract-for-completion-output); Audit → [audit-workflow-guide.md](references/audit-workflow-guide.md#output-etiquette--after-an-audit-query-or-export).

## Task Navigation

| I need to... | Read first |
|---|---|
| Identity CLI reference | [references/identity-commands.md](references/identity-commands.md) |
| Manage users (list / create / invite / update / delete) | [references/user-management.md](references/user-management.md) |
| Manage groups (CRUD + membership) | [references/group-management.md](references/group-management.md) |
| Manage robot accounts | [references/robot-account-management.md](references/robot-account-management.md) |
| Manage external apps (OAuth2 + secrets + federated credentials) | [references/external-app-management.md](references/external-app-management.md) |
| Manage personal access tokens (PATs) | [references/pat-management.md](references/pat-management.md) |
| Configure SMTP email settings | [references/smtp-management.md](references/smtp-management.md) |
| Authorization CLI reference | [references/authorization/authorization-commands.md](references/authorization/authorization-commands.md) |
| Manage custom roles | [references/authorization/role-management.md](references/authorization/role-management.md) |
| Grant permission(s) to a principal — scope/service intersection flow | [references/authorization/grant-permissions.md](references/authorization/grant-permissions.md) |
| Manage role assignments (incl. role-service vs scope-path validation, Rule 17) | [references/authorization/role-assignment-management.md](references/authorization/role-assignment-management.md) |
| List permission definitions | [references/authorization/permission-catalog.md](references/authorization/permission-catalog.md) |
| Check effective access for a principal | [references/authorization/check-access.md](references/authorization/check-access.md) |
| Organizations CLI reference | [references/organizations-commands.md](references/organizations-commands.md) |
| Tenants CLI reference | [references/tenants-commands.md](references/tenants-commands.md) |
| Manage the organization (read + update, polling, regions, org services read-only) | [references/organization-management.md](references/organization-management.md) |
| Manage tenants (CRUD, enable/disable, tenant services) | [references/tenant-management.md](references/tenant-management.md) |
| IP-restriction CLI reference | [references/ip-restriction/ip-restriction-commands.md](references/ip-restriction/ip-restriction-commands.md) |
| Manage IP allowlist entries | [references/ip-restriction/ip-range-management.md](references/ip-restriction/ip-range-management.md) |
| Toggle enforcement (+ `my-ip` safety check) | [references/ip-restriction/enforcement-management.md](references/ip-restriction/enforcement-management.md) |
| Manage bypass rules | [references/ip-restriction/bypass-rule-management.md](references/ip-restriction/bypass-rule-management.md) |
| Audit CLI reference | [references/audit-commands.md](references/audit-commands.md) |
| Audit investigation workflows (scope disambiguation, who-did-X, login history, date-range dump, overview) | [references/audit-workflow-guide.md](references/audit-workflow-guide.md) |
| Paginate audit events beyond 200 | [references/audit-commands.md](references/audit-commands.md) + Rule 25 |
