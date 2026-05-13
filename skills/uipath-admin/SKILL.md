---
name: uipath-admin
description: "UiPath Admin — Identity Server management via uip admin. Users, groups, robot accounts, external apps (OAuth2), personal access tokens (PATs), SMTP email settings, federated credentials. For Orchestrator folders/jobs→uipath-platform. For RPA workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Admin

> **Preview** — Under active development. Command coverage will expand.

Identity Server management via `uip admin`. Users, groups, robot accounts, external OAuth2 apps, personal access tokens, SMTP settings.

## When to Use This Skill

- **Manage identity users** — list, create, invite, update, delete
- **Manage groups** — CRUD + add/remove members
- **Manage robot accounts** — create, update, delete unattended robot identities
- **Manage external apps** — OAuth2 clients, secrets, federated credentials
- **Manage personal access tokens (PATs)** — create, list, revoke, regenerate
- **Configure SMTP** — get, update, test, delete email settings
- **Browse OAuth2 scopes** — list available scopes for external apps and PATs
- **Onboard human user** — invite, assign to groups
- **Onboard robot account** — create account, assign to groups

## Critical Rules

1. **Verify login first.** Run `uip login status --output json`. If not logged in: `uip login`.
2. **Organization ID is resolved automatically from login.** CLI reads org ID from active session.
3. **Discover before creating.** `list` before `create` to avoid duplicates. Applies to robot accounts, groups, and external apps — not to `users invite`.
4. **Use `--output json` on all commands.** Parse programmatically. Present results conversationally.
5. **Tokens and secrets shown only once.** When creating external apps, generating secrets, creating PATs, or regenerating PATs — the value appears only in the creation response. Warn user to save immediately.
6. **External apps require scopes at creation.** Use `--app-scope` for application (service-to-service) scopes, `--user-scope` for delegated (user-context) scopes. At least one is required. Use `uip admin scopes list` to discover available scopes.
7. **Group membership uses user IDs, not usernames.** Resolve IDs via `users list` before `groups members add` or `groups members revoke`.
8. **Confirm before delete.** Always confirm with user before running `delete` or `revoke`.
9. **Stop on error (interactive use).** If any command fails, show error to user. Do not retry auth failures — ask user to run `uip login`.

## What NOT to Do

1. **Never delete built-in groups.** `type: "BuiltIn"` groups cannot be deleted. Only custom groups.
2. **Never pass IDs or names as flags.** They are positional arguments: `external-apps create "My App"`, NOT `--name "My App"`. Same for all `get`, `update`, `delete`, `create`, `revoke`, `regenerate` subcommands.
3. **Never combine `--non-confidential` with `--app-scope`.** Non-confidential apps only support `--user-scope`. If user wants app-only scopes, use confidential (default).
4. **Always ask for `--redirect-uri` when creating non-confidential apps or apps with `--user-scope`.** It is required — do not omit or default it. Ask the user for their callback URL.

## Quick Start

The most common identity flow is **user management** — inviting users, assigning them to groups, and managing access.

### Step 0 — Verify login

```bash
uip login status --output json
```

If not logged in: `uip login`. CLI reads org ID from active session automatically.

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

## Key Concepts

### Organization Hierarchy

```
Organization (org)
  └── Partition (= org in most cases)
        ├── Users           ← human identities
        ├── Groups          ← role containers (BuiltIn + Custom)
        ├── Robot Accounts  ← unattended automation identities
        ├── External Apps   ← OAuth2 clients (confidential + public)
        ├── PATs            ← per-user API tokens with scoped access
        └── SMTP Settings   ← email delivery configuration
```

### Robot Accounts vs External Apps

These are separate concepts — do not conflate them.

| Concept | Purpose | Managed By |
|---------|---------|------------|
| **Robot account** | Identity — who the robot is | Identity Server (`uip admin`) |
| **Robot credentials** | Per-robot Client ID + Secret for machine auth | Orchestrator (machine connection) |
| **External app** | OAuth2 client for API integrations, CI/CD | Identity Server (`uip admin`) |

Robot credentials are provisioned automatically by Orchestrator when connecting a robot to a machine — not by creating external apps.

### External App Types

| Type | Flag | Use Case | Secret? |
|------|------|----------|---------|
| **Confidential** | (default) | Server-side apps, CI/CD, service-to-service | Yes |
| **Non-confidential** | `--non-confidential` | SPAs, mobile apps, public clients | No |

### Scope Types

| Flag | Type | Use Case |
|------|------|----------|
| `--app-scope` | Application (app-only) | Service-to-service calls without user context |
| `--user-scope` | User (delegated) | Actions on behalf of a signed-in user |

Discover available scopes: `uip admin scopes list --output json`

## Completion Output

After any mutation (create, update, delete, invite, members add, members revoke, generate-secret, pat create/revoke/regenerate):

1. Show the command result (success or failure)
2. For creates: display the new resource ID
3. For external-app create, generate-secret, pat create, or pat regenerate: **highlight the token/secret value and warn user to save it**
4. Offer logical next steps:
   - After creating a robot account → "Assign to a group for role-based access?"
   - After creating an external app → "Generate an additional secret?"
   - After inviting a user → "Check user list to see when they accept?"
   - After creating a PAT → "Token saved? It won't be shown again."

## Task Navigation

| I need to... | Read first |
|---|---|
| **Full CLI command reference** | [references/identity-commands.md](references/identity-commands.md) |
| **Manage users** (list, create, invite, update, delete) | [references/user-management.md](references/user-management.md) |
| **Manage groups** (CRUD + membership) | [references/group-management.md](references/group-management.md) |
| **Manage robot accounts** | [references/robot-account-management.md](references/robot-account-management.md) |
| **Manage external apps** (OAuth2 + secrets + federated credentials) | [references/external-app-management.md](references/external-app-management.md) |
| **Manage personal access tokens** | [references/pat-management.md](references/pat-management.md) |
| **Configure SMTP email** | [references/smtp-management.md](references/smtp-management.md) |

## References

- **[identity-commands.md](references/identity-commands.md)** — Complete CLI reference for all `uip admin` commands
- **[user-management.md](references/user-management.md)** — User lifecycle workflows
- **[group-management.md](references/group-management.md)** — Group CRUD, membership management
- **[robot-account-management.md](references/robot-account-management.md)** — Robot account lifecycle
- **[external-app-management.md](references/external-app-management.md)** — OAuth2 clients, secrets, federated credentials
- **[pat-management.md](references/pat-management.md)** — Personal access token lifecycle
- **[smtp-management.md](references/smtp-management.md)** — SMTP email configuration
