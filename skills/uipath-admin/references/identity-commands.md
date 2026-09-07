# Identity CLI Command Reference

Complete reference for `uip admin` commands.

## Global usage

Run `uip login status --output json` first. Organization ID comes from the active login session.

Every command accepts `--output <format>` (`json`, `table`, `yaml`, or `plain`; default `json`) and `--login-validity <minutes>` (overrides token validity and forces refresh when the token expires within this window).

## Users — `uip admin users`

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin users list --output json` | `-s, --search <term>`; `--sort-by <field>` (for example, `UserName`, `Email`); `--sort-order <asc\|desc>` (default `asc`); `-l, --limit <number>` (default `20`); `--offset <number>` (default `0`) | `UserList` |
| `get` | `uip admin users get <USER_ID> --output json` | `<USER_ID>` required, UUID | `UserDetails` |
| `create` | `uip admin users create <USERNAME> --email <EMAIL> --output json` | `<USERNAME>` and `-e, --email <email>` required; `-n, --name <name>`; `--surname <surname>` | `UserCreated` |
| `update` | `uip admin users update <USER_ID> --email <NEW_EMAIL> --output json` | `<USER_ID>` required, UUID; at least one of `-e, --email <email>`, `-n, --name <name>`, `--surname <surname>` required | `UserUpdated` |
| `delete` | `uip admin users delete <USER_ID> --output json` | `<USER_ID>` required | `UserDeleted` |
| `invite` | `uip admin users invite --email <EMAIL> --output json` | `-e, --email <email>` required; `-n, --name <name>`; `--surname <surname>`. Always include name and surname when known; invite one user at a time. | `UsersInvited` |

## Groups — `uip admin groups`

Group IDs are positional, not flags. Run `groups get <GROUP_ID>`, not `groups get --group-id <GROUP_ID>`. This applies to `members add`, `members revoke`, `members list`, `update`, and `delete`.

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin groups list --output json` | None | `GroupList` |
| `get` | `uip admin groups get <GROUP_ID> --output json` | `<GROUP_ID>` required, UUID | `GroupDetails` |
| `create` | `uip admin groups create "<GROUP_NAME>" --output json` | `<GROUP_NAME>` required; unique within a partition | `GroupCreated` |
| `update` | `uip admin groups update <GROUP_ID> --name "<NEW_NAME>" --output json` | `<GROUP_ID>` required, UUID; `-n, --name <name>` required | `GroupUpdated` |
| `delete` | `uip admin groups delete <GROUP_ID> --output json` | Only custom groups can be deleted; built-in groups cannot | `GroupDeleted` |
| `members list` | `uip admin groups members list <GROUP_ID> --output json` | `<GROUP_ID>` required, UUID; `-l, --limit <number>` (default `50`); `--offset <number>` (default `0`) | `GroupMembers` |
| `members add` | `uip admin groups members add <GROUP_ID> --user-ids "<USER_ID_1>,<USER_ID_2>" --output json` | `<GROUP_ID>` required; `--user-ids <ids>` required, comma-separated UUIDs. Run `users list` first to resolve IDs. | `GroupMembersAdded` |
| `members revoke` | `uip admin groups members revoke <GROUP_ID> --user-ids "<USER_ID>" --output json` | `<GROUP_ID>` and `--user-ids <ids>` required | `GroupMembersRevoked` |

## Robot Accounts — `uip admin robot-accounts`

IDs and names are positional, not flags. Run `robot-accounts get <ID>`, not `robot-accounts get --id <ID>`. This applies to `create <NAME>`, `update <ID>`, and `delete <ID>`.

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin robot-accounts list --output json` | `-s, --search <term>`; `--sort-by <field>` (for example, `Name`); `--sort-order <asc\|desc>` (default `asc`); `-l, --limit <number>` (default `20`); `--offset <number>` (default `0`) | `RobotAccountList` |
| `get` | `uip admin robot-accounts get <ROBOT_ACCOUNT_ID> --output json` | ID positional and required | `RobotAccountDetails` |
| `create` | `uip admin robot-accounts create "<NAME>" --display-name "<DISPLAY_NAME>" --output json` | `<NAME>` required and unique; `--display-name <name>` optional, defaults to name | `RobotAccountCreated` |
| `update` | `uip admin robot-accounts update <ROBOT_ACCOUNT_ID> --display-name "<NEW_DISPLAY_NAME>" --output json` | ID positional; at least one field flag required; `--display-name <name>` | `RobotAccountUpdated` |
| `delete` | `uip admin robot-accounts delete <ROBOT_ACCOUNT_ID> --output json` | ID positional and required | `RobotAccountDeleted` |

## External Apps — `uip admin external-apps`

IDs and names are positional, not flags. Run `external-apps create "<APP_NAME>"`, not `external-apps create --name "<APP_NAME>"`. This applies to `get <CLIENT_ID>`, `update <ID>`, `delete <ID>`, `generate-secret <ID>`, and `delete-secret <ID>`.

Non-confidential apps support only `--user-scope`; never combine `--non-confidential` with `--app-scope`. Use confidential apps (default) for app-only scopes. `--redirect-uri` is required for `--non-confidential` apps and any app with `--user-scope`; always ask for the callback URL and do not omit it.

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin external-apps list --output json` | None | `ExternalClientList` |
| `get` | `uip admin external-apps get <CLIENT_ID> --output json` | `<CLIENT_ID>` required; returns resources, scopes, and federated credentials | `ExternalClientDetails` |
| `create` | `uip admin external-apps create "<APP_NAME>" --app-scope "<SCOPES>" --output json` | `<APP_NAME>` required; at least one of `--app-scope <scopes>`, `--user-scope <scopes>`; `--scope <scopes>` deprecated alias for `--app-scope`; `--redirect-uri <uri>` optional unless required above, comma-separated; `--non-confidential`; `--no-secret`. Confidential by default; generates a client secret. | `ExternalClientCreated` |
| `update` | `uip admin external-apps update <CLIENT_ID> --name "<NEW_NAME>" --app-scope "<SCOPES>" --output json` | `<CLIENT_ID>` required; at least one field flag required; `-n, --name <name>`; `--redirect-uri <uri>`; `--app-scope <scopes>` and `--user-scope <scopes>` replace existing scopes; `--scope <scopes>` deprecated alias for `--app-scope` | `ExternalClientUpdated` |
| `delete` | `uip admin external-apps delete <CLIENT_ID> --output json` | `<CLIENT_ID>` required | `ExternalClientDeleted` |
| `generate-secret` | `uip admin external-apps generate-secret <CLIENT_ID> --output json` | `<CLIENT_ID>` required; `--description <text>`; `--expiration <date>` ISO 8601 | `ExternalClientSecretGenerated` |
| `delete-secret` | `uip admin external-apps delete-secret <SECRET_ID> --output json` | `<SECRET_ID>` required, numeric; takes no client ID | `ExternalClientSecretDeleted` |

### Federated credentials

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin external-apps federated-credentials list <CLIENT_ID> --output json` | `<CLIENT_ID>` required | `FederatedCredentialList` |
| `get` | `uip admin external-apps federated-credentials get <CLIENT_ID> <CREDENTIAL_ID> --output json` | Both IDs required | `FederatedCredentialDetails` |
| `create` | `uip admin external-apps federated-credentials create <CLIENT_ID> --name "<NAME>" --issuer "<ISSUER>" --audience "<AUDIENCE>" --subject "<SUBJECT>" --output json` | `<CLIENT_ID>`; `-n, --name <name>`; `--issuer <url>`; `--audience <audience>`; and `--subject <subject>` required; `--description <text>` optional. Maps an external identity to the app. | `FederatedCredentialCreated` |
| `update` | `uip admin external-apps federated-credentials update <CLIENT_ID> <CREDENTIAL_ID> --name "<NAME>" --issuer "<ISSUER>" --audience "<AUDIENCE>" --subject "<SUBJECT>" --output json` | All fields required; full replace | `FederatedCredentialUpdated` |
| `delete` | `uip admin external-apps federated-credentials delete <CLIENT_ID> <CREDENTIAL_ID> --output json` | Both IDs required | `FederatedCredentialDeleted` |

## Personal Access Tokens — `uip admin pat`

For `revoke` and `regenerate`, token ID is positional. Run `pat revoke <TOKEN_ID>`, not `pat revoke --token-id <TOKEN_ID>`.

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `list` | `uip admin pat list --output json` | Lists your tokens by default; `--scope <scope>`: `all` lists all organization tokens (admin only); `--search <term>` filters by user and implies `--scope all`; `-l, --limit <number>` (default `50`); `--offset <number>` (default `0`) | `PatList` |
| `create` | `uip admin pat create --description "<DESCRIPTION>" --expiration "<DATE>" --scope "<SCOPES>" --output json` | `--description <text>`, `--expiration <date>`, and `--scope <scopes>` required; date ISO 8601 `YYYY-MM-DD`; maximum 360 days (organization default); scopes comma-separated | `PatCreated` |
| `revoke` | `uip admin pat revoke <TOKEN_ID> --output json` | `<TOKEN_ID>` required and positional | `PatRevoked` |
| `regenerate` | `uip admin pat regenerate <TOKEN_ID> --expiration "<DATE>" --output json` | `<TOKEN_ID>` positional UUID; `--expiration <date>` required, ISO 8601 `YYYY-MM-DD` | `PatRegenerated` |

## SMTP — `uip admin smtp`

| Command | Usage | Arguments and flags | Output |
|---|---|---|---|
| `get` | `uip admin smtp get --output json` | None | `SmtpSettings` |
| `update` | `uip admin smtp update --host "<HOST>" --port <PORT> --enable-ssl "<true\|false>" --username "<USERNAME>" --password "<PASSWORD>" --from-address "<EMAIL>" --output json` | At least one required: `--host <host>`; `--port <port>` (1–65535); `--username <username>`; `--password <password>`; `--domain <domain>`; `--enable-ssl <value>` (`true`/`false`); `--use-default-credentials <value>` (`true`/`false`); `--from-address <email>`; `--from-display-name <name>`; `--connection-timeout <ms>` (1–300000) | `SmtpSettingsUpdated` |
| `delete` | `uip admin smtp delete --output json` | Deletes all settings and reverts to platform defaults | `SmtpSettingsDeleted` |
| `test` | `uip admin smtp test --recipient "<EMAIL>" --output json` | `--recipient <email>` required; `--host <host>`, `--port <port>`, `--password <password>`, and all other SMTP update flags optional. Uses saved settings by default; custom settings are test-only and require `--password`. | `SmtpTestSent` |

## Scopes — `uip admin scopes`

Run `uip admin scopes list --output json` to list available OAuth2 scopes grouped by resource for external apps and PATs. Output: `ScopesList`.

## Output etiquette after identity mutations

Apply these steps to `users create / update / invite / delete`, `groups create / update / delete`, `groups members add / revoke`, `robot-accounts create / update / delete`, and `external-apps create / update / delete / generate-secret / delete-secret`:

1. Show the command result, success or failure.
2. For creates, display the new resource ID.
3. For `external-apps create` and `generate-secret`, highlight the secret value and warn the user to save it; it appears only once in the creation response.
4. Offer logical next steps:
   - After creating a robot account: “Assign to a group for role-based access?”
   - After creating an external app: “Generate an additional secret?”
   - After inviting a user: “Check user list to see when they accept?”
