# Connections

Connections are authenticated connector sessions that store credentials and tokens and can be shared within a folder.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown below.

---

## Response Fields

| Field | Show to user? | Description |
|---|---|---|
| **`Name`** | **Yes** | Display name and primary user-facing identifier. |
| **`State`** | **Yes** | `Enabled` or another status; only Enabled connections can be used. |
| **`IsDefault`** | **Yes** | `Yes` or `No`; recommend the default, but let the user confirm. |
| **`Owner`** | **Yes** | Creator email. |
| **`Folder`** | **Yes** | Folder name. |
| `ConnectorName` | **Yes** | Human-readable connector name. |
| `ByoaConnection` | **Yes** | `Yes` or `No`; BYOA means the customer registered the external OAuth app and is required by some webhook triggers. |
| `Id` | Internal | Connection UUID; use only in `--connection-id`, never show it. |
| `ConnectorKey` | Internal | Connector key; use only in CLI arguments. |
| `FolderKey` | Internal | Folder UUID; use only in `--folder-key`, never show it. |
| `ElementInstanceId` | Internal | Numeric instance ID; use only in `--element-instance-id` for `uip is webhooks config`. |

---

## Command Syntax and Discovery

Pass `<connector-key>` positionally and always use `--all-folders` for discovery:

```bash
uip is connections list "uipath-salesforce-slack" --all-folders --output json
```

Do not use the nonexistent `--connector-key` flag:

```bash
uip is connections list --connector-key "uipath-salesforce-slack"
```

If the call reports "connector not found" or unexpectedly returns empty, look up the key:

```bash
uip is connectors list --filter "<vendor>" --output json
```

Keys are source-prefixed: `uipath-<vendor>-<service>` for catalog connectors and `custom-entity-*` for tenant-built connectors. See [connectors.md — Connector Disambiguation](connectors.md#connector-disambiguation).

Always pass `--all-folders` when discovering connections; otherwise search only the active folder. After selection, retain `FolderKey` for downstream binding; do not pass `--folder-key` during discovery.

`--all-folders` works with or without positional `<connector-key>` and is mutually exclusive with `--folder` / `--folder-key`; conflicting flags fail with `Result: Failure`, `Message: "Conflicting folder flags..."`, exit code 1.

Target a known folder explicitly:

```bash
uip is connections list "<connector-key>" --folder "<folder-name-or-key>" --output json
```

Enumerate folders individually:

```bash
uip or folders list --output json
# → for each folder, call:
uip is connections list "<connector-key>" --folder "<folder-name-or-key>" --output json
```

If a connection in the personal workspace is invisible, re-list with `--folder` set to that workspace before creating one.

---

## Selecting a Connection

### Connector-Specific Overrides

Check overrides before auto-selection; a matching override supersedes auto-selection.

| Connector key | Applies when | Override action | Detail |
|---|---|---|---|
| `uipath-microsoft-teams` | `send-bot-*` activity node types | Ask the user; warn that bot scope is required. | [uipath-microsoft-teams.md → Connection Selection Override](connector-overrides/uipath-microsoft-teams.md#connection-selection-override) |
| `uipath-salesforce-slack` | Webhook trigger node types, excluding `button-clicked` | Ask the user; filter `--byoa` from the start. | [uipath-salesforce-slack.md → Connection Selection Override](connector-overrides/uipath-salesforce-slack.md#connection-selection-override) |

To add an override, see [connector-overrides/README.md](connector-overrides/README.md).

### Auto-Selection

Auto-select without prompting only when all three conditions hold:

- `IsDefault: Yes`
- `State: Enabled`
- `Folder` is the user's personal workspace

Detect the personal workspace once per session:

```bash
uip or folders list --all --output json
# → Data: [{ Name, Key, Path, Description, Type, ParentKey }]
# Filter entries where Type == "Personal"
```

Match `connection.FolderKey` to the personal workspace `Key`. If there are multiple personal workspaces or no match, use the presentation flow. Ping every selected connection, including auto-selected ones.

### Native Connectors

1. Run:
   ```bash
   uip is connections list "<connector-key>" --all-folders --output json
   ```
2. Present all enabled connections by **Name, Owner, and Folder**, never UUIDs. Recommend the enabled default (`IsDefault: Yes`, `State: Enabled`) and let the user confirm; confirm even when there is one enabled connection.
3. Ping every selected connection:
   ```bash
   uip is connections ping "<connection-id>" --output json
   ```
4. If listing or pinging says the connection is not enabled, prompt the user to re-authenticate with `is connections edit <id>`, then re-ping.
5. If step 1 is empty, bypass the cache:
   ```bash
   uip is connections list "<connector-key>" --all-folders --refresh --output json
   ```
   If still empty, prompt the user to create one:
   ```bash
   uip is connections create "<connector-key>"
   ```

### BYOA Connections (Webhook Triggers)

BYOA requirements are per event object, not per connector; read `byoaConnection` from `triggers objects`.

1. Run:
   ```bash
   uip is connections list "<connector-key>" --all-folders --output json
   ```
   Get any enabled connection for the next call.
2. Query the event:
   ```bash
   uip is triggers objects "<connector-key>" "<OPERATION>" \
     --connection-id "<id>" --output json
   ```
3. If `byoaConnection: true`, do not use the step-1 connection. Filter BYOA across folders:
   ```bash
   uip is connections list "<connector-key>" --byoa --all-folders --output json
   ```
   If empty, retry with cache bypass:
   ```bash
   uip is connections list "<connector-key>" --byoa --all-folders --refresh --output json
   ```
   If still empty, stop and tell the user: "This trigger requires a BYOA connection for `<connector-key>`. None found. Create one in the Integration Service portal or with `uip is connections create "<connector-key>"`, then re-run."
4. If `byoaConnection: false`, use the step-1 connection and ping it:
   ```bash
   uip is connections ping "<id>" --output json
   ```

Surface connector-specific OAuth-app instructions from `triggers objects` `design.textBlocks` verbatim; do not invent service-specific guidance. For webhook URL retrieval, see [triggers.md — Webhook URL Retrieval](triggers.md#webhook-url-retrieval).

### HTTP Fallback

1. List connections for `uipath-uipath-http`.
2. Find names containing the target vendor by case-insensitive substring match.
3. Present matches and let the user choose if there are multiple.
4. If none match, present all HTTP connections and ask the user to choose or offer to create one.

Name matching is best-effort; if names do not follow vendor conventions, present all HTTP connections.

---

## Identifying a JDBC Connection's Target DB

For `uipath-uipath-jdbc` ("Database Hub"), `connections list` hides `jdbcUrl` and `driverClass`; infer only from `connection.name`, case-insensitively, and say "likely <DB>", never "is <DB>":

| DB | Name substrings |
|---|---|
| Snowflake | `snowflake`, `sf` |
| Databricks | `databricks`, `dbx` |
| Postgres | `postgres`, `postgresql`, `pg` |
| MySQL | `mysql` |
| SQL Server | `sqlserver`, `mssql` |
| Oracle | `oracle` |
| Redshift | `redshift` |
| BigQuery | `bigquery`, `bq` |

An explicitly named connection overrides name matching and must be bound directly. Used by [connectors.md — JDBC Gateway](connectors.md#jdbc-gateway--database-sql-intent).

---

## Getting a Connection's Vendor Base URL

Run this for the exact vendor base URL used by proxied calls, including raw `http-request` and Managed HTTP Request in connector mode. Manual-mode invocations do not use it; the connection must be Enabled:

```bash
uip is connections base-url "<connection-id>" --output json
# → { "Result": "Success", "Code": "ConnectionBaseUrl",
#     "Data": { "ConnectionId": "<id>", "BaseUrl": "https://..." } }
```

Use the returned `BaseUrl` when composing a relative `url` for `http-request` or Managed HTTP Request in connector mode. See [http-request.md](http-request.md).

| Connector | Returned `BaseUrl` |
|---|---|
| `uipath-atlassian-jira` | `https://api.atlassian.com/ex/jira/<site-id>/rest/api/2` |
| `uipath-microsoft-outlook365` | `https://graph.microsoft.com/v1.0` |
| `uipath-uipath-marketo` | `https://<account>.mktorest.com/rest` |

---

## Scope-Related Errors

An `Enabled` connection can lack optional OAuth scopes. Suspect this when execute returns **403 Forbidden** or a vendor-specific insufficient-permissions error while ping succeeds and another broader-scope connection works.

1. Tell the user the connection may need broader OAuth scopes.
2. Re-authorize:
   ```bash
   uip is connections edit <connection-id>
   ```
3. Ping again, then retry the operation.
