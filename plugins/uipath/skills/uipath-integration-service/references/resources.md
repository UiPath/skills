# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

---

## List Resources

**Always pass `--connection-id` and `--operation`** to get accurate results including custom objects in a single call.

- `--connection-id` — Returns custom objects specific to that connection
- `--operation` — Filters to resources that support the intended action

```bash
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" \
  --operation <Create|List|Retrieve|Update|Delete|Replace> \
  --format json
```

> Run `uipcli is resources list --help` for all flags.

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

- `--connection-id` — Returns custom fields specific to that connection. Without it, only standard fields are returned.
- `--operation` — Returns only the relevant field subset (required/optional for that operation) instead of full metadata. Without it, you get a summary of available operations.

```bash
uipcli is resources describe "<connector-key>" "<object-name>" \
  --connection-id "<id>" \
  --operation Create \
  --format json
```

> Run `uipcli is resources describe --help` for all flags.

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

Some fields in the describe response have a `reference` section — their value must be looked up from another resource. For each reference field: list the `referencedObject`, collect the `lookupValue` from results, and present options to the user.

A reference field in the describe output:

```json
{
  "field": "departmentId",
  "referencedObject": "departments",
  "lookupValue": "id",
  "hint": "Resolve by executing: is resources execute list ... \"departments\" ..."
}
```

### Example: Creating a Zoho Desk Ticket

```bash
# 1. Describe → discover referenceFields: departmentId → "departments", contactId → "contacts"
uipcli is resources describe "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" --operation Create --format json

# 2. Resolve references
uipcli is resources execute list "uipath-zoho-desk" "departments" --connection-id "<id>" --format json
# → { "id": "1892000000006907", "name": "Engineering" }
uipcli is resources execute list "uipath-zoho-desk" "contacts" --connection-id "<id>" --format json
# → { "id": "1892000000048009", "name": "John Doe" }

# 3. Execute with resolved IDs
uipcli is resources execute create "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" \
  --body '{"departmentId": "1892000000006907", "subject": "Bug report", "contactId": "1892000000048009"}' \
  --format json
```

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

All execute commands follow this pattern:

```bash
uipcli is resources execute <verb> "<connector-key>" "<object-name>" \
  --connection-id "<CONNECTION_ID>" \
  [--body '{"field": "value"}'] \
  [--query "key=value&key=value"] \
  --format json
```

| Verb | Requires `--body` | Requires `--query` | Use case |
|---|---|---|---|
| `create` | Yes | No | Create a new record |
| `list` | No | Optional (`limit=10&offset=0`) | List multiple records |
| `get` | No | Yes (`id=<RECORD_ID>`) | Get a single record by ID |
| `update` | Yes | Yes (`id=<RECORD_ID>`) | Partial update of a record |
| `replace` | Yes | Yes (`id=<RECORD_ID>`) | Full replacement of a record |
| `delete` | No | Yes (`id=<RECORD_ID>`) | Delete a record |

Run `uipcli is resources execute --help` for all available options.

---

## Pagination

List operations may return paginated results. Use `--query "limit=50&offset=0"` and increment `offset` by `limit` to page through. Stop when the result set is empty or smaller than the limit.

```bash
uipcli is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --format json
# → next page: --query "limit=50&offset=50"
```

---

## HTTP Connector

The HTTP connector (`uipath-uipath-http`) has a single resource: `http-request`. See [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback) for body fields and usage.
