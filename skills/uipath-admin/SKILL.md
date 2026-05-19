---
name: uipath-admin
description: "Always invoke for `uip admin` commands or audit-investigation prompts (who/when/where on a resource, login history, compliance dumps). UiPath Admin via `uip admin <subject> <verb>` — Identity Server (users, groups, robot accounts, external OAuth2 apps, credential generation) and Audit Service (event sources, paginated event queries, long-term-store ZIP exports). For Orchestrator folders/jobs→uipath-platform. For RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Admin

> **Preview** — Under active development. Command coverage will expand.

Administrative operations on UiPath via `uip admin` — Identity Server (users, groups, robot accounts, external OAuth2 apps) and Audit Service (event sources, event queries, long-term-store ZIP exports).

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

### Audit

Activate on both **explicit audit requests** and **natural-language investigation intent** — users rarely say "audit events" by name.

- **Explicit** — `uip admin audit` commands; list sources / targets / types; query, filter, paginate, or export events; CSV/ZIP dump of audit history for a window.
- **Investigation intent** — "Who deleted the X folder last Tuesday?", "Show me failed logins for user Y this month.", "What changed on tenant Z between Jan 1 and Feb 1?", "Give me the audit log for the last 30 days.", "Was the API key rotated by someone in our org?", "Export everything for compliance for Q4."

## Critical Rules

### Identity

1. **Verify login first.** Run `uip login status --output json`. If not logged in: `uip login`.
2. **Organization ID is resolved automatically from login.** CLI reads org ID from active session.
3. **Discover before creating.** `list` before `create` to avoid duplicates. Applies to robot accounts, groups, and external apps — not to `users invite`.
4. **Use `--output json` on all commands.** Parse programmatically. Present results conversationally.
5. **Secrets shown only once.** When creating external apps or generating secrets, secret value appears only in creation response. Warn user to save immediately.
6. **External apps require scopes at creation.** `--scope` is required. Common scopes: `OR.Folders`, `OR.Assets`, `OR.Queues`, `OR.Jobs`, `OR.Machines`.
7. **Group membership uses user IDs, not usernames.** Resolve IDs via `users list` before `groups members add` or `groups members revoke`.
8. **Confirm before delete.** Always confirm with user before running `delete` on users, groups, robot accounts, or external apps.
9. **Stop on error (interactive use).** If any command fails, show error to user. Do not retry auth failures — ask user to run `uip login`.

### Audit

10. **Pick scope before any other audit call — and don't silently default.** Use the [Disambiguation rule](#audit-scope-disambiguation) below: if the prompt is vague about `org` vs `tenant` AND there's no prior conversational context, **ask** which scope (and which tenant if `tenant`). `tenant` requires either a tenant in the login context or `--tenant-id <guid>`. `org` ignores `--tenant-id`.
11. **Discover source IDs with `sources` before filtering `events`.** Never invent GUIDs for `--source`/`--target`/`--type` — the SDK won't help you guess.
12. **`events` returns `{ auditEvents, next, previous }` — NOT a bare array.** Cursor naming is **chronological**: `next` = newer, `previous` = older. The default newest-backward walk follows `previous`.
13. **`events` server-clamps `maxCount` to `[10, 200]`.** When the user wants more than 200, the tool paginates internally — pass `--limit N` and the tool fetches `ceil(N/200)` pages. Do **not** re-implement pagination in the agent.
14. **`export` writes a ZIP from the long-term store.** `--from-date`, `--to-date`, and `--output-file` are required and ISO 8601 (for the dates). Never overwrite a path the user did not explicitly approve.
15. **ISO 8601 for time bounds, UTC by default.** Date-only (`2026-04-01`) or with time (`2026-04-01T14:30:00Z`). `--to-date` is inclusive of the exact instant — pass the start of the next day (or `T23:59:59.999Z`) to capture a full final day.

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
| **Full CLI command reference (identity)** | [references/identity-commands.md](references/identity-commands.md) |
| **Manage users** (list, create, invite, update, delete) | [references/user-management.md](references/user-management.md) |
| **Manage groups** (CRUD + membership) | [references/group-management.md](references/group-management.md) |
| **Manage robot accounts** | [references/robot-account-management.md](references/robot-account-management.md) |
| **Manage external apps** (OAuth2 + secrets) | [references/external-app-management.md](references/external-app-management.md) |
| **Full CLI command reference (audit)** | [references/audit-commands.md](references/audit-commands.md) |
| **Investigation playbooks** (who-did-X / login-history / date-range dump / overview) | [references/audit-workflow-guide.md](references/audit-workflow-guide.md) |
| **Paginate audit events beyond 200** | [references/audit-commands.md](references/audit-commands.md) (events flag table) + Critical Rule #13 |

## References

- **[identity-commands.md](references/identity-commands.md)** — Complete CLI reference for all `uip admin` identity commands with flags, arguments, and output codes
- **[user-management.md](references/user-management.md)** — User lifecycle workflows: discover, create, invite, update, delete, pagination, sorting
- **[group-management.md](references/group-management.md)** — Group CRUD, membership management (add/remove members), built-in vs custom groups
- **[robot-account-management.md](references/robot-account-management.md)** — Robot account lifecycle, relationship to external apps
- **[external-app-management.md](references/external-app-management.md)** — OAuth2 client management, secret generation/rotation, scope reference
- **[audit-commands.md](references/audit-commands.md)** — Single source of truth for every `uip admin audit` subcommand: signature, every flag with required/optional, the `Code` value, and the exact `Data` shape returned
- **[audit-workflow-guide.md](references/audit-workflow-guide.md)** — Narrative playbook for the four canonical investigations: who-did-X, login-history, date-range-dump, and org-vs-tenant comparison
