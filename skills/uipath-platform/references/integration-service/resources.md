# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

## Contents
- Listing and Describing Resources
- Response Fields
- Describe Response
- Describe Failures
- Reference Fields (CRITICAL)
- Inferring References Without Describe
- Execute Operations
- Read-Only Field Recovery
- Pagination

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

## Describe Failures

Some resources appear in `resources list --operation Create` but return empty `availableOperations` on describe, or fail with "Operation not found". This is a **server-side metadata gap**, not a cache issue — do not retry with `--refresh`.

**Recovery:**

1. **Skip describe entirely** — do not waste calls retrying.
2. **Infer fields from user context** — use the field names and values the user provided in their request.
3. **Infer reference fields from naming** — see [Inferring References Without Describe](#inferring-references-without-describe).
4. **Attempt execute directly** — let the server validate. If a field is rejected, adjust and retry (see [Read-Only Field Recovery](#read-only-field-recovery)).

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
uip is resources describe "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" --operation Create --output json

# 2. Resolve references
uip is resources execute list "uipath-zoho-desk" "departments" --connection-id "<id>" --output json
# → { "id": "1892000000006907", "name": "Engineering" }
uip is resources execute list "uipath-zoho-desk" "contacts" --connection-id "<id>" --output json
# → { "id": "1892000000048009", "name": "John Doe" }

# 3. Execute with resolved IDs
uip is resources execute create "uipath-zoho-desk" "tickets" \
  --connection-id "<id>" \
  --body '{"departmentId": "1892000000006907", "subject": "Bug report", "contactId": "1892000000048009"}' \
  --output json
```

---

## Field Dependency Chains (Field Actions)

Some reference fields **depend on other fields** — the child field's valid values are scoped by the parent field's selection. The connector's underlying metadata encodes this in `reference.path` using template variables like `{fields.project.key}`.

### How to detect dependencies

When two fields share the same `reference.objectName` (e.g., both reference `"project"`), or when a field's reference path contains `{otherField}`, they form a dependency chain. Resolve them **in order** — parent first, then child using the parent's resolved value.

### Common pattern: Jira project → issue type

The Jira `curated_create_issue` resource has this dependency:

```
fields.project.key  → reference.path: /project/search                          (no dependency)
fields.issuetype.id → reference.path: /project/{fields.project.key}/issuetypes (depends on project.key)
```

**Wrong** — listing `issuetype` globally returns Bug types from ALL projects:
```bash
uip is resources execute list "uipath-atlassian-jira" "issuetype" \
  --connection-id "<id>" --output json
# → Bug (id=1), Bug (id=10004), Bug (id=12947), ... dozens of duplicates
```

**Correct** — resolve project first, then list issue types scoped to that project:
```bash
# Step 1: Resolve project
uip is resources execute list "uipath-atlassian-jira" "project" \
  --connection-id "<id>" --output json
# → { "key": "ENGCE", "name": "Integration Service", "id": "10845" }

# Step 2: Resolve issue types FOR that project (scoped path)
uip is resources execute list "uipath-atlassian-jira" "project/ENGCE/issuetypes" \
  --connection-id "<id>" --output json
# → { "id": "10004", "name": "Bug" }  ← only issue types valid for ENGCE
```

### General rule

When resolving reference fields:
1. **Sort fields by dependency** — fields with no `{template}` in their reference path come first
2. **Resolve parent fields** — list the parent resource, pick the value
3. **Substitute into child path** — replace `{parentField}` in the child's reference path with the resolved value
4. **Resolve child fields** — list the scoped resource using the substituted path

This pattern applies across connectors (Jira, Salesforce, ServiceNow, Zoho, etc.) wherever child fields are scoped by parent selections.

---

## Inferring References Without Describe

When describe metadata is unavailable (see [Describe Failures](#describe-failures)), infer reference fields from naming conventions:

- Fields ending in **`Id`** (e.g., `PromotionId`, `AccountId`) typically reference the object with the matching base name (`Promotion`, `Account`).
- List the inferred object to resolve the ID: `is resources execute list "<connector-key>" "<base-name>" --connection-id "<id>" --output json`
- Match the user's value by `Name` or `DisplayName` in the results.

### Example: Coupon → Promotion (no describe available)

```bash
# User wants: create coupon "XYZ" for promotion "Chandu Test"
# Infer: PromotionId → list Promotion objects
uip is resources execute list "uipath-salesforce-sfdc" "Promotion" \
  --connection-id "<id>" --output json
# → { "Id": "<promotion-id>", "Name": "Summer Sale" }

# Use resolved Id in create
uip is resources execute create "uipath-salesforce-sfdc" "Coupon" \
  --connection-id "<id>" \
  --body '{"CouponCode": "SAVE20", "PromotionId": "<promotion-id>"}' --output json
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

### Filtering Results with `--output-filter`

Use the global `--output-filter` flag with a JMESPath expression to extract specific fields from large responses if possible via JMESPath.

```bash
# Extract only id, name, and email from a user list
uip is resources execute list "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" \
  --output json \
  --output-filter "Data[].{id: id, name: name, email: profile.email}"
```

Common JMESPath patterns:

| Pattern | Effect |
|---|---|
| `Data[]` | Return all records (unwrap the Data envelope) |
| `Data[].name` | Return just the `name` field from each record |
| `Data[].{id: id, name: name}` | Return selected fields as objects |
| `Data[?status=='active']` | Filter records by field value |
| `Data[0]` | Return only the first record |

---

## Read-Only Field Recovery

Some objects have auto-generated fields that cannot be set on create (e.g., Salesforce `Name` on Coupon, `CaseNumber` on Case). The server returns error `INVALID_FIELD_FOR_INSERT_UPDATE` listing the offending field(s).

**Recovery:**

1. **Parse the error** — extract the field name(s) from `providerMessage.fields`.
2. **Remove the offending field** from `--body`.
3. **Find the correct writable field** — the user's intended value often maps to a different field name (e.g., `CouponCode` instead of `Name`). Use domain knowledge or try the most specific field name for the object.
4. **Retry** the create with corrected fields.

> **Avoid `Name` as a first guess** for specialized Salesforce objects (Coupon, Case, etc.) — it is frequently auto-generated. Prefer object-specific fields like `CouponCode`, `Subject`, `Title`.

---

## Pagination

List operations may return paginated results. Use `--query "limit=50&offset=0"` and increment `offset` by `limit` to page through. Stop when the result set is empty or smaller than the limit.

```bash
uip is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --output json
# → next page: --query "limit=50&offset=50"
```
