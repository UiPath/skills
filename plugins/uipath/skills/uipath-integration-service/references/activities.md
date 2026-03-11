# Activities

Activities are pre-built actions available for each connector. These are the building blocks used in automation workflows. Each activity performs a specific operation (e.g., "Send Message", "Create Issue", "Get Record").

---

## List Activities

```bash
uipcli is activities list "<connector-key>" --format json
```

Force refresh (bypass cache):
```bash
uipcli is activities list "<connector-key>" --refresh --format json
```

> **Cache behavior:** Results are cached locally. If expected activities are not found, retry with `--refresh` to fetch latest from API.

This lists **non-trigger activities only** (actions the automation can perform, not event listeners).

### Response Fields

| Field | Description |
|---|---|
| `Name` | Activity identifier |
| `DisplayName` | Human-readable name (e.g., "HTTP Request", "Send Message") |
| `Description` | What the activity does |
| `ObjectName` | The resource object this activity operates on |
| `MethodName` | HTTP method used (GET, POST, etc.) |
| `Operation` | Operation type (N/A for method-based activities) |
| `IsCurated` | Whether this is a curated/recommended activity |

---

## Activities vs Resources

Activities and resources serve different purposes:

| | Activities | Resources |
|---|---|---|
| **What** | Pre-built actions (e.g., "Send Email") | Data objects with CRUD operations (e.g., "Account") |
| **When** | Use for specific actions the connector supports | Use for generic CRUD on connector objects |
| **How** | Discovered via `is activities list` | Discovered via `is resources list` |
| **Execute** | Via workflow activities in Studio | Via `is resources execute <verb>` |

Some connectors have both activities and resources. Others may have only one. Always check both:

```bash
# Check activities
uipcli is activities list "<connector-key>" --format json

# Check resources
uipcli is resources list "<connector-key>" --format json
```

---

## HTTP Connector Activities

The HTTP connector (`uipath-uipath-http`) has a single activity:

| Activity | Description |
|---|---|
| **HTTP Request** | Make a generic HTTP request to any REST API endpoint |

This is used when no native connector exists for the target service. The HTTP Request activity supports all HTTP methods and allows custom headers, query parameters, and request bodies.

---

## Examples

### List Salesforce activities
```bash
uipcli is activities list "uipath-salesforce-sfdc" --format json
# Returns: Create Account, Update Contact, Query Records, ...
```

### List Slack activities
```bash
uipcli is activities list "uipath-salesforce-slack" --format json
# Returns: Send Message, List Channels, Get User, ...
```

### List Jira activities
```bash
uipcli is activities list "uipath-atlassian-jira" --format json
# Returns: Create Issue, Update Issue, Get Issue, ...
```
