# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

---

## List Resources

**Always pass `--connection-id` and `--operation`** to get accurate results including custom objects. Without these, the response may be incomplete and require retries.

> **Caching:** Results are cached locally. If expected resources are not found, retry with `--refresh` to bypass the cache and fetch the latest from the API.

```bash
# Recommended: always include connection-id and operation
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" \
  --operation <Create|List|Retrieve|Update|Delete|Replace> \
  --format json

# Force refresh (bypass cache)
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" \
  --operation Create \
  --refresh --format json
```

> **Why both flags?** `--connection-id` returns custom objects specific to that connection. `--operation` filters to resources that support the intended action. Together they give you the exact list you need in a single call — no retries.

### Response Fields

| Field | Description |
|---|---|
| `Name` | Resource identifier (used in commands) |
| `DisplayName` | Human-readable name |
| `Path` | API path for this resource |
| `Type` | Resource type (standard, custom) |
| `SubType` | Sub-type (e.g., method, entity) |

---

## Describe a Resource

**Always pass `--connection-id` and `--operation`** to get the exact field schema you need.

- **`--connection-id`** — Required to include custom fields specific to that connection. Without it, only standard fields are returned and a warning is shown.
- **`--operation`** — Returns only the subset of metadata relevant to that operation (e.g., required and optional fields for Create) instead of the entire metadata blob. Without it, you get a summary of available operations and a hint to specify one.

> **Caching:** When `--operation` is provided, results are cached locally. Subsequent calls with the same connector/connection/object/operation return from cache instantly. If expected fields are missing or seem stale, retry with `--refresh` to bypass the cache and fetch the latest from the API.

```bash
# Recommended: always include connection-id and operation
uipcli is resources describe "<connector-key>" "<object-name>" \
  --connection-id "<id>" \
  --operation Create \
  --format json

# Force refresh (bypass cache)
uipcli is resources describe "<connector-key>" "<object-name>" \
  --connection-id "<id>" \
  --operation Create \
  --refresh --format json
```

### Describe Response

When `--operation` is provided, the describe command returns:
- **requiredFields** — Fields that must be provided for this operation
- **optionalFields** — Fields that can optionally be provided
- **responseFields** — Fields returned in the response
- **referenceFields** — Fields that reference other objects (see below)
- **metadataFile** — Cached file path with full field details

When `--operation` is omitted, it returns:
- **availableOperations** — List of operations the resource supports (e.g., Create, List, Retrieve)
- **files** — Cached file paths per operation for direct inspection
- **hint** — Instruction to use `--operation` for field-level details

---

## Reference Fields (CRITICAL)

Some fields in the describe response have a `reference` section, meaning their value must be looked up from another resource. **You MUST resolve these before executing the main operation.** Never fabricate or guess reference IDs.

### How Reference Fields Work

A reference field looks like this in the describe output:

```json
{
  "field": "departmentId",
  "displayName": "Department",
  "description": "ID of the department to which the ticket belongs",
  "referencedObject": "departments",
  "lookupValue": "id",
  "hint": "Resolve by executing: is resources execute list ... \"departments\" ..."
}
```

This means: `departmentId` expects a valid ID from the `departments` resource.

### Resolution Workflow

```
Step 1: Describe the target resource (e.g., "tickets") with --operation Create
        → Identify fields with referenceFields in the response

Step 2: For EACH reference field:
        → Execute: is resources execute list "<connector-key>" "<referencedObject>"
                   --connection-id <id> --format json
        → Collect the lookupValue (e.g., "id") from the results
        → Present options to the user if multiple values exist (show name + id)

Step 3: Build the request body using the resolved reference values
        → Execute the main operation (e.g., create the ticket)
```

### Example: Creating a Zoho Desk Ticket

```bash
# 1. Describe the resource to find required fields and references
uipcli is resources describe "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" --operation Create --format json
# → requiredFields: ["departmentId", "subject", "contactId"]
# → referenceFields: [
#     { field: "departmentId", referencedObject: "departments", lookupValue: "id" },
#     { field: "contactId", referencedObject: "contacts", lookupValue: "id" }
#   ]

# 2. Resolve reference: list departments
uipcli is resources execute list "uipath-zoho-desk" "departments" \
  --connection-id "<id>" --format json
# → [{ "id": "1892000000006907", "name": "Engineering" }, ...]
# → Present to user: "Which department? Engineering (1892000000006907), ..."

# 3. Resolve reference: list contacts
uipcli is resources execute list "uipath-zoho-desk" "contacts" \
  --connection-id "<id>" --format json
# → [{ "id": "1892000000048009", "name": "John Doe" }, ...]

# 4. Execute with resolved values
uipcli is resources execute create "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" \
  --body '{"departmentId": "1892000000006907", "subject": "Bug report", "contactId": "1892000000048009"}' \
  --format json
```

### Rules for Reference Fields

1. **ALWAYS check the describe output for referenceFields before executing create/update operations.**
2. **NEVER fabricate reference IDs.** Always list the referenced object and use real values.
3. **Present options to the user** when multiple values exist for a reference field.
4. **Resolve ALL reference fields** before building the request body.

---

## Resource Operations

| Operation | CLI Verb | HTTP Method | Description |
|---|---|---|---|
| **List** | `list` | GET | Retrieve multiple records |
| **Retrieve** | `get` | GET (by ID) | Get a single record by ID |
| **Create** | `create` | POST | Create a new record |
| **Update** | `update` | PATCH | Partial update of a record |
| **Delete** | `delete` | DELETE | Delete a record |
| **Replace** | `replace` | PUT | Full replacement of a record |

---

## Execute Operations

All execute commands require `--connection-id`.

### Create a Record

```bash
uipcli is resources execute create "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --body '{"field1": "value1", "field2": "value2"}' \
  --format json
```

### List Records

```bash
uipcli is resources execute list "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --format json

# With query parameters (pagination, filtering)
uipcli is resources execute list "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --query "limit=10&offset=0" \
  --format json
```

### Get a Record by ID

```bash
uipcli is resources execute get "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --query "id=<RECORD_ID>" \
  --format json
```

### Update a Record

```bash
uipcli is resources execute update "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --body '{"field1": "new_value"}' \
  --query "id=<RECORD_ID>" \
  --format json
```

### Replace a Record

```bash
uipcli is resources execute replace "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --body '{"field1": "value1", "field2": "value2"}' \
  --query "id=<RECORD_ID>" \
  --format json
```

### Delete a Record

```bash
uipcli is resources execute delete "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  --query "id=<RECORD_ID>" \
  --format json
```

---

## Execute Options

| Option | Description |
|---|---|
| `--connection-id <id>` | Connection ID (**required** for all execute operations) |
| `--body <json>` | Request body as JSON string (required for create, update, replace) |
| `--query <params>` | Query parameters as `key=value&key=value` (e.g., `limit=10&offset=0`) |

---

## Workflow: Discovering and Executing

```bash
# 1. List available resources (always pass --connection-id and --operation)
uipcli is resources list "uipath-salesforce-sfdc" \
  --connection-id "<id>" --operation Create --format json

# 2. Describe the resource to see required/optional fields
uipcli is resources describe "uipath-salesforce-sfdc" "Account" \
  --connection-id "<id>" --operation Create --format json

# 3. Execute the operation
uipcli is resources execute create "uipath-salesforce-sfdc" "Account" \
  --connection-id "<id>" \
  --body '{"Name": "Acme Corp", "Industry": "Technology"}' \
  --format json
```

---

## HTTP Connector Resources

The HTTP connector (`uipath-uipath-http`) has a single resource: `http-request`.

```bash
# Make an HTTP request via the HTTP connector
uipcli is resources execute create "uipath-uipath-http" "http-request" \
  --connection-id "<CONNECTION_ID>" \
  --body '{"method": "GET", "url": "https://api.example.com/v2/items", "query": {"limit": "20"}}' \
  --format json
```

### HTTP Request Body Fields

| Field | Type | Description |
|---|---|---|
| `method` | string | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `url` | string | Full URL to call |
| `headers` | object | Optional request headers |
| `query` | object | Optional query parameters |
| `body` | object | Optional request body (for POST/PUT/PATCH) |
