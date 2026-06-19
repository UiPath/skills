# Connections

Connections are authenticated sessions for a specific connector. They store credentials and tokens, and can be shared across automations within a folder.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Response Fields

| Field | Show to user? | Description |
|---|---|---|
| **`Name`** | **Yes** | Display name — always use this as the primary identifier when presenting to the user (e.g., "Salesforce Prod", "bai.li") |
| **`State`** | **Yes** | `Enabled` or other status. Only Enabled connections can be used. |
| **`IsDefault`** | **Yes** | `Yes` or `No`. Recommend the default connection but always let the user confirm. |
| **`Owner`** | **Yes** | Who created the connection (email) |
| **`Folder`** | **Yes** | Folder name this connection belongs to (e.g., "Shared", "Personal") |
| `ConnectorName` | **Yes** | Human-readable connector name (e.g., "Slack", "Salesforce") |
| `ByoaConnection` | **Yes** | `Yes` or `No`. BYOA (Bring Your Own Account) connection — customer registered their own OAuth app with the external service. Required for some webhook triggers. |
| `Id` | Internal | Connection UUID — use only in `--connection-id` CLI args, never show to user |
| `ConnectorKey` | Internal | Connector key — use only in CLI args |
| `FolderKey` | Internal | Folder UUID — use only in `--folder-key` CLI args, never show to user |
| `ElementInstanceId` | Internal | Numeric instance ID — use only in `--element-instance-id` for `uip is webhooks config` |

---

## Command Syntax

`<connector-key>` is a **positional argument**, not a flag:

```bash
# Correct — always pass --all-folders for discovery (see Folder Scoping below)
uip is connections list "uipath-salesforce-slack" --all-folders --output json

# WRONG — there is no --connector-key flag
uip is connections list --connector-key "uipath-salesforce-slack"
```

**Always pass a connector key.** Running `uip is connections list` with no arg returns a noisy, paginated list across every connector in the tenant and is not a useful survey step.

**Wrong key?** If the call errors with "connector not found" or returns empty unexpectedly, look up the correct key:

```bash
uip is connectors list --filter "<vendor>" --output json
```

Connector keys are prefixed by source — `uipath-<vendor>-<service>` for catalog connectors, `custom-entity-*` for tenant-built. See [connectors.md — Connector Disambiguation](connectors.md#connector-disambiguation) for the full classification ladder.

---

## Selecting a Connection

### Connector-Specific Overrides

**Before applying the auto-select rule below, check this table.** If the connector key (and node-type pattern, where listed) matches an entry, read the linked file and follow its rules. Override supersedes the auto-select rule.

| Connector key | Applies when | Override action | Detail |
|---|---|---|---|
| `uipath-microsoft-teams` | `send-bot-*` activity node types | Ask user; warn that bot scope is required | [uipath-microsoft-teams.md → Connection Selection Override](connector-overrides/uipath-microsoft-teams.md#connection-selection-override) |
| `uipath-salesforce-slack` | Webhook trigger node types (allow-list — excludes `button-clicked`) | Ask user; filter `--byoa` from the start | [uipath-salesforce-slack.md → Connection Selection Override](connector-overrides/uipath-salesforce-slack.md#connection-selection-override) |

To add a new override, see [connector-overrides/README.md](connector-overrides/README.md).

---

**Auto-select rule (no prompt) — when all three hold:**

- `IsDefault: Yes`
- `State: Enabled`
- `Folder` is the user's personal workspace

Bind silently and skip the presentation steps below.

Detect the user's personal workspace once per session — list all folders and filter for the personal type:

```bash
uip or folders list --all --output json
# → Data: [{ Name, Key, Path, Description, Type, ParentKey }]
# Filter entries where Type == "Personal"
```

Match `connection.FolderKey` against the personal workspace's `Key`. If the call returns multiple personal workspaces (admin tenant) or no match, fall through to the presentation flow.

**Otherwise — present connections to the user.** Recommend the default but let the user confirm.

### Folder Scoping (`--all-folders`)

**Always pass `--all-folders` when discovering connections.** Without it, the CLI returns the active folder only — producing false "no connections found" results when the connection exists in another folder you can see. After the user picks a connection, capture its `FolderKey` from the response for downstream binding; do not pass `--folder-key` during discovery.

- `--all-folders`: spans every folder you have access to. Works with or without a `<connector-key>` positional.
- **Mutually exclusive with `--folder` / `--folder-key`** — passing both fails with `Result: Failure`, `Message: "Conflicting folder flags..."`, exit code 1.

### For Native Connectors

1. List connections for the connector across all folders:

   ```bash
   uip is connections list "<connector-key>" --all-folders --output json
   ```

2. Present all enabled connections to the user using **Name, Owner, and Folder** (never UUIDs), **recommending** the default (`IsDefault: Yes`, `State: Enabled`):
   - "I found these connections: 1) **Salesforce Prod** by user@example.com (default, enabled, Shared folder) ← recommended 2) **Salesforce Dev** by admin@example.com (enabled, Shared folder). Which should I use?"
3. If only one enabled connection exists, still confirm: "I found connection **<Name>** by <Owner> in **<Folder>** folder (default, enabled). Should I use this one?"
4. **Verify health — ping after every selection** (auto-select and user-confirmed alike):

   ```bash
   uip is connections ping "<connection-id>" --output json
   ```

   If ping fails or reports not Enabled, follow step 5.

5. If not enabled (from list `State` or ping result) → prompt user to re-authenticate via `is connections edit <id>`, then re-ping.

6. **No connections in step 1 — bypass the cache before concluding none exist:**
   1. Retry with `--refresh`:
      ```bash
      uip is connections list "<connector-key>" --all-folders --refresh --output json
      ```
   2. If still empty, prompt user to create one via `uip is connections create "<connector-key>"`.

### For BYOA Connections (Webhook Triggers)

BYOA (Bring Your Own Account) connections use an OAuth app the customer registered with the external service (e.g., a Slack app they own). Some webhook triggers require BYOA; many do not. **The requirement is per event object, not per connector** — read it from the `triggers objects` response.

**Decision flow:**

1. Get any enabled connection — needed only as `--connection-id` for the next call:

   ```bash
   uip is connections list "<connector-key>" --all-folders --output json
   ```

2. Query trigger objects and read the `byoaConnection` flag for the matching event:

   ```bash
   uip is triggers objects "<connector-key>" "<OPERATION>" \
     --connection-id "<id>" --output json
   ```

3. **If `byoaConnection: true`** — the connection from step 1 is not usable. Filter to BYOA across all folders:

   ```bash
   uip is connections list "<connector-key>" --byoa --all-folders --output json
   ```

   If empty, retry with `--refresh` to bypass the CLI cache:

   ```bash
   uip is connections list "<connector-key>" --byoa --all-folders --refresh --output json
   ```

   If still empty, **stop and tell the user**: "This trigger requires a BYOA connection for `<connector-key>`. None found. Create one in the Integration Service portal or with `uip is connections create "<connector-key>"`, then re-run."

4. **If `byoaConnection: false`** — use the connection from step 1. Verify health with `uip is connections ping "<id>" --output json`.

> Connector-specific OAuth-app setup instructions (e.g., what permissions a Slack app needs) come from the trigger's `design.textBlocks` field in the `triggers objects` response. Surface that text to the user verbatim — do not invent service-specific guidance.

For webhook URL retrieval after the trigger is configured, see [triggers.md — Webhook URL Retrieval](triggers.md#webhook-url-retrieval).

### For HTTP Fallback

1. List connections for `uipath-uipath-http`
2. Look for a connection whose **Name** contains the target vendor (case-insensitive substring match, e.g., "Apify" matches "Apify", "Apify - Prod", "My Apify Connection")
3. Present matches to the user. If multiple matches → let them choose.
4. If no match → present all existing HTTP connections and ask the user to choose, or offer to create a new one

> **Note:** Name-based matching is best-effort. If connection names don't follow vendor naming conventions, present all HTTP connections to the user.

---

## Identifying a JDBC Connection's Target DB

For the JDBC gateway connector (`uipath-uipath-jdbc`, "Database Hub"), `connections list` does **not** expose `jdbcUrl` or `driverClass` — config is intentionally hidden. The only signal for "what DB does this JDBC connection point to?" is the connection **`name`**.

Match case-insensitively (weak signal — surface as "likely &lt;DB&gt;", never "is &lt;DB&gt;"):

| DB | Substrings in `connection.name` |
|---|---|
| Snowflake | `snowflake`, `sf` |
| Databricks | `databricks`, `dbx` |
| Postgres | `postgres`, `postgresql`, `pg` |
| MySQL | `mysql` |
| SQL Server | `sqlserver`, `mssql` |
| Oracle | `oracle` |
| Redshift | `redshift` |
| BigQuery | `bigquery`, `bq` |

If the user explicitly named a connection in their prompt (e.g. "use the `pat_databricks` connection"), that overrides name-matching — bind it directly.

Used by the [connectors.md — JDBC Gateway](connectors.md#jdbc-gateway--database-sql-intent) decision matrix.

---

## Getting a Connection's Vendor Base URL

`uip is connections base-url <connection-id>` returns the exact vendor base URL the connection uses for proxied calls (e.g., raw `http-request` calls, Managed HTTP Request in connector mode). Manual-mode invocations don't use it. The connection must be Enabled.

```bash
uip is connections base-url "<connection-id>" --output json
# → { "Result": "Success", "Code": "ConnectionBaseUrl",
#     "Data": { "ConnectionId": "<id>", "BaseUrl": "https://..." } }
```

Examples across connectors:

| Connector | Returned `BaseUrl` |
|---|---|
| `uipath-atlassian-jira` | `https://api.atlassian.com/ex/jira/<site-id>/rest/api/2` |
| `uipath-microsoft-outlook365` | `https://graph.microsoft.com/v1.0` |
| `uipath-uipath-marketo` | `https://<account>.mktorest.com/rest` |

Use this whenever you need to compose a relative `url` for `http-request` or Managed HTTP Request in connector mode. See [http-request.md](http-request.md).

---

## Scope-Related Errors

A connection can be `Enabled` but lack optional OAuth scopes needed for specific activities. This typically surfaces as a **403 Forbidden** error during execute.

**Symptoms:**
- Connection pings successfully (`State: Enabled`)
- Execute fails with 403 or a vendor-specific "insufficient permissions" error
- The same operation works with a different connection that has broader scopes

**Recovery:**
1. Inform the user that the connection may need broader OAuth scopes for this activity
2. Re-authorize with broader scopes: `uip is connections edit <connection-id>`
3. After re-auth, ping again to verify, then retry the operation
