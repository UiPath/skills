# Identity CLI Command Reference

Complete reference for all `uip admin identity` commands. Every command supports `--output json` and `--login-validity <minutes>`. Organization ID is resolved automatically from the active login session.

## Prerequisites

```bash
# Verify login — org ID is resolved automatically
uip login status --output json
```

---

## Users — `uip admin identity users`

### `users list`

List users in a partition.

```bash
uip admin identity users list --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `-s, --search <term>` | No | Search by name or email |
| `--order-by <field>` | No | Sort field (e.g., `UserName`, `Email`) |
| `--order-direction <asc\|desc>` | No | Sort direction (default: asc) |
| `-l, --limit <number>` | No | Items to return (default: 20) |
| `--offset <number>` | No | Items to skip (default: 0) |

**Output code:** `UserList`

### `users get`

Get user details by ID.

```bash
uip admin identity users get <USER_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<USER_ID>` | Yes | User ID (UUID) |

**Output code:** `UserDetails`

### `users create`

Create a new user.

```bash
uip admin identity users create <USERNAME> \
  --email <EMAIL> \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<USERNAME>` | Yes | Username |
| `-e, --email <email>` | Yes | Email address |
| `-n, --name <name>` | No | First name |
| `--surname <surname>` | No | Last name |

**Output code:** `UserCreated`

### `users update`

Update an existing user. At least one field flag is required.

```bash
uip admin identity users update <USER_ID> \
  --email <NEW_EMAIL> \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<USER_ID>` | Yes | User ID (UUID) |
| `-e, --email <email>` | No | New email |
| `-n, --name <name>` | No | New first name |
| `--surname <surname>` | No | New last name |

**Output code:** `UserUpdated`

### `users delete`

Delete a user by ID.

```bash
uip admin identity users delete <USER_ID> --output json
```

**Output code:** `UserDeleted`

### `users invite`

Invite users by email. Sends an invitation to join the organization.

```bash
uip admin identity users invite \
  --email "user@example.com" \
  --name "John" \
  --surname "Doe" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `-e, --email <email>` | Yes | Email address to invite |
| `-n, --name <name>` | No | First name |
| `--surname <surname>` | No | Last name |

Always include `--name` and `--surname` when the user's full name is known. Invite one user at a time.

**Output code:** `UsersInvited`

---

## Groups — `uip admin identity groups`

> **Group ID is a positional argument, not a flag.** Write `groups get <GROUP_ID>`, NOT `groups get --group-id <GROUP_ID>`. Same for `add-members`, `remove-members`, `get-members`, `update`, `delete`.

### `groups list`

List all groups in a partition.

```bash
uip admin identity groups list --output json
```

**Output code:** `GroupList`

### `groups get`

Get group details by ID.

```bash
uip admin identity groups get <GROUP_ID> --output json
```

**Output code:** `GroupDetails`

### `groups create`

Create a new group. Group names must be unique within a partition.

```bash
uip admin identity groups create "<GROUP_NAME>" --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_NAME>` | Yes | Group name |

**Output code:** `GroupCreated`

### `groups update`

Rename a group.

```bash
uip admin identity groups update <GROUP_ID> \
  --name "<NEW_NAME>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_ID>` | Yes | Group ID (UUID) |
| `-n, --name <name>` | Yes | New group name |

**Output code:** `GroupUpdated`

### `groups delete`

Delete a group. Only custom groups can be deleted — built-in groups cannot.

```bash
uip admin identity groups delete <GROUP_ID> --output json
```

**Output code:** `GroupDeleted`

### `groups get-members`

List members of a group.

```bash
uip admin identity groups get-members <GROUP_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_ID>` | Yes | Group ID (UUID) |
| `-l, --limit <number>` | No | Items to return (default: 50) |
| `--offset <number>` | No | Items to skip (default: 0) |

**Output code:** `GroupMembers`

### `groups add-members`

Add users to a group. User IDs are required — resolve them via `users list` first.

```bash
uip admin identity groups add-members <GROUP_ID> \
  --user-ids "<USER_ID_1>,<USER_ID_2>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_ID>` | Yes | Group ID (UUID) |
| `--user-ids <ids>` | Yes | Comma-separated user IDs (UUIDs) |

**Output code:** `GroupMembersAdded`

### `groups remove-members`

Remove users from a group.

```bash
uip admin identity groups remove-members <GROUP_ID> \
  --user-ids "<USER_ID>" \
  --output json
```

**Output code:** `GroupMembersRemoved`

---

## Robot Accounts — `uip admin identity robot-accounts`

> **IDs and names are positional arguments, not flags.** Write `robot-accounts get <ID>`, NOT `robot-accounts get --id <ID>`. Same for `create <NAME>`, `update <ID>`, `delete <ID>`.

### `robot-accounts list`

List robot accounts in a partition.

```bash
uip admin identity robot-accounts list --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `-s, --search <term>` | No | Search by name |
| `--order-by <field>` | No | Sort field (e.g., `Name`) |
| `--order-direction <asc\|desc>` | No | Sort direction (default: asc) |
| `-l, --limit <number>` | No | Items to return (default: 20) |
| `--offset <number>` | No | Items to skip (default: 0) |

**Output code:** `RobotAccountList`

### `robot-accounts get`

Get robot account details.

```bash
uip admin identity robot-accounts get <ROBOT_ACCOUNT_ID> --output json
```

**Output code:** `RobotAccountDetails`

### `robot-accounts create`

Create a new robot account. Names must be unique within a partition.

```bash
uip admin identity robot-accounts create "<NAME>" \
  --display-name "<DISPLAY_NAME>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<NAME>` | Yes | Robot account name (unique) |
| `--display-name <name>` | No | Display name (defaults to name) |

**Output code:** `RobotAccountCreated`

### `robot-accounts update`

Update a robot account's display name.

```bash
uip admin identity robot-accounts update <ROBOT_ACCOUNT_ID> \
  --display-name "<NEW_DISPLAY_NAME>" \
  --output json
```

**Output code:** `RobotAccountUpdated`

### `robot-accounts delete`

Delete a robot account.

```bash
uip admin identity robot-accounts delete <ROBOT_ACCOUNT_ID> --output json
```

**Output code:** `RobotAccountDeleted`

---

## External Apps — `uip admin identity external-apps`

> **IDs and names are positional arguments, not flags.** Write `external-apps get <CLIENT_ID>`, NOT `external-apps get --client-id <CLIENT_ID>`. Same for `create <NAME>`, `update <ID>`, `delete <ID>`, `generate-secret <ID>`, `delete-secret <ID>`.

### `external-apps list`

List external OAuth2 apps in a partition.

```bash
uip admin identity external-apps list --output json
```

**Output code:** `ExternalClientList`

### `external-apps get`

Get external app details including resources and scopes.

```bash
uip admin identity external-apps get <CLIENT_ID> --output json
```

**Output code:** `ExternalClientDetails`

### `external-apps create`

Create a confidential external app. A client secret is auto-generated and returned once.

```bash
uip admin identity external-apps create "<APP_NAME>" \
  --scope "OR.Folders,OR.Assets,OR.Queues" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<APP_NAME>` | Yes | App display name |
| `--scope <scopes>` | Yes | Comma-separated scope names |
| `--redirect-uri <uri>` | No | OAuth2 redirect URI |

**Output code:** `ExternalClientCreated`

Common scopes: `OR.Folders`, `OR.Assets`, `OR.Queues`, `OR.Jobs`, `OR.Machines`, `OR.Robots`, `OR.Execution`, `OR.Monitoring`.

### `external-apps update`

Update an external app. At least one field flag is required.

```bash
uip admin identity external-apps update <CLIENT_ID> \
  --name "<NEW_NAME>" \
  --scope "OR.Folders,OR.Jobs" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<CLIENT_ID>` | Yes | External app ID |
| `-n, --name <name>` | No | New display name |
| `--redirect-uri <uri>` | No | New redirect URI |
| `--scope <scopes>` | No | New comma-separated scopes (replaces existing) |

**Output code:** `ExternalClientUpdated`

### `external-apps delete`

Delete an external app.

```bash
uip admin identity external-apps delete <CLIENT_ID> --output json
```

**Output code:** `ExternalClientDeleted`

### `external-apps generate-secret`

Generate a new secret for an external app. The secret value is returned only once.

```bash
uip admin identity external-apps generate-secret <CLIENT_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<CLIENT_ID>` | Yes | External app ID |
| `--description <text>` | No | Description for the secret |
| `--expiration <date>` | No | Expiration date (ISO 8601, e.g., `2027-01-01`) |

**Output code:** `ExternalClientSecretGenerated`

### `external-apps delete-secret`

Delete a specific secret. Takes only the secret ID — no client ID needed.

```bash
uip admin identity external-apps delete-secret <SECRET_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<SECRET_ID>` | Yes | Secret ID (numeric) |

**Output code:** `ExternalClientSecretDeleted`
