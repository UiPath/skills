# Connectors

Connectors are pre-built integrations to external applications. Each connector has a unique key (e.g., `uipath-salesforce-sfdc`, `uipath-servicenow-servicenow`).

## Architecture

```
Integration Service (cloud.uipath.com)
  └── Connector                     ← Pre-built integration (e.g., Salesforce, SAP)
        ├── Connection(s)           ← Authenticated session(s) for this connector
        ├── Activities              ← Pre-built automation actions
        └── Resources               ← Object types with CRUD operations
              └── Operations        ← List, Retrieve, Create, Update, Delete, Replace
```

---

## List Connectors

```bash
uipcli is connectors list --format json
```

With filter:
```bash
uipcli is connectors list --filter "salesforce" --format json
```

Force refresh (bypass cache):
```bash
uipcli is connectors list --refresh --format json
```

> **Cache behavior:** Results are cached locally. If expected connectors are not found, retry with `--refresh` to fetch latest from API.

### Response Fields

| Field | Description |
|---|---|
| `Id` | Connector ID |
| `Name` | Display name (e.g., "Salesforce") |
| `Key` | Unique key used in all commands (e.g., `uipath-salesforce-sfdc`) |
| `Active` | Whether the connector is active |
| `DapCompatible` | Whether it supports Data Access Policy |

---

## Get Connector Details

```bash
uipcli is connectors get "<connector-key>" --format json
```

Returns full details including description, authentication types, categories, and documentation URL.

---

## HTTP Connector Fallback

When no native connector exists for a vendor, use the HTTP connector (`uipath-uipath-http`) to call REST APIs directly.

```bash
# Search for vendor
uipcli is connectors list --filter "apify" --refresh --format json
# → No connectors found

# Fall back to HTTP connector
uipcli is connections list "uipath-uipath-http" --refresh --format json
# → Look for a connection named after the vendor (e.g., "Apify")
```

The HTTP connector supports generic HTTP requests (GET, POST, PUT, PATCH, DELETE) to any REST API. The connection stores the authentication configuration (API keys, OAuth tokens, base URL).

### When to use HTTP fallback

- The vendor is not in the connector catalog
- The vendor has a REST API
- You need to call a custom/internal API

### HTTP request format

When using the HTTP connector's `http-request` resource:

```bash
uipcli is resources execute create "uipath-uipath-http" "http-request" \
  --connection-id "<CONNECTION_ID>" \
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
