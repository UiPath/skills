# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

> Full command syntax and options: [uipcli-commands.md — Integration Service](../uipcli-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Listing and Describing Resources

**Always pass `--connection-id` and `--operation`** to get accurate results:

- `--connection-id` — Returns custom objects/fields specific to that connection. Without it, only standard objects/fields are returned.
- `--operation` — Filters to resources/fields relevant to the intended action. Without it on describe, you get a summary of available operations instead of field-level details.

## Response Fields

| Field | Description |
|---|---|
| **`Name`** | Resource identifier (used in commands) |
| `DisplayName` | Human-readable name |
| `Path` | API path for this resource |
| `Type` | Resource type (standard, custom) |
| `SubType` | Sub-type (e.g., method, entity) |

## Describe Response

When `--operation` is provided:

| Section | Description |
|---|---|
| **requiredFields** | Fields that must be provided for this operation |
| **optionalFields** | Fields that can optionally be provided |
| **responseFields** | Fields returned in the response |
| **referenceFields** | Fields that reference other objects (see below) |
| **metadataFile** | Cached file path with full field details |

When `--operation` is omitted, returns **availableOperations** and a hint to use `--operation` for field-level details.

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

## Execute Operations

| Verb | Description | `--body` | `--query` |
|---|---|---|---|
| `create` | Create a new record | Yes | No |
| `list` | Retrieve multiple records | No | Optional (`limit=10&offset=0`) |
| `get` | Get a single record by ID | No | Yes (`id=<RECORD_ID>`) |
| `update` | Partial update (PATCH) | Yes | Yes (`id=<RECORD_ID>`) |
| `delete` | Delete a record | No | Yes (`id=<RECORD_ID>`) |
| `replace` | Full replacement (PUT) | Yes | Yes (`id=<RECORD_ID>`) |

> **Update** (PATCH) = change specific fields. **Replace** (PUT) = overwrite entire record. Default to **Update** unless the user says "replace" or "overwrite".

---

## Pagination

List operations may return paginated results. Use `--query "limit=50&offset=0"` and increment `offset` by `limit` to page through. Stop when the result set is empty or smaller than the limit.

```bash
uipcli is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --format json
# → next page: --query "limit=50&offset=50"
```
