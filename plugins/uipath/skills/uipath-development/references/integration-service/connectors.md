# Connectors

Connectors are pre-built integrations to external applications. Each connector has a unique key (e.g., `uipath-salesforce-sfdc`, `uipath-servicenow-servicenow`). A connector contains **connections** (authenticated sessions), **activities** (pre-built actions), and **resources** (object types with CRUD operations).

> Full command syntax and options: [uipcli-commands.md — Integration Service](../uipcli-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Response Fields

| Field | Description |
|---|---|
| **`Key`** | Unique key used in all subsequent commands (e.g., `uipath-salesforce-sfdc`) |
| `Id` | Connector ID |
| `Name` | Display name (e.g., "Salesforce") |
| `Active` | Whether the connector is active |
| `DapCompatible` | Whether it supports Data Access Policy |

---

## HTTP Connector Fallback

When no native connector exists for a vendor, use the HTTP connector (`uipath-uipath-http`) to call REST APIs directly.

```bash
# Search for vendor → not found → fall back to HTTP connector
uipcli is connectors list --filter "apify" --format json
# → No connectors found

# List HTTP connections and look for one named after the vendor
uipcli is connections list "uipath-uipath-http" --format json
```

The HTTP connector supports generic HTTP requests (GET, POST, PUT, PATCH, DELETE) to any REST API. The connection stores the authentication configuration (API keys, OAuth tokens, base URL).

### When to use HTTP fallback

- The vendor is not in the connector catalog
- The vendor has a REST API
- You need to call a custom/internal API

### HTTP request format

The HTTP connector has a single resource: `http-request`.

```bash
uipcli is resources execute create "uipath-uipath-http" "http-request" \
  --connection-id "<id>" \
  --body '{"method": "GET", "url": "https://api.example.com/v2/resource"}' \
  --format json
```

Body fields:

| Field | Description |
|---|---|
| `method` | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `url` | Full URL to call |
| `headers` | Optional request headers (object) |
| `query` | Optional query parameters (object) |
| `body` | Optional request body (for POST/PUT/PATCH) |
