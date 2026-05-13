# Identity CLI Command Reference

Complete reference for all `uip admin` commands.

## Global Flags

Every command accepts these flags (omitted from per-command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` (default: json) |
| `--login-validity <minutes>` | Override token validity — forces refresh if token expires within this window |

Organization ID is resolved automatically from the active login session.

## Prerequisites

```bash
uip login status --output json
```

---

## Users — `uip admin users`

### `users list`

List users in a partition.

```bash
uip admin users list --output json
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
uip admin users get <USER_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<USER_ID>` | Yes | User ID (UUID) |

**Output code:** `UserDetails`

### `users create`

Create a new user.

```bash
uip admin users create <USERNAME> \
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
uip admin users update <USER_ID> \
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
uip admin users delete <USER_ID> --output json
```

**Output code:** `UserDeleted`

### `users invite`

Invite users by email. Sends an invitation to join the organization.

```bash
uip admin users invite \
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

## Groups — `uip admin groups`

> **Group ID is a positional argument, not a flag.** Write `groups get <GROUP_ID>`, NOT `groups get --group-id <GROUP_ID>`. Same for `members add`, `members revoke`, `members list`, `update`, `delete`.

### `groups list`

List all groups in a partition.

```bash
uip admin groups list --output json
```

**Output code:** `GroupList`

### `groups get`

Get group details by ID.

```bash
uip admin groups get <GROUP_ID> --output json
```

**Output code:** `GroupDetails`

### `groups create`

Create a new group. Group names must be unique within a partition.

```bash
uip admin groups create "<GROUP_NAME>" --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_NAME>` | Yes | Group name |

**Output code:** `GroupCreated`

### `groups update`

Rename a group.

```bash
uip admin groups update <GROUP_ID> \
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
uip admin groups delete <GROUP_ID> --output json
```

**Output code:** `GroupDeleted`

### `groups members list`

List members of a group.

```bash
uip admin groups members list <GROUP_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_ID>` | Yes | Group ID (UUID) |
| `-l, --limit <number>` | No | Items to return (default: 50) |
| `--offset <number>` | No | Items to skip (default: 0) |

**Output code:** `GroupMembers`

### `groups members add`

Add users to a group. User IDs are required — resolve them via `users list` first.

```bash
uip admin groups members add <GROUP_ID> \
  --user-ids "<USER_ID_1>,<USER_ID_2>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<GROUP_ID>` | Yes | Group ID (UUID) |
| `--user-ids <ids>` | Yes | Comma-separated user IDs (UUIDs) |

**Output code:** `GroupMembersAdded`

### `groups members revoke`

Remove users from a group.

```bash
uip admin groups members revoke <GROUP_ID> \
  --user-ids "<USER_ID>" \
  --output json
```

**Output code:** `GroupMembersRevoked`

---

## Robot Accounts — `uip admin robot-accounts`

> **IDs and names are positional arguments, not flags.** Write `robot-accounts get <ID>`, NOT `robot-accounts get --id <ID>`. Same for `create <NAME>`, `update <ID>`, `delete <ID>`.

### `robot-accounts list`

List robot accounts in a partition.

```bash
uip admin robot-accounts list --output json
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
uip admin robot-accounts get <ROBOT_ACCOUNT_ID> --output json
```

**Output code:** `RobotAccountDetails`

### `robot-accounts create`

Create a new robot account. Names must be unique within a partition.

```bash
uip admin robot-accounts create "<NAME>" \
  --display-name "<DISPLAY_NAME>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<NAME>` | Yes | Robot account name (unique) |
| `--display-name <name>` | No | Display name (defaults to name) |

**Output code:** `RobotAccountCreated`

### `robot-accounts update`

Update a robot account. At least one field flag is required.

```bash
uip admin robot-accounts update <ROBOT_ACCOUNT_ID> \
  --display-name "<NEW_DISPLAY_NAME>" \
  --output json
```

**Output code:** `RobotAccountUpdated`

### `robot-accounts delete`

Delete a robot account.

```bash
uip admin robot-accounts delete <ROBOT_ACCOUNT_ID> --output json
```

**Output code:** `RobotAccountDeleted`

---

## External Apps — `uip admin external-apps`

> **IDs and names are positional arguments, not flags.** Write `external-apps get <CLIENT_ID>`, NOT `external-apps get --client-id <CLIENT_ID>`. Same for `create <NAME>`, `update <ID>`, `delete <ID>`, `generate-secret <ID>`, `delete-secret <ID>`.

### `external-apps list`

List external OAuth2 apps in a partition.

```bash
uip admin external-apps list --output json
```

**Output code:** `ExternalClientList`

### `external-apps get`

Get external app details including resources, scopes, and federated credentials.

```bash
uip admin external-apps get <CLIENT_ID> --output json
```

**Output code:** `ExternalClientDetails`

### `external-apps create`

Create an external app. Confidential by default (generates client secret). Use `--non-confidential` for public clients.

```bash
uip admin external-apps create "<APP_NAME>" \
  --app-scope "OR.Folders,OR.Assets,OR.Queues" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<APP_NAME>` | Yes | App display name |
| `--app-scope <scopes>` | Conditional | Comma-separated application scopes (at least one scope type required) |
| `--user-scope <scopes>` | Conditional | Comma-separated user (delegated) scopes |
| `--scope <scopes>` | No | Deprecated alias for `--app-scope` |
| `--redirect-uri <uri>` | Conditional | OAuth2 redirect URI(s), comma-separated. Required with `--user-scope` or `--non-confidential` |
| `--non-confidential` | No | Create public client (no secret) |
| `--no-secret` | No | Skip generating secret on creation |

**Output code:** `ExternalClientCreated`

### `external-apps update`

Update an external app. At least one field flag is required.

```bash
uip admin external-apps update <CLIENT_ID> \
  --name "<NEW_NAME>" \
  --app-scope "OR.Folders,OR.Jobs" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<CLIENT_ID>` | Yes | External app ID |
| `-n, --name <name>` | No | New display name |
| `--redirect-uri <uri>` | No | New redirect URI(s) |
| `--app-scope <scopes>` | No | New application scopes (replaces existing) |
| `--user-scope <scopes>` | No | New user scopes (replaces existing) |
| `--scope <scopes>` | No | Deprecated alias for `--app-scope` |

**Output code:** `ExternalClientUpdated`

### `external-apps delete`

Delete an external app.

```bash
uip admin external-apps delete <CLIENT_ID> --output json
```

**Output code:** `ExternalClientDeleted`

### `external-apps generate-secret`

Generate a new secret for an external app. Value returned only once.

```bash
uip admin external-apps generate-secret <CLIENT_ID> --output json
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
uip admin external-apps delete-secret <SECRET_ID> --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<SECRET_ID>` | Yes | Secret ID (numeric) |

**Output code:** `ExternalClientSecretDeleted`

### `external-apps federated-credentials list`

List federated credentials for an external app.

```bash
uip admin external-apps federated-credentials list <CLIENT_ID> --output json
```

**Output code:** `FederatedCredentialList`

### `external-apps federated-credentials get`

Get a federated credential by ID.

```bash
uip admin external-apps federated-credentials get <CLIENT_ID> <CREDENTIAL_ID> --output json
```

**Output code:** `FederatedCredentialDetails`

### `external-apps federated-credentials create`

Create a federated credential. Maps an external identity (e.g., GitHub Actions OIDC) to this app.

```bash
uip admin external-apps federated-credentials create <CLIENT_ID> \
  --name "GitHub Actions" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "api://AzureADTokenExchange" \
  --subject "repo:myorg/myrepo:ref:refs/heads/main" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<CLIENT_ID>` | Yes | External app ID |
| `-n, --name <name>` | Yes | Credential name |
| `--issuer <url>` | Yes | Token issuer URL |
| `--audience <audience>` | Yes | Expected audience claim |
| `--subject <subject>` | Yes | Expected subject claim |
| `--description <text>` | No | Description |

**Output code:** `FederatedCredentialCreated`

### `external-apps federated-credentials update`

Update a federated credential. All fields required (full replace).

```bash
uip admin external-apps federated-credentials update <CLIENT_ID> <CREDENTIAL_ID> \
  --name "Updated Name" \
  --issuer "https://token.actions.githubusercontent.com" \
  --audience "api://AzureADTokenExchange" \
  --subject "repo:myorg/myrepo:ref:refs/heads/release" \
  --output json
```

**Output code:** `FederatedCredentialUpdated`

### `external-apps federated-credentials delete`

Delete a federated credential.

```bash
uip admin external-apps federated-credentials delete <CLIENT_ID> <CREDENTIAL_ID> --output json
```

**Output code:** `FederatedCredentialDeleted`

---

## Personal Access Tokens — `uip admin pat`

> **Token ID is a positional argument for `revoke` and `regenerate`.** Write `pat revoke <TOKEN_ID>`, NOT `pat revoke --token-id <TOKEN_ID>`.

### `pat list`

List personal access tokens. By default lists your own. Use `--scope all` for all org tokens (admin only).

```bash
uip admin pat list --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--scope <scope>` | No | `all` to list all org tokens (admin only) |
| `--search <term>` | No | Filter by user search term (implies `--scope all`) |
| `-l, --limit <number>` | No | Items to return (default: 50) |
| `--offset <number>` | No | Items to skip (default: 0) |

**Output code:** `PatList`

### `pat create`

Create a personal access token. Token value returned only once.

```bash
uip admin pat create \
  --description "CI/CD pipeline token" \
  --expiration "2027-01-15" \
  --scopes "OR.Folders.Read,OR.Jobs.Read" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--description <text>` | Yes | Token description |
| `--expiration <date>` | Yes | Expiration date (ISO 8601: `YYYY-MM-DD`) |
| `--scopes <scopes>` | Yes | Comma-separated scope names |

**Output code:** `PatCreated`

### `pat revoke`

Revoke a personal access token.

```bash
uip admin pat revoke <TOKEN_ID> --output json
```

**Output code:** `PatRevoked`

### `pat regenerate`

Regenerate a token with new expiration. New token value returned only once.

```bash
uip admin pat regenerate <TOKEN_ID> --expiration "2028-01-15" --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<TOKEN_ID>` | Yes | Token ID (UUID) |
| `--expiration <date>` | Yes | New expiration date (ISO 8601: `YYYY-MM-DD`) |

**Output code:** `PatRegenerated`

---

## SMTP — `uip admin smtp`

### `smtp get`

Get current SMTP settings.

```bash
uip admin smtp get --output json
```

**Output code:** `SmtpSettings`

### `smtp update`

Update SMTP settings. At least one field required.

```bash
uip admin smtp update \
  --host "smtp.example.com" \
  --port 587 \
  --enable-ssl "true" \
  --username "smtp-user" \
  --password "smtp-pass" \
  --from-address "noreply@example.com" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--host <host>` | No | SMTP server hostname |
| `--port <port>` | No | SMTP server port (1-65535) |
| `--username <username>` | No | SMTP auth username |
| `--password <password>` | No | SMTP auth password |
| `--domain <domain>` | No | SMTP auth domain |
| `--enable-ssl <value>` | No | Enable SSL/TLS: `true` or `false` |
| `--use-default-credentials <value>` | No | Use Windows credentials: `true` or `false` |
| `--from-address <email>` | No | Sender email address |
| `--from-display-name <name>` | No | Sender display name |
| `--connection-timeout <ms>` | No | Connection timeout in milliseconds (1-300000) |

**Output code:** `SmtpSettingsUpdated`

### `smtp delete`

Delete all SMTP settings. Platform emails will stop working.

```bash
uip admin smtp delete --output json
```

**Output code:** `SmtpSettingsDeleted`

### `smtp test`

Test SMTP by sending a test email. Uses saved settings by default. Pass SMTP options to test custom settings without saving (requires `--password` when using custom settings).

```bash
uip admin smtp test --recipient "admin@example.com" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--recipient <email>` | Yes | Email address to send test to |
| `--host <host>` | No | Custom SMTP host (test only) |
| `--port <port>` | No | Custom SMTP port (test only) |
| `--password <password>` | Conditional | Required when using custom settings |
| *(other SMTP flags)* | No | Same as `smtp update` — used for testing only |

**Output code:** `SmtpTestSent`

---

## Scopes — `uip admin scopes`

### `scopes list`

List all available OAuth2 scopes grouped by resource. Use to discover valid scope names for external apps and PATs.

```bash
uip admin scopes list --output json
```

**Output code:** `ScopesList`
