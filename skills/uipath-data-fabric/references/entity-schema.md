# Entity Schema Reference

## Creating an Entity

```bash
uip df entities create "MyEntity" \
  --description "Optional description" \
  --fields '[
    {"name":"title","type":"text"},
    {"name":"score","type":"number"},
    {"name":"active","type":"boolean"},
    {"name":"createdDate","type":"date"}
  ]' \
  --format json
```

Response includes `EntityId` — save this for subsequent operations.

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

## Field Definition Object

```json
{
  "name": "fieldName",
  "type": "text",
  "displayName": "Optional display label",
  "isRequired": false
}
```

- `name` is required and becomes the technical name (lowercase, no spaces)
- `type` defaults to `"text"` if omitted

## Adding / Removing Fields

Fields can be added or removed after entity creation:

```bash
# Add a field
uip df entities add-field <entity-id> myNewField --type decimal --format json

# Remove a field
uip df entities remove-field <entity-id> myOldField --format json
```

**Warning**: Removing a field deletes all data stored in that field for every record.

## System Fields

Every entity has auto-created system fields: `Id`, `CreatedOn`, `CreatedBy`, `UpdatedOn`, `UpdatedBy`. These are read-only and excluded from field manipulation commands.

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
