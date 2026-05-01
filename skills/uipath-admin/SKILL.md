---
name: uipath-admin
description: "UiPath Admin — Identity Server management via uip admin identity. Users, groups, robot accounts, external apps (OAuth2), credential generation (Client ID/Secret). Onboarding workflows for human users and unattended robots. For Orchestrator folders/jobs→uipath-platform. For RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Glob, Grep
---

# UiPath Admin

> **Preview** — Under active development. Command coverage will expand.

Identity Server management via `uip admin identity`. Users, groups, robot accounts, external OAuth2 apps.

## When to Use

- **Manage identity users** — list, create, invite, update, delete
- **Manage groups** — CRUD + add/remove members
- **Manage robot accounts** — create, update, delete unattended robot identities
- **Manage external apps** — OAuth2 clients, generate/rotate secrets
- **Onboard human user** — invite, assign roles, assign folder permissions
- **Onboard robot account** — create account, generate credentials, configure machine
- **Identity concepts** — partitions, organizations, OAuth2 scopes
- **Generate Client ID/Secret** — credentials for API or robot authentication

## Critical Rules

1. **Verify login first.** Run `uip login status --output json`. If not logged in: `uip login`.

2. **Resolve organization ID first.** Every identity command requires `--organization <ORG_ID>`. Extract from `uip login status --output json` (field: `organizationId`). Never hardcode UUIDs.

3. **Discover before creating.** Always `list` before `create` to avoid duplicates. Robot account and group names must be unique within a partition.

4. **Use `--output json` on all commands.** Parse programmatically. Present results conversationally.

5. **Secrets shown only once.** When creating external apps or generating secrets, secret value appears only in creation response. Warn user to save immediately.

6. **External apps require scopes at creation.** `--scope` is required. Common scopes: `OR.Folders`, `OR.Assets`, `OR.Queues`, `OR.Jobs`, `OR.Machines`.

7. **Group membership uses user IDs, not usernames.** Resolve IDs via `users list` before `groups add-members` or `groups remove-members`.

8. **Confirm before delete.** Always confirm with user before running `delete` on users, groups, robot accounts, or external apps.

## Quick Start

```bash
uip login status --output json
uip admin identity users list --organization <ORG_ID> --output json
uip admin identity groups list --organization <ORG_ID> --output json
uip admin identity robot-accounts list --organization <ORG_ID> --output json
uip admin identity external-apps list --organization <ORG_ID> --output json
```

## Task Navigation

| I need to... | Read first |
|---|---|
| **Full CLI command reference** | [references/identity-commands.md](references/identity-commands.md) |
| **Manage users** (list, create, invite, update, delete) | [references/user-management.md](references/user-management.md) |
| **Manage groups** (CRUD + membership) | [references/group-management.md](references/group-management.md) |
| **Manage robot accounts** | [references/robot-account-management.md](references/robot-account-management.md) |
| **Manage external apps** (OAuth2 + secrets) | [references/external-app-management.md](references/external-app-management.md) |
| **Onboard user or robot** (end-to-end) | [references/onboarding-workflows.md](references/onboarding-workflows.md) |

## What NOT to Do

1. **Never hardcode organization IDs.** Resolve dynamically from `uip login status`.
2. **Never skip `list`.** Duplicate robot accounts or groups cause confusing errors.
3. **Never pass usernames to group membership.** Only user IDs (UUIDs) accepted.
4. **Never assume secrets persist.** Returned once at creation. If lost, generate new one.
5. **Never delete built-in groups.** `type: "BuiltIn"` groups cannot be deleted. Only custom groups.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not logged in` | Auth expired or missing | `uip login` |
| `HTTP 401` | Invalid/expired token | `uip login` |
| `HTTP 403` | Insufficient permissions | Needs admin/org-admin role |
| `Organization ID not available` | No org context | `uip login status --output json` — verify `organizationId` |
| `already exists` | Duplicate name | `list` first to check existing resources |
| `No fields to update` | No change flags | Provide `--name`, `--email`, etc. |
