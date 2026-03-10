# Integration Service Guide

Guide to UiPath Integration Service — managing connectors, connections, activities, and resources via the CLI.

## What is Integration Service?

UiPath Integration Service provides pre-built connectors to hundreds of third-party applications (Salesforce, SAP, ServiceNow, Slack, etc.). It handles:

- **Authentication** — OAuth2, API keys, and other auth flows managed centrally
- **Connections** — Reusable authenticated sessions shared across automations
- **Activities** — Pre-built actions for each connector (e.g., "Create Salesforce Account")
- **Resources** — CRUD operations on connector objects (e.g., Salesforce Account, Contact)

### Architecture

```
Integration Service (cloud.uipath.com)
  └── Connector                     ← Pre-built integration (e.g., Salesforce, SAP)
        ├── Connection(s)           ← Authenticated session(s) for this connector
        ├── Activities              ← Pre-built automation actions
        └── Resources               ← Object types with CRUD operations
              └── Operations        ← List, Retrieve, Create, Update, Delete, Replace
```

---

## Connectors

Connectors are pre-built integrations to external applications. Each connector has a unique key (e.g., `uipath-salesforce`, `uipath-servicenow`).

### List Connectors

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

### Get Connector Details

```bash
uipcli is connectors get "uipath-salesforce" --format json
```

---

## Connections

Connections are authenticated sessions for a specific connector. They store credentials and tokens, and can be shared across automations within a folder.

### List Connections

```bash
# List all connections
uipcli is connections list --format json

# List connections for a specific connector
uipcli is connections list "uipath-salesforce" --format json

# Filter by folder
uipcli is connections list --folder-key "<GUID>" --format json

# Filter by specific connection ID
uipcli is connections list --connection-id "<ID>" --format json
```

### Create a Connection

Create a new authenticated connection for a connector. Opens an OAuth flow in the browser:

```bash
uipcli is connections create "<connector-key>" --format json
```

For headless environments (prints the auth URL instead of opening a browser):
```bash
uipcli is connections create "<connector-key>" --no-browser --format json
```

**Example:**
```bash
# Find the connector key
uipcli is connectors list --filter "slack" --format json
# → Key: "uipath-salesforce-slack"

# Create the connection
uipcli is connections create "uipath-salesforce-slack" --format json
```

### Test a Connection

Ping a connection to verify it's healthy:

```bash
uipcli is connections ping "<CONNECTION_ID>" --format json
```

### Edit a Connection

Update an existing connection's configuration:

```bash
uipcli is connections edit "<CONNECTION_ID>" --format json
```

---

## Activities

Activities are pre-built actions available for each connector. These are the building blocks used in automation workflows.

### List Activities

```bash
uipcli is activities list "uipath-salesforce" --format json
```

This lists non-trigger activities (actions the automation can perform).

---

## Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

### List Resources

```bash
# List all resources for a connector
uipcli is resources list "uipath-salesforce" --format json

# List operations for a specific object
uipcli is resources list "uipath-salesforce" "Account" --format json

# Filter by operation type
uipcli is resources list "uipath-salesforce" "Account" --operation Create --format json
```

### Describe a Resource

Get detailed schema and operation information for a specific resource object:

```bash
uipcli is resources describe "uipath-salesforce" "Account" --format json

# With specific operation
uipcli is resources describe "uipath-salesforce" "Account" --operation Create --format json
```

### Execute a Resource Operation

Perform a CRUD operation on a resource object:

```bash
# Create a record
uipcli is resources execute "uipath-salesforce" "Account" \
  --connection-id "<CONNECTION_ID>" \
  --body '{"Name": "Acme Corp", "Industry": "Technology"}' \
  --format json

# Query records
uipcli is resources execute "uipath-salesforce" "Account" \
  --connection-id "<CONNECTION_ID>" \
  --query '{"$filter": "Industry eq Technology"}' \
  --format json
```

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID (required for execution) |
| `--body <json>` | Request body as JSON string |
| `--query <json>` | Query parameters as JSON string |

---

## Resource Operations

| Operation | Description |
|---|---|
| **List** | Retrieve multiple records (with filtering/pagination) |
| **Retrieve** | Get a single record by ID |
| **Create** | Create a new record |
| **Update** | Update an existing record (partial update) |
| **Delete** | Delete a record |
| **Replace** | Replace a record entirely (full update) |

---

## Common Workflows

### Discover Available Integrations

```bash
# 1. List all connectors
uipcli is connectors list --format json

# 2. Find a specific connector
uipcli is connectors list --filter "servicenow" --format json

# 3. Get connector details
uipcli is connectors get "uipath-servicenow" --format json

# 4. List what you can do with it
uipcli is activities list "uipath-servicenow" --format json
uipcli is resources list "uipath-servicenow" --format json
```

### Explore a Resource Schema

```bash
# 1. List resources for the connector
uipcli is resources list "uipath-salesforce" --format json

# 2. Describe the resource to see fields and operations
uipcli is resources describe "uipath-salesforce" "Account" --format json

# 3. Check what operations are available
uipcli is resources list "uipath-salesforce" "Account" --operation Create --format json
```

### Test a Connection

```bash
# 1. List connections to find the connection ID
uipcli is connections list "uipath-salesforce" --format json

# 2. Execute a simple List operation to verify connectivity
uipcli is resources execute "uipath-salesforce" "Account" \
  --connection-id "<CONNECTION_ID>" \
  --query '{"$top": 1}' \
  --format json
```

---

## Using Integration Service in Coded Workflows

In coded workflows, Integration Service connectors are accessed via the `office365` and `google` service properties (for Microsoft 365 and Google Workspace), or via custom connector activities.

### Microsoft 365 (via `office365` service)

Requires `UiPath.MicrosoftOffice365.Activities` package in `project.json`.

```csharp
// Send email via Microsoft Graph
office365.SendMail(
    to: "recipient@example.com",
    subject: "Invoice Report",
    body: "Please find the attached report.",
    importance: "Normal"
);

// Read Excel from OneDrive
var data = office365.ReadRange(
    driveItem: "path/to/file.xlsx",
    sheetName: "Sheet1"
);
```

### Google Workspace (via `google` service)

Requires `UiPath.GSuite.Activities` package in `project.json`.

```csharp
// Send email via Gmail
google.SendGmail(
    to: "recipient@example.com",
    subject: "Report",
    body: "Monthly report attached."
);

// Read Google Sheets
var data = google.ReadRange(
    spreadsheetId: "<SPREADSHEET_ID>",
    range: "Sheet1!A1:D10"
);
```

> **Note:** Both `office365` and `google` services require Integration Service connections configured in UiPath Automation Cloud. They use OAuth tokens managed by Integration Service.
