# Entity Schema Reference

## Creating an Entity

```bash
uip df entities create "MyEntity" \
  --body '{
    "fields": [
      {"fieldName":"title","type":"text"},
      {"fieldName":"score","type":"number"},
      {"fieldName":"active","type":"boolean"},
      {"fieldName":"createdDate","type":"date"}
    ],
    "displayName": "My Entity",
    "description": "Optional description"
  }' \
  --output json
```

- `fields` array is **required**. Each entry must include `fieldName`.
- `displayName`, `description`, and `isRbacEnabled` are optional top-level keys.
- Response: `{ Code: "EntityCreated", Data: { ID: "<entity-id>" } }` — save the ID for subsequent operations.
- Alternatively use `--file <path>` pointing to a JSON file with the same structure.

## Supported Field Types

| User type | SQL equivalent | Use case |
|-----------|---------------|----------|
| `text` | NVARCHAR(200) | Short strings, names |
| `longtext` | NVARCHAR(4000) | Descriptions, notes |
| `number` | INT | Counts, IDs |
| `decimal` | DECIMAL | Prices, percentages |
| `boolean` | BIT | Flags, status |
| `datetime` | DATETIME2 | Timestamps |
| `date` | DATE | Calendar dates |
| `file` | NVARCHAR(200) | Binary file attachment (manage with `files upload/download/delete`) |

## Field Definition Object

```json
{
  "fieldName": "myField",
  "type": "text",
  "displayName": "Optional display label",
  "isRequired": false
}
```

- `fieldName` is required and becomes the technical name (lowercase, no spaces)
- `type` defaults to `"text"` if omitted

## Not Supported

| Operation | Action |
|-----------|--------|
| Delete an entity | No command exists — tell the user it is not supported |
| Remove / delete a field | Not supported — do not pass `removeFields` in `entities update` (CLI errors) |
| Change a field's data type | Not supported via `updateFields` — type is set at creation only |

---

## Updating an Entity

Use `entities update` to add fields, modify field metadata, or update entity-level properties.

```bash
# Add new fields to an existing entity
uip df entities update <entity-id> \
  --body '{"addFields":[{"fieldName":"priority","type":"number"},{"fieldName":"tags","type":"text"}]}' \
  --output json

# Update entity display name and description
uip df entities update <entity-id> \
  --body '{"displayName":"Updated Name","description":"New description"}' \
  --output json

# Add fields and update metadata in one call
uip df entities update <entity-id> \
  --body '{
    "addFields": [{"fieldName":"region","type":"text"}],
    "displayName": "Regional Entity"
  }' \
  --output json
```

Supported keys in the update body:

| Key | Description |
|-----|-------------|
| `addFields` | Array of field definition objects to add |
| `updateFields` | Array of field updates (modify existing field metadata) |
| `displayName` | New display name for the entity |
| `description` | New description |
| `isRbacEnabled` | Toggle RBAC on the entity |

## System Fields

Every entity has auto-created system fields: `Id`, `CreatedOn`, `CreatedBy`, `UpdatedOn`, `UpdatedBy`. These are read-only and must not be included in field definitions or CSV imports.

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
