---
name: uipath-admin
description: "UiPath Admin via `uip admin` — Identity Server (users, groups, robot accounts, external OAuth2 apps, secrets, PATs, SMTP), Authorization (custom roles, role assignments, permission catalog, effective-access check-access PDP), OMS (org read/update, tenant lifecycle, service provisioning, regions, async op polling), IP Restriction (allowlist, enforcement, bypass rules, lockout safety), and Audit via `uip admin audit` (event sources, paginated queries, JSON-folder or CSV export). Troubleshoot access-denied, login failures, role misconfig, IP lockout, PAT/app auth. Owns ALL org/tenant/identity audit — use `uip admin audit`, NOT `uip or audit-logs`, for any audit logs / audit trail / audit events / export / login history / who-did-what request. Orchestrator-specific roles/permissions/folders/jobs→uipath-platform. RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Admin

Administrative operations through `uip admin` for Identity Server, Authorization, OMS, IP Restriction, and Audit.

## When to Use

- **Identity:** Users, groups and membership, robot accounts, external apps and credentials, PATs, SMTP, OAuth2 scope discovery, and human or robot onboarding.
- **Authz:** Custom roles, assignments, permission catalogs, effective access, and ad-hoc grants. Role scopes are `Organization`, `TenantGlobal`, `Tenant`, and `Project`; assignments may also use `Folder` or `App`.
- **OMS:** Current organization, tenant lifecycle, service provisioning, operation polling, and region discovery. The CLI cannot create or delete organizations.
- **IP Restriction:** Allowlist entries, enforcement, bypass rules, and `ip-restriction my-ip` for public-IP questions and safety checks.
- **Audit:** Use `uip admin audit`, never `uip or audit-logs`, for organization or tenant audit events, sources, targets, types, queries, login history, membership/license activity, tenant activity, investigations, and exports. `uip or audit-logs` is Orchestrator-operational audit and belongs to `uipath-platform`.
- **Troubleshooting:** Use the [diagnose capability index](references/diagnose/CAPABILITY.md) and [identity troubleshooting guide](references/identity-troubleshoot-guide.md) for access, authentication, identity, tenant operations, provisioning, robot authentication, SMTP, PAT, external-app, or IP-lockout symptoms.

For audit availability, run `uip admin audit <scope> sources`; discover live catalogs instead of relying on memory. Route `org` versus `tenant` with [audit-workflow-guide.md → Audit scope disambiguation](references/audit-workflow-guide.md#scope-selection) and Rule 23. Natural-language investigations may cover resource changes/deletions, sign-ins, tenant changes, compliance windows, and cross-scope requests; run once per requested scope and combine results.

Troubleshooting routes: access denied → resolve the principal, check access, and inspect assignments ([Playbook 1](references/identity-troubleshoot-guide.md#playbook-1--user-cant-access-resource-x)); suspicious logins → organization audit ([Playbook 2](references/identity-troubleshoot-guide.md#playbook-2--suspicious-login-activity)); role misconfiguration → actions and scope ([Playbook 3](references/identity-troubleshoot-guide.md#playbook-3--role-misconfiguration)); IP lockout → `my-ip`, ranges, and enforcement ([Playbook 4](references/identity-troubleshoot-guide.md#playbook-4--ip-restriction-lockout)); PAT/external-app failure → expiry, scopes, and revocation audit ([Playbook 5](references/identity-troubleshoot-guide.md#playbook-5--pat-or-external-app-not-working)). SMTP uses `smtp get` and `smtp test`; poll stuck tenant operations; for provisioning no-ops check platform-pinned services; distinguish robot identity issues from credential-model issues.

## Critical Rules

Each rule is part of the agent contract.

### Universal

1. **Route correctly:** Orchestrator-specific role/permission requests go to `uip or roles` (`uipath-platform`), not `uip admin authorization`. Organization/tenant audit always uses `uip admin audit <scope>` (`sources`, `events`, or `export`), never `uip or audit-logs`, including audit history, exports, login history, compliance dumps, and “who did what/where.”
2. **Verify login first:** Run `uip login status --output json`. If unauthenticated, stop and ask the user to run `uip login`; it opens an interactive browser flow and must not run in automated/non-interactive sessions. Environment-authenticated sessions are already logged in. Resolve the organization from the active session.
3. **Use `--output json` on every command.** Parse programmatically and present conversationally.
4. **Stop on error and show it verbatim.** Never retry authentication failures; ask the user to run `uip login`.
5. **Resolve named principals before high-risk operations:** users, groups, robot accounts, and external apps, including assignment create/delete, user/group deletion, membership changes, robot deletion, external-app deletion, and secret generation. Search first and echo `Principal: <displayName> (<userName>) — <id>`. Zero matches: stop and ask. Multiple matches: show a numbered list and wait for a digit. Never substitute the current login user. See [Resolving Principal IDs](references/authorization/role-assignment-management.md#resolve-principals-before-mutation).

### Identity

6. **Discover before creating:** List robot accounts, groups, and external apps first; user invites are excepted.
7. **Show secrets once only** for external-app creation and `generate-secret`; tell the user to save them immediately.
8. **External apps require creation scopes:** `--app-scope` or `--user-scope`, such as `--app-scope "OR.Folders"`.
9. **Group membership uses user IDs:** Resolve users under Rule 5, then use `groups members add/revoke`.
10. **Confirm deletion** of users, groups, robot accounts, and external apps after resolving the target. Built-in groups (`type: "BuiltIn"`) cannot be deleted; only `Custom` groups can.

### Authz

11. **Built-in roles are read-only.** Create/update/delete only `Custom` roles. The CLI rejects service-managed or platform-level authoring; see [Services That Manage Their Own Roles](references/authorization/role-management.md#services-and-role-ownership).
12. **`roles create/update` are PUT-style upserts.** Build the body from flags and `--file ./actions.json`; always `roles get` before update because omitted flags overwrite fields.
13. **`--service` infers scope** (for example, `studio` → `Tenant`, `apps` → `Organization`); use `--scope` only to override. **Never guess a `serviceName`** — valid values and the re-derive command: [permission-catalog.md → serviceNames](references/authorization/permission-catalog.md#--service-servicenames-and-how-to-re-derive-them).
14. **Listing supports every service; authoring does not.** `roles list --service <svc>` and `roles assignments list --service <svc>` accept every service. Use `check-access` for effective access.
15. **Scope vocabularies differ:** `roles create --scope` = `Organization|TenantGlobal|Tenant|Project`; assignment create adds `Folder|App`; assignment list excludes `TenantGlobal`; `check-access --scope` supports only `Tenant|Folder`.
16. **Assignment create/delete requires principal resolution** under Rule 5; `--identity-id` is an unchecked raw UUID.
17. **Assignment ownership must match the scope path:** `ownerServiceName` must match the path service segment. `CentralizedAccess` has no service segment (`/` or `/tenant/<tid>`); others require lowercase `ownerServiceName` in the path. Apply display-name mappings such as `Reinfer` → `IXP`. See [Validate Role's Owning Service](references/authorization/role-assignment-management.md#validate-role-service-binding-and-scope-path).

### OMS

18. **Async lifecycle: auto-poll, then hand off.** Tenant create/update/delete/enable/disable return `operationId`; poll `organizations operation get <OP_ID>` three times at five-second intervals, stop on terminal status, then, if still in progress, present a numbered menu. Never loop indefinitely. Organizations create/delete are unavailable in the CLI and require Portal/support. See [Polling procedure](references/organization-management.md#polling-procedure-auto-poll-then-hand-off).
19. **`tenants delete` is soft-only.** Restoration requires support; no hard-delete flag exists.
20. **Tenant commands default to the login tenant.** Always provide explicit `<TENANT_ID>` for tenant delete/disable and `tenants services remove`.
21. **Resolve region before tenant creation:** Run `organizations regions list` first because `--region` is required and region-aware.
22. **Service disable/remove can falsely report Success.** Always re-list afterward. See [Tenants concepts](references/tenants-commands.md#concepts-and-safety-rules).

### Audit

23. **Disambiguate `org` versus `tenant` before querying.** If vague and no prior turn fixes scope, ask one clarifying question, using AskUserQuestion when available; do not silently default. If non-interactive clarification is impossible, query both and combine. Scope is positional: `uip admin audit org sources` or `uip admin audit tenant events`; `--scope` is invalid. See [Audit scope disambiguation](references/audit-workflow-guide.md#scope-selection).
24. **Events return `{auditEvents, next, previous}`**, not a bare array. Read `Data.auditEvents[]`; `next` is newer, `previous` older, and newest-backward traversal follows `previous`.
25. **`--limit` paginates internally.** Do not date-loop for pagination. Each server request is clamped to `[10, 200]`; CLI limits are up to 10000. `--limit` must be `[1, 10000]`; above 10000 returns `Result: "ValidationError"`. Omit it or stay within range for “everything.”
26. **Run `audit <scope> sources` first.** Never invent source, target, or type GUIDs; use live catalog GUIDs. The response also answers availability questions.
27. **Bound event windows in UTC ISO 8601.** Do not query noisy tenants without `--from-date` and `--to-date`. Accept date-only or timestamp forms such as `2026-04-01T14:30:00Z`. `--to-date` includes the exact instant; use the next day’s start or `T23:59:59.999Z` for a full final day. Resolve relative dates using actual UTC (`date -u`), never guessing, and echo the window.
27b. **An empty targeted query is complete.** State that no matching event was found, with scope, filters, and window; offer widening, the other scope, or checking resource existence. Never infer an actor from adjacent resources, event types, or broad searches, and never loosen filters merely to find a culprit. Name an actor only when the matching event supports both requested resource and verb; quote `createdOn` and identifying `eventDetails`. See [Step 5](references/audit-workflow-guide.md#step-5--report-no-match-safely).
28. **`--tenant-id` is ignored for org audit.** Use `audit tenant` instead.
29. **On audit 401, do not retry.** The token lacks `Audit.Read`; tell the user to run `uip logout && uip login`.
29b. **Retry transient audit 5xx errors** (`ErrorCode: server_error` / `Retry: RetryLater`, such as 503/504) up to two more times with several seconds of backoff, using the identical query. Do not change limit or window. Never present or save an error envelope as data; report failed retrieval.
30. **Exports use a base directory and whole UTC days.** Require `--from-date`, `--to-date`, and `--output-path`. Dates are inclusive calendar days; do not use the events next-day trick. `--output-path` is a directory, never a filename/extension; the CLI creates `audit_<from>_<to>_<generated-at>` inside it. Default JSON creates per-day `<YYYY-MM-DD>.json`; `--file-format csv` creates one merged CSV. Use CSV for flat spreadsheets and JSON for day-wise files. Pass a user-named destination verbatim without confirmation; confirm only a selected default such as `./audit-exports`. Report `Path` and `GeneratedAt`.

### IP Restriction

31. **Enforcement enable requires a safety check and confirmation:** Run `ip-restriction my-ip`, verify the caller IP is covered by `ip-ranges list`, then state: “After enabling IP restriction, any caller (Portal, CLI, robot, external app) whose source IP is not in `ip-ranges list` will be blocked from this org. Misconfiguration locks you out and requires platform-side recovery. Proceed?” Require `--confirm`. Deleting a range while enforcement is enabled also requires `--confirm`. See [enforcement management](references/ip-restriction/enforcement-management.md).
32. **IP-lockout recovery is platform-side:** use an allowlisted IP to disable enforcement or Portal recovery; there is no CLI bypass.
33. **Never expose “APMS.”** Say “IP Restriction” in user-facing output.

## What Not to Do

1. **Never pass resource IDs as flags.** IDs and names are positional, for example `groups members add <GROUP_ID> --user-ids ...`; apply this to get/update/delete/create commands.
2. **Never present authz results without provenance:** role name, `scopeType`, `ownerServiceName`, and tenant binding using names rather than UUIDs. See [Provenance contract](references/authorization/authorization-commands.md#provenance-contract-for-completion-output).

The rest are the inverse of the Critical Rules — never:
- use `uip or audit-logs` for org/tenant audit (R1), or default the audit scope when ambiguous (R23);
- treat `audit events` as a bare array (R24), hand-loop dates to paginate (R25), invent source/target/type GUIDs (R26), or query events unbounded on a noisy tenant (R27);
- name an actor the query didn't return (R27b), pass `--tenant-id` to `org` audit (R28), retry a 401 (R29), or save/report an error envelope as data (R29b);
- use the next-day `--to-date` trick on `export` (R30), or `roles update` with only the changed flag (R12);
- confuse provisioned `services list` with the `list-available` catalog (R22), or run an OMS mutation without echoing the resolved target (Output Etiquette).

## Quick Start

| Goal | Entry point |
|---|---|
| Invite user and assign group | [user-management.md](references/user-management.md), [group-management.md](references/group-management.md) |
| Create custom role | `uip admin authorization roles create --scope <Organization\|TenantGlobal\|Tenant\|Project> --name "<NAME>" --file ./actions.json --output json` |
| Grant permissions | [grant-permissions.md](references/authorization/grant-permissions.md) |
| Assign a role | Resolve principal; `roles get`; validate owner service/path; create assignment |
| Check effective access | `uip admin authorization check-access <USER_GUID_OR_EMAIL> --scope <Tenant\|Folder> --output json` |
| Create tenant | [tenant-management.md](references/tenant-management.md) |
| Add tenant service | `tenants services list-available --region <R>`; add; verify post-state |
| Find public IP | `ip-restriction my-ip --output json`; return `Data.ipAddress` |
| Enable IP enforcement | `my-ip` → verify range → `enforcement enable --confirm` |
| Query/export audit | [audit-workflow-guide.md](references/audit-workflow-guide.md) |

## Key Concepts

See [key-concepts.md](references/key-concepts.md) for organization hierarchy and distinctions among users, groups, robot accounts, robot credentials, and external apps.

## Output Etiquette and Report Contract

| Area | Required output |
|---|---|
| Identity mutations | Result and new resource ID; highlight one-time external-app secrets, warn to save them, and offer a relevant next step. |
| Authz reads/mutations | Role name, `scopeType`, `ownerServiceName` from the response, translated display name where applicable, and tenant binding resolved to a name. For `check-access`, label each row `direct` or `inherited from <Group name>` using nested `roleAssignments[].securityPrincipalType`. See [Provenance contract](references/authorization/authorization-commands.md#provenance-contract-for-completion-output). |
| OMS reads | Lead with `Organization: <ORG_NAME>`; separate provisioned services with status from the available catalog without status. Tenant reads also show name, UUID, and lifecycle status. |
| OMS mutations | Echo resolved target; auto-poll async operations three times at five-second intervals, then offer a numbered menu; re-list synchronous services to verify state. |
| Audit queries/exports | State scope, count, resolved UTC window, filters, and cursor state; obey Rules 23, 26, and 27. After reporting, wait for the user's next-step choice and do not chain mutations. For exports report `Path` and `GeneratedAt`. See [audit output etiquette](references/audit-workflow-guide.md#output-etiquette--after-every-audit-query-or-export). |
| IP Restriction mutations | Before enabling, state impact and obtain explicit confirmation; afterward rerun `my-ip` and `ip-ranges list` to confirm coverage; never say APMS. |

## Task Navigation

| Need | Reference |
|---|---|
| Identity CLI | [identity-commands.md](references/identity-commands.md) |
| Users | [user-management.md](references/user-management.md) |
| Groups and membership | [group-management.md](references/group-management.md) |
| Robot accounts | [robot-account-management.md](references/robot-account-management.md) |
| External apps | [external-app-management.md](references/external-app-management.md) |
| PATs | [pat-management.md](references/pat-management.md) |
| SMTP | [smtp-management.md](references/smtp-management.md) |
| Authorization CLI | [authorization-commands.md](references/authorization/authorization-commands.md) |
| Custom roles | [role-management.md](references/authorization/role-management.md) |
| Grant permissions | [grant-permissions.md](references/authorization/grant-permissions.md) |
| Role assignments | [role-assignment-management.md](references/authorization/role-assignment-management.md) |
| Permission catalog | [permission-catalog.md](references/authorization/permission-catalog.md) |
| Effective access | [check-access.md](references/authorization/check-access.md) |
| Organizations | [organizations-commands.md](references/organizations-commands.md), [organization-management.md](references/organization-management.md) |
| Tenants and services | [tenants-commands.md](references/tenants-commands.md), [tenant-management.md](references/tenant-management.md) |
| IP Restriction CLI | [ip-restriction-commands.md](references/ip-restriction/ip-restriction-commands.md) |
| IP ranges | [ip-range-management.md](references/ip-restriction/ip-range-management.md) |
| Enforcement | [enforcement-management.md](references/ip-restriction/enforcement-management.md) |
| Bypass rules | [bypass-rule-management.md](references/ip-restriction/bypass-rule-management.md) |
| Audit CLI | [audit-commands.md](references/audit-commands.md) |
| Audit investigations | [audit-workflow-guide.md](references/audit-workflow-guide.md) |
| Audit pagination | [audit-commands.md](references/audit-commands.md) plus Rule 25 |
| Troubleshooting | [identity-troubleshoot-guide.md](references/identity-troubleshoot-guide.md) |
| Diagnostic capability index | [diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Failure modes | [failure-modes.md](references/diagnose/failure-modes.md) |
| Diagnostic priority ladder | [troubleshooting-guide.md](references/diagnose/troubleshooting-guide.md) |
