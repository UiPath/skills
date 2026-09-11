# Connectors

Connectors are pre-built integrations to external applications. Each has a unique key (for example, `uipath-salesforce-sfdc` or `uipath-servicenow-servicenow`) and contains authenticated **connections**, pre-built **activities**, and **resources** with CRUD operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns appear below.

## Response Fields

| Field | Show to user? | Description |
|---|---|---|
| **`Name`** | **Yes** | Display name; always show it (for example, "Salesforce" or "Slack"). |
| **`Key`** | **Yes** | Unique key for subsequent commands; also show it because it is human-readable (for example, `uipath-salesforce-sfdc`). |
| `Active` | **Yes** | Whether the connector is active. |
| `DapCompatible` | Optional | Whether it supports Data Access Policy. |
| `Id` | Internal | Connector UUID; never show it. |

## HTTP Connector Fallback

When no native connector exists, or when the vendor requires a custom/internal REST API, use `uipath-uipath-http`. Its connection stores authentication configuration (API keys, OAuth tokens, and base URL), and its resource is `http-request`.

Run:

```bash
# Search for vendor → not found → fall back to HTTP connector
uip is connectors list --filter "apify" --output json
# → No connectors found

# List HTTP connections and look for one named after the vendor
uip is connections list "uipath-uipath-http" --output json
```

Run:

```bash
uip is resources run create "uipath-uipath-http" "http-request" \
  --connection-id "<id>" \
  --body '{"method": "GET", "url": "https://api.example.com/v2/resource"}' \
  --output json
```

Body fields:

| Field | Description |
|---|---|
| `method` | HTTP method: GET, POST, PUT, PATCH, DELETE. |
| `url` | Full URL to call. |
| `headers` | Optional request headers (object). |
| `query` | Optional query parameters (object). |
| `body` | Optional request body for POST/PUT/PATCH. |

## Connector Disambiguation

When search returns multiple results for the same intent, never silently select the first. Before binding, apply this ladder:

1. **Classify by connector key prefix.**
   - `uipath-<vendor>-<service>` = **catalog**, a UiPath-shipped IS catalog connector; default choice.
   - `custom-entity-*` = **custom**, tenant-built via Connector Builder; use only when no catalog match exists or the user explicitly names one.
   - `uipath-mock-*` = **mock**, an internal development artifact; filter it out and treat it as absent.

   Keys may appear inside activity/node-type strings such as `uipath.connector.<key>.<op>`, `uipath.connector.trigger.<key>.<op>`, or `uipath.agent.resource.tool.connector.<key>.<op>`; extract `<key>` for classification.

2. **Match intent using each result's `Description`.** Drop catalog candidates whose described operation does not match the request. For example, for pulling user data from Databricks, drop `uipath-databricks-databricks.query-a-serving-endpoint` (AI inference) and keep `uipath-uipath-jdbc.execute-query-synchronously` (SQL).

3. **Count remaining candidates.**
   - Exactly 1 catalog candidate: take it silently.
   - More than 1 catalog candidate with different keys: AskUser. Label each option `<DisplayName> · <connector-key>` and put its `Description` in the option description; that description is the user's primary signal.
   - 0 catalog candidates with only custom candidates: STOP. Surface the issue in the consumer skill's Open Questions; never silently bind to a custom-entity connector.

4. **Lock the choice** in the consumer skill's planning notes. Never re-derive it per node within the same flow, agent, or run.

For a single database-SQL intent satisfied by either a vendor catalog connector or the JDBC gateway, follow [JDBC Gateway — Database SQL Intent](#jdbc-gateway--database-sql-intent).

## JDBC Gateway — Database SQL Intent

When the user names a database (Snowflake, Databricks, Postgres, Oracle, SQL Server, Redshift, MySQL, BigQuery, etc.) for SQL, consider both:

1. **Native database connector**, such as `uipath-snowflake-snowflake`; it is vendor-specific and may not expose SQL. For example, `uipath-databricks-databricks` exposes only AI serving endpoints; its SQL search hit is the JDBC gateway, not the native key.
2. **JDBC gateway**, `uipath-uipath-jdbc` (Database Hub), providing `Execute Query Synchronously` and `*-record` CRUD activities through tenant-registered JDBC connections.

> **Lifecycle:** Read each candidate's lifecycle from the consumer skill's registry/discovery response (`Tags` / status field) and surface it when binding. The JDBC gateway has historically been PREVIEW; do not assume GA. Do not hard-code lifecycle labels; defer to the registry.

### Discovery

A DB-name keyword search through the consumer skill's discovery API returns both paths because the gateway description names every supported DB. Do not dismiss `uipath-uipath-jdbc.*` results because the key looks unrelated; the cross-reference is registry-surfaced.

Run:

```bash
uip is connections list "uipath-uipath-jdbc" --output json
```

### Connection identity

For inferring a JDBC connection's target DB from its `name` (because `jdbcUrl` and `driverClass` are not exposed by `connections list`) and for the explicit-user-named-connection override, follow [connections.md — Identifying a JDBC Connection's Target DB](connections.md#identifying-a-jdbc-connection's-target-db). The decision table assumes each JDBC connection is classified as **name-matched** or **ambiguously named** using that guide.

### Decision

After dropping intent-mismatched candidates under [Connector Disambiguation](#connector-disambiguation), apply this table:

| Confident paths remaining | Action |
|---|---|
| Exactly one (native SQL connector or a single name-matched JDBC connection) | Take it silently and disclose lifecycle from the discovery response. |
| Native SQL connector and a name-matched JDBC connection | **AskUser**. Use `Native <DB> · <key>` and `JDBC gateway · <name> — likely <DB>` as option labels; append the registry lifecycle (for example, ` · PREVIEW`) to each option. |
| No native connector, only ambiguously named JDBC connections (for example, `DH-Conn-001`) | **AskUser** and flag each option as "purpose unknown, please confirm". |
| No native connector and no JDBC connection | Use the consumer skill's HTTP-fallback or placeholder patterns, or instruct the user to create a JDBC connection by running `uip is connections create "uipath-uipath-jdbc"`. Do not silently STOP. |