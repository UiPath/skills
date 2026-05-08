# Connectors

Connectors are pre-built integrations to external applications. Each connector has a unique key (e.g., `uipath-salesforce-sfdc`, `uipath-servicenow-servicenow`). A connector contains **connections** (authenticated sessions), **activities** (pre-built actions), and **resources** (object types with CRUD operations).

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Response Fields

| Field | Show to user? | Description |
|---|---|---|
| **`Name`** | **Yes** | Display name — always show this to the user (e.g., "Salesforce", "Slack") |
| **`Key`** | **Yes** | Unique key used in all subsequent commands (e.g., `uipath-salesforce-sfdc`) — also shown to users since it's human-readable |
| `Active` | **Yes** | Whether the connector is active |
| `DapCompatible` | Optional | Whether it supports Data Access Policy |
| `Id` | Internal | Connector UUID — never show to the user |

---

## HTTP Connector Fallback

When no native connector exists for a vendor, use the HTTP connector (`uipath-uipath-http`) to call REST APIs directly.

```bash
# Search for vendor → not found → fall back to HTTP connector
uip is connectors list --filter "apify" --output json
# → No connectors found

# List HTTP connections and look for one named after the vendor
uip is connections list "uipath-uipath-http" --output json
```

The HTTP connector supports generic HTTP requests (GET, POST, PUT, PATCH, DELETE) to any REST API. The connection stores the authentication configuration (API keys, OAuth tokens, base URL).

### When to use HTTP fallback

- The vendor is not in the connector catalog
- The vendor has a REST API
- You need to call a custom/internal API

### HTTP request format

The HTTP connector has a single resource: `http-request`.

```bash
uip is resources execute create "uipath-uipath-http" "http-request" \
  --connection-id "<id>" \
  --body '{"method": "GET", "url": "https://api.example.com/v2/resource"}' \
  --output json
```

Body fields:

| Field | Description |
|---|---|
| `method` | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `url` | Full URL to call |
| `headers` | Optional request headers (object) |
| `query` | Optional query parameters (object) |
| `body` | Optional request body (for POST/PUT/PATCH) |

---

## Connector Disambiguation

When a connector/registry search returns multiple results for the same user intent, **never silently pick the first match**. Apply this short ladder before binding:

1. **Classify each result by connector key prefix.**
   - `uipath-<vendor>-<service>` = **catalog** — UiPath-shipped IS catalog connector. Default choice.
   - `custom-entity-*` = **custom** — tenant-built via Connector Builder. Use only when no catalog match exists, or the user explicitly names one.
   - `uipath-mock-*` = **mock** — internal dev artifact. Filter from results, treat as if absent.

   Connector keys typically appear inside richer activity / node-type strings such as `uipath.connector.<key>.<op>`, `uipath.connector.trigger.<key>.<op>`, or `uipath.agent.resource.tool.connector.<key>.<op>` — extract the `<key>` segment for classification.

2. **Intent-match by reading each result's `Description`.** Drop catalog candidates whose described operation does not match the user's intent. Example: a "pull user data from Databricks" prompt drops `uipath-databricks-databricks.query-a-serving-endpoint` (AI inference) and keeps `uipath-uipath-jdbc.execute-query-synchronously` (SQL).

3. **Count what's left after steps 1–2.**
   - 1 catalog candidate → take it silently.
   - >1 catalog candidates with different keys → AskUser. Use option label `<DisplayName> · <connector-key>` and put each candidate's `Description` in the option description — that text is the user's primary signal.
   - 0 catalog, only custom → STOP. Surface in the consumer skill's Open Questions. Never silently bind to a custom-entity connector.

4. **Lock the choice** in the consumer skill's planning notes. Never re-derive per node within the same flow / agent / run.

For the database-SQL special case (a single intent satisfied by either a per-vendor catalog connector or the JDBC gateway), see [JDBC Gateway — Database SQL Intent](#jdbc-gateway--database-sql-intent) below.

---

## JDBC Gateway — Database SQL Intent

When the user names a database (Snowflake, Databricks, Postgres, Oracle, SQL Server, Redshift, MySQL, BigQuery, etc.) for a SQL operation, two paths can satisfy the same intent:

1. **Native database connector** — e.g. `uipath-snowflake-snowflake`. Vendor-specific. May not expose SQL at all (e.g. `uipath-databricks-databricks` only exposes AI serving endpoints — its SQL search hit is the JDBC gateway, not the native key).
2. **JDBC gateway** — `uipath-uipath-jdbc` (Database Hub) with `Execute Query Synchronously` plus `*-record` CRUD activities, fronting any JDBC-compatible DB via tenant-registered connections.

> **Lifecycle**: read each candidate's lifecycle from the consumer skill's registry / discovery response (`Tags` / status field) and surface it to the user when binding. The JDBC gateway has historically been PREVIEW — do not assume GA. Hard-coded lifecycle labels in this doc would rot; always defer to the registry.

### Discovery

A keyword search by DB name (run via the consumer skill's discovery API) returns BOTH paths because the gateway's `Description` text names every supported DB. **Do not dismiss `uipath-uipath-jdbc.*` results** because the key looks unrelated — the cross-reference is registry-surfaced.

For the JDBC connection-side probe (platform-native, same regardless of consumer):

```bash
uip is connections list "uipath-uipath-jdbc" --output json
```

### Connection identity

For the rules on inferring a JDBC connection's target DB from its `name` (since `jdbcUrl` / `driverClass` are not exposed by `connections list`), and the explicit-user-named-connection override, see [connections.md — Identifying a JDBC Connection's Target DB](connections.md#identifying-a-jdbc-connections-target-db). The Decision matrix below assumes each JDBC connection has been classified as "name-matched" or "ambiguously named" using that guide.

### Decision

After dropping intent-mismatched candidates per [Connector Disambiguation](#connector-disambiguation) above:

| Confident paths remaining | Action |
|---|---|
| Exactly one (native SQL connector, OR a single name-matched JDBC connection) | Take it silently. Disclose lifecycle from the discovery response. |
| Native SQL connector AND a name-matched JDBC connection | **AskUser**. Option labels: `Native <DB> · <key>` / `JDBC gateway · <name> — likely <DB>`. Append the registry lifecycle (e.g. ` · PREVIEW`) per option. |
| No native, only ambiguously-named JDBC connections (e.g. `DH-Conn-001`) | **AskUser**, flag each option as "purpose unknown, please confirm". |
| No native and no JDBC connection | Fall back via the consumer skill's HTTP-fallback or placeholder patterns, or instruct the user to create a JDBC connection (`uip is connections create "uipath-uipath-jdbc"`). Do not silently STOP. |
