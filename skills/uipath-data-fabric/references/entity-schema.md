# Entity Schema Reference

## Creating an Entity

```bash
uip df entities create "MyEntity" \
  --body '{
    "displayName": "My Entity",
    "description": "Optional description",
    "fields": [
      {"fieldName": "Title",       "type": "STRING",   "isRequired": true},
      {"fieldName": "Score",       "type": "INTEGER"},
      {"fieldName": "Active",      "type": "BOOLEAN"},
      {"fieldName": "CreatedDate", "type": "DATE"}
    ]
  }' \
  --output json
```

- `fields` array is **required**. Each entry must include `fieldName`.
- `displayName`, `description`, and `isRbacEnabled` are optional top-level keys.
- Response: `{ Code: "EntityCreated", Data: { ID: "<entity-id>" } }` — save the ID for subsequent operations.
- Alternatively use `--file <path>` pointing to a JSON file with the same structure.

## Supported Field Types

Pass the exact `EntityFieldDataType` string in the `"type"` field — the CLI is case-sensitive.

| CLI type (`EntityFieldDataType`) | SQL backing type | Notes |
|----------------------------------|-----------------|-------|
| `UUID` | UNIQUEIDENTIFIER | GUID fields |
| `STRING` | NVARCHAR | Short text |
| `MULTILINE_TEXT` | NVARCHAR(MAX) | Long text |
| `INTEGER` | INT | 32-bit integer |
| `BIG_INTEGER` | BIGINT | 64-bit integer |
| `DECIMAL` | DECIMAL | Fixed-precision decimal |
| `FLOAT` | REAL | Single-precision float |
| `DOUBLE` | FLOAT | Double-precision float |
| `BOOLEAN` | BIT | true/false |
| `DATE` | DATE | Date only (no time) |
| `DATETIME` | DATETIME2 | Date + time (no timezone) |
| `DATETIME_WITH_TZ` | DATETIMEOFFSET | Date + time + timezone |
| `FILE` | UNIQUEIDENTIFIER | Attachment — manage with `files upload/download/delete` |
| `CHOICE_SET_SINGLE` | INT | Single-select from a choice set — also requires `choiceSetId` |
| `CHOICE_SET_MULTIPLE` | NVARCHAR | Multi-select from a choice set — also requires `choiceSetId` |
| `AUTO_NUMBER` | DECIMAL | Auto-incrementing number |
| `RELATIONSHIP` | UNIQUEIDENTIFIER | FK link to another entity — requires `referenceEntityName` + `referenceFieldName` |

## Field Definition Object

### Name Validation

Both entity names and field names must:
- Start with a letter (`[a-zA-Z]`)
- Contain only letters, digits, and underscores (`[a-zA-Z0-9_]`)
- Be 3–100 characters long

**Reserved field names** (will error if used): `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`

### All Field Options

```json
{
  "fieldName": "AccountNumber",
  "type": "STRING",
  "displayName": "Account Number",
  "description": "Customer bank account number",
  "isRequired": true,
  "isUnique": false,
  "isRbacEnabled": false,
  "isEncrypted": false,
  "defaultValue": ""
}
```

| Option | Type | Default | Notes |
|--------|------|---------|-------|
| `fieldName` | string | required | 3–100 chars, starts with letter, `[a-zA-Z0-9_]` |
| `type` | `EntityFieldDataType` | `STRING` | See type table above |
| `displayName` | string | fieldName | Human-readable label |
| `description` | string | `""` | Optional description |
| `isRequired` | boolean | `false` | Field must have a value on insert |
| `isUnique` | boolean | `false` | Value must be unique across all records |
| `isRbacEnabled` | boolean | `false` | Role-based access control on this field |
| `isEncrypted` | boolean | `false` | Encrypted at rest |
| `defaultValue` | string | — | Default value (always a string representation) |

### Choice Set Fields

```json
{ "fieldName": "Status", "type": "CHOICE_SET_SINGLE", "choiceSetId": "<choice-set-id>" }
```

`CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` both require `choiceSetId`.

### Relationship Fields

```json
{
  "fieldName": "CustomerId",
  "type": "RELATIONSHIP",
  "referenceEntityName": "<target-entity-name>",
  "referenceFieldName": "<field-name-in-target-entity>"
}
```

`RELATIONSHIP` requires `referenceEntityName` (the technical name of the target entity) and `referenceFieldName` (the field in the target entity to link on). Use `entities get <id>` to verify exact entity and field names.

## Not Supported

| Operation | Action |
|-----------|--------|
| Delete an entity | No command exists — tell the user it is not supported |
| Remove / delete a field | CLI explicitly rejects `removeFields` with an error — do not attempt |
| Change a field's data type | Not supported — type is fixed at creation and cannot be changed via `updateFields` |

---

## Updating an Entity

Use `entities update` to add fields, modify existing field metadata, or update entity-level properties.

```bash
# Add new fields
uip df entities update <entity-id> \
  --body '{"addFields":[{"fieldName":"Priority","type":"INTEGER"},{"fieldName":"Tags","type":"STRING"}]}' \
  --output json

# Update entity display name and description (metadata only)
uip df entities update <entity-id> \
  --body '{"displayName":"Updated Name","description":"New description"}' \
  --output json

# Add fields and update metadata in one call
uip df entities update <entity-id> \
  --body '{
    "addFields": [{"fieldName":"Region","type":"STRING"}],
    "displayName": "Regional Entity"
  }' \
  --output json
```

### Updating Existing Field Metadata (`updateFields`)

`updateFields` identifies fields by their **field ID** (UUID), not by name. Retrieve field IDs from `entities get <entity-id> --output json` — each field in the `Fields` array includes an `ID` property (uppercase in the GET response). Use that value as `id` (lowercase) in the `updateFields` payload.

```bash
uip df entities update <entity-id> \
  --body '{
    "updateFields": [
      { "id": "<field-id>", "displayName": "Unit Price", "isRequired": true, "isUnique": false }
    ]
  }' \
  --output json
```

`updateFields` entry supports: `id` (required), `displayName`, `description`, `isRequired`, `isUnique`, `isRbacEnabled`, `isEncrypted`, `defaultValue`.

### Supported `entities update` Body Keys

| Key | Description |
|-----|-------------|
| `addFields` | Array of field definition objects to add (same shape as create) |
| `updateFields` | Array of field updates — each entry must include `id` (field UUID) |
| `displayName` | New display name for the entity |
| `description` | New description |
| `isRbacEnabled` | Toggle RBAC on the entity |

> `removeFields` is explicitly rejected by the CLI with an error — do not attempt it.

## System Fields

Every entity has auto-created system fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`. These are read-only and must not be included in field definitions or CSV imports.

## Listing and Inspecting Entities

```bash
# Discover all entities (shows Source: Native or Federated)
uip df entities list --output json

# Discover only native entities (recommended before any write operation)
uip df entities list --native-only --output json

# Get full schema including all fields
uip df entities get <entity-id> --output json
```

## Native vs Federated Entities

The `entities list` output includes a `Source` field:

- `Native` — data stored in Data Fabric, full read/write access
- `Federated (ConnectorName)` — backed by an external connector (e.g. Salesforce, Azure AD), read-only

**Only native entities support record creation, update, delete, and import.**

> Creating federated entities or linking entities to external connectors is **not currently supported**. This cannot be done via the CLI or the UiPath portal.
