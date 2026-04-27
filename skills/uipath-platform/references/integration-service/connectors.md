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

## Official vs Custom Connectors

A tenant may have both a **catalog** (official) connector and a **custom** connector for the same vendor. When `uip is connectors list --filter "<vendor>"` returns multiple results, distinguish them by **Key prefix**:

| Key prefix | Type |
|---|---|
| `uipath-` | Catalog (official) connector |
| `custom-` | Custom tenant connector |
| `design-` | Custom tenant connector (rare) |

### Selection rules

1. **Filter out custom connectors first.** Drop any `custom-`/`design-` prefixed keys unless the user explicitly requests a custom connector.
2. **Single catalog match** → use it automatically.
3. **Multiple catalog matches** → present the list to the user and ask which one to use. A vendor can have multiple official connectors serving different purposes (e.g., Snowflake DB vs Snowflake Cortex, or multiple Microsoft connectors). Never auto-select in this case.
4. **No catalog match, only custom** → fall back to `custom-`/`design-` connectors.

```bash
# Example: catalog vs custom — auto-select the catalog connector
uip is connectors list --filter "google sheets" --output json
# → Key: "uipath-googlesheets-googlesheets"  ← catalog — use this one
# → Key: "custom-google-sheets-abc"           ← custom — skip unless user asks

# Example: multiple catalog connectors — present choice to user
uip is connectors list --filter "snowflake" --output json
# → Key: "uipath-snowflake-db"      Name: "Snowflake DB"
# → Key: "uipath-snowflake-cortex"  Name: "Snowflake Cortex"
# → Ask the user which one to use — do NOT auto-select
```

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
