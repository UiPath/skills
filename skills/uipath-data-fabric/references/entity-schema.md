# Entity Schema Reference

## Creating an Entity

> **Preview-then-confirm gate (SKILL.md Rule 14).** Before invoking `entities create` — or any `entities update` that adds, updates, or removes fields — render the full proposed schema (entity name, displayName, description, every field with normalized type and all extras) as a table or formatted JSON block and wait for explicit user approval. Don't run the CLI until the user confirms.

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
| `RELATIONSHIP` | UNIQUEIDENTIFIER | FK link to another entity — requires `referenceEntityId` (target entity UUID) + `referenceFieldId` (target field UUID) |

### Normalizing user-facing type names

User prompts use natural-language casing and synonyms; the CLI accepts only the exact UPPERCASE enum value above. Two patterns:

**1. Case-fold — trivial 1:1.** When the user's word matches an enum value modulo case, just uppercase it before invoking. Do this silently:

| User says | Send to CLI |
|---|---|
| `boolean` / `Boolean` | `BOOLEAN` |
| `string` / `String` | `STRING` |
| `integer` / `Integer` | `INTEGER` |
| `decimal` / `Decimal` | `DECIMAL` |
| `date` / `Date` | `DATE` |
| `datetime` / `DateTime` | `DATETIME` |
| `uuid` / `Uuid` / `Guid` | `UUID` |
| `file` / `File` | `FILE` |
| `relationship` / `Relationship` | `RELATIONSHIP` |

**2. Disambiguate — synonyms that map to multiple enum values.** When the user's phrasing covers more than one type, **ask before picking**. Never default silently:

| User phrasing | Candidates | What to ask |
|---|---|---|
| `text`, `short text`, `long text`, `paragraph` | `STRING` or `MULTILINE_TEXT` | "Expected length? `STRING` is capped at 4000 chars; `MULTILINE_TEXT` allows up to 10000." |
| `number`, `numeric` | `INTEGER`, `BIG_INTEGER`, `DECIMAL`, `FLOAT`, `DOUBLE` | "Whole or fractional? If fractional, how many decimal places? If whole, are values ever > 2³¹?" |
| `money`, `price`, `amount` | `DECIMAL` (almost always) | Default to `DECIMAL` with `decimalPrecision: 2` and confirm. |
| `timestamp`, `datetime` | `DATETIME` or `DATETIME_WITH_TZ` | "Does timezone matter? `DATETIME` is wall-clock; `DATETIME_WITH_TZ` carries offset." |
| `choice`, `enum`, `picklist`, `dropdown` | `CHOICE_SET_SINGLE` or `CHOICE_SET_MULTIPLE` | "One value per record, or multiple?" |
| `tags`, `labels`, `multi-pick` | `CHOICE_SET_MULTIPLE` | Default; confirm. |
| `link to <entity>`, `belongs to`, `foreign key` | `RELATIONSHIP` | Use pick-or-create flow for the target entity (see [Relationship Fields](#relationship-fields)). |
| `attachment`, `upload`, `document` | `FILE` | Default; confirm. |
| `auto number`, `counter`, `serial` | `AUTO_NUMBER` | Default; confirm. |

If the CLI rejects a `--body` with *"Cannot read properties of undefined (reading 'sqlTypeName')"*, the `type` value didn't match a known enum — almost always a casing issue. Re-emit with the exact UPPERCASE value from the table above.

## Field Definition Object

### Name Validation

Both entity names and field names must:
- Start with a letter (`[a-zA-Z]`)
- Contain only letters, digits, and underscores (`[a-zA-Z0-9_]`)
- Be 3–100 characters long
- **Not** be a SQL, C#, or VB reserved keyword — full list, error string (`"cannot be a reserved word in C# or VB"` / `RESERVED_LANGUAGE_KEYWORDS`), and rename examples are in **SKILL.md Rule 4**.

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
  "defaultValue": "",
  "lengthLimit": 200
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
| `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision` | number | type-specific | Advanced per-type constraints — see below |

### Advanced Field Constraints

Accepted on `entities create` and on `addFields` / `updateFields` in `entities update`. Each constraint applies only to specific types — passing one to an unsupported type errors with *"Field '<name>' of type <TYPE> does not accept <option>"*. `minValue` must be strictly less than `maxValue`.

| Constraint | Allowed types | Range |
|------------|---------------|-------|
| `lengthLimit` | `STRING` (1–4000), `MULTILINE_TEXT` (1–10000) | — |
| `maxValue` / `minValue` | `INTEGER`, `BIG_INTEGER`, `DECIMAL`, `FLOAT`, `DOUBLE` | ±9,007,199,254,740,991 |
| `decimalPrecision` | `DECIMAL`, `FLOAT`, `DOUBLE` | 0–10 |

```bash
uip df entities create "Orders" \
  --body '{
    "fields": [
      {"fieldName": "ProductName", "type": "STRING",  "lengthLimit": 500, "isRequired": true},
      {"fieldName": "Price",       "type": "DECIMAL", "decimalPrecision": 4, "maxValue": 999999, "minValue": 0},
      {"fieldName": "Quantity",    "type": "INTEGER", "maxValue": 10000, "minValue": 1}
    ]
  }' \
  --output json
```

Change a constraint after creation via `updateFields` (use the field UUID from `entities get`):

```bash
uip df entities update <entity-id> \
  --body '{"updateFields":[{"id":"<field-id>","lengthLimit":1000}]}' \
  --output json
```

`entities get` echoes the current constraint values on each field under `Fields[].fieldDataType.{lengthLimit,maxValue,minValue,decimalPrecision}` — read these before authoring an `updateFields` call.

### Choice Set Fields

```json
{ "fieldName": "Status", "type": "CHOICE_SET_SINGLE",   "choiceSetId": "<choice-set-id>" }
{ "fieldName": "Tags",   "type": "CHOICE_SET_MULTIPLE", "choiceSetId": "<choice-set-id>" }
```

`choiceSetId` is the UUID from `uip df choice-sets list`. If a needed choice set doesn't exist, ask the user — then author it with `choice-sets create` + `choice-set-values create` (do not fall back to `STRING`). Record value is the integer `NumberId` (single) or integer array (multi), from `choice-sets list-values`. Filter semantics — including the `CHOICE_SET_MULTIPLE` `=` vs `contains` distinction — are in [records-query.md](records-query.md#filtering-on-choice-set-fields). Full workflow in [`choice-sets.md`](choice-sets.md).

### Relationship Fields

```json
{ "fieldName": "customerId", "type": "RELATIONSHIP", "referenceEntityId": "<target-entity-uuid>", "referenceFieldId": "<target-field-uuid>" }
```

- `referenceEntityId` — UUID of the target entity. Get it from `entities list --native-only` (the `Id` column). Target must exist and be native (no federated targets).
- `referenceFieldId` — UUID of the join field on the target entity. Get it from `entities get <target-entity-id>` (`Fields[].Id`). Configures join-on-read; the stored value is still the target record's `Id`.
- The field lives on the *child* (many-side) and points at the *parent* (one-side) — no reverse field on the parent.
- Record value is **always the target record's UUID `Id`**, regardless of which field's UUID was passed as `referenceFieldId` (it controls the join, not the stored value). If the user supplies an email / label, resolve it first via `records query` on the target entity.
- Same shape applies to `FILE` fields: `referenceEntityId` + `referenceFieldId` are both required.
- Cue phrases that signal a `RELATIONSHIP` (never substitute `STRING`/`UUID` — **SKILL.md Rule 12**): *"each order has a Customer"*, *"each report has a Supplier"*, *"each issue belongs to a Project"*.
- If the user didn't name a target entity OR the named one doesn't exist, follow the **pick-or-create flow in SKILL.md Rule 13** — list candidates via `entities list --native-only`, ask, create only with approval.

```bash
# 1. Discover target entity + field UUIDs
uip df entities list --native-only --output json   # → find Customer entity's Id
uip df entities get <customer-entity-id> --output json   # → find Id field's Id under Fields[]

# 2. Resolve email → record Id, then insert
uip df records query <customer-entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Email","operator":"=","value":"alice@example.com"}]},"selectedFields":["Id"]}' \
  --output json
uip df records insert <child-entity-id> --body '{"customerId":"<resolved-uuid>","amount":250}' --output json
```

### FILE Fields

```json
{ "fieldName": "EvidenceFile", "type": "FILE", "referenceEntityId": "<EntityAttachment-uuid>", "referenceFieldId": "<EntityAttachment-Name-field-uuid>" }
```

- Point `referenceEntityId` at the tenant's internal `EntityAttachment` entity and `referenceFieldId` at its `Name` field. This is the only target shape the platform accepts — any other binding produces a field that renders broken in the UiPath Data Fabric UI with no in-place fix.
- The `EntityAttachment` UUIDs are tenant-specific. Discover them once and reuse across every FILE field in the tenant:
  ```bash
  # EntityAttachment entity Id
  uip df entities list --output json | python3 -c "import json,sys;print([e['Id'] for e in json.load(sys.stdin)['Data'] if e['Name']=='EntityAttachment'][0])"
  # Its Name-field Id (use this as referenceFieldId)
  uip df entities get <EntityAttachment-id> --output json | python3 -c "import json,sys;print([f['Id'] for f in json.load(sys.stdin)['Data']['Fields'] if f['Name']=='Name'][0])"
  ```
  Alternative: inspect any existing entity that already has a FILE field — `entities get` echoes the target as `ReferenceEntity.Id` + `ReferenceField.Id`.
- CLI `files upload` against the field is currently unusable — upload via the UiPath Data Fabric UI instead. Status and workaround: [`file-attachments.md`](file-attachments.md).

### Combined Example — mixing scalar, choice-set, and relationship fields

Complex types accept the same standard field options as scalars — `isRequired`, `isUnique`, `displayName`, `description`, `defaultValue`, `isRbacEnabled`, `isEncrypted`, and the type-specific constraints (`lengthLimit`, `maxValue`/`minValue`, `decimalPrecision`). The only extras unique to complex types are `choiceSetId` (for `CHOICE_SET_*`) and `referenceEntityId` + `referenceFieldId` (for `RELATIONSHIP` and `FILE`).

```bash
# Prereqs: target entity exists; choice set exists (look up ID)
uip df entities create "Expense" --body '{
  "displayName": "Expense",
  "description": "Reimbursable expenses with category, tags, and submitter",
  "fields": [
    {"fieldName":"invoiceNumber", "type":"STRING",  "isRequired": true, "isUnique": true, "lengthLimit": 50,
     "displayName":"Invoice Number"},
    {"fieldName":"amount",        "type":"DECIMAL", "isRequired": true, "decimalPrecision": 2, "minValue": 0,
     "displayName":"Amount (USD)"},
    {"fieldName":"notes",         "type":"MULTILINE_TEXT", "lengthLimit": 2000},
    {"fieldName":"category",      "type":"CHOICE_SET_SINGLE",   "choiceSetId":"<choice-set-id>",
     "isRequired": true, "displayName":"Category"},
    {"fieldName":"tags",          "type":"CHOICE_SET_MULTIPLE", "choiceSetId":"<choice-set-id>"},
    {"fieldName":"customerId",    "type":"RELATIONSHIP", "referenceEntityId":"<customer-entity-uuid>", "referenceFieldId":"<customer-id-field-uuid>",
     "isRequired": true, "displayName":"Customer"}
  ]
}' --output json
```

## Deleting an Entity

```bash
uip df entities delete <entity-id> --yes --reason "<why>" --output json
```

Irreversible — deletes the entity and every record in it. **Before invoking, discover and surface every dependent to the user:**

1. **Inbound relationship references** — run `entities list --output json` and pull every entry whose `Fields[].ReferenceEntity.Id == <entity-id>`. Those entities have FK columns pointing here; after delete, their relationship values become orphaned UUIDs. Ask the user explicitly for each one: *"Entity X has a `<field>` field pointing at this one — delete X, leave it (with dangling FKs), or stop?"*
2. **Choice sets used by this entity's fields** — from `entities get <entity-id>`, pull every `Fields[].ChoiceSetId`. Choice sets are shared resources; they're NOT deleted automatically. Ask the user explicitly for each one: *"Choice set Y is used by this entity's `<field>`. Delete it too (it may be in use by other entities), leave it, or stop?"*

Apply only the choices the user confirms — never cascade silently. If the user is uncertain about any dependent, default to "leave it" rather than deleting.

## Deleting a Field

```bash
uip df entities update <entity-id> \
  --body '{"removeFields":[{"fieldName":"<exact-field-name>"}]}' \
  --confirm --reason "<why>" \
  --output json
```

Irreversible — drops the column and every record's value in it. Note the body shape: `removeFields` takes `{"fieldName": "..."}`, **NOT** `{"id": "..."}` (that's `updateFields`). Mixing those forms returns *"Each field in removeFields must include a non-empty 'fieldName' string"*.

Before invoking, surface the impact to the user:

- **RELATIONSHIP / FILE fields** — confirm no flow / coded app reads the value. The FK column disappears entirely.
- **CHOICE_SET_* fields** — the choice set itself is shared and isn't affected; only this entity's link to it is removed.
- **System fields** (`Id`, `CreatedBy`, …) can't be removed regardless.

Response: `{ Code: "EntityUpdated", Data: { Id, RemovedFields: ["<name>"], Reason } }`.

## Not Supported

| Operation | Action |
|-----------|--------|
| Change a field's data type | Not supported — type is fixed at creation and cannot be changed via `updateFields` |
| Field name matching a SQL / language keyword | API returns `RESERVED_LANGUAGE_KEYWORDS` — rename before retrying (see Name Validation above) |
| Upload a file to a `FILE` field via `uip df files upload` | CLI insists on `referenceEntityId`/`referenceFieldId` at field create, then uploads fail with *"Relationship violation"* against arbitrary targets. No public attachment-storage entity is documented. Treat FILE upload as unusable via CLI until the target-entity contract is clarified — surface the gap to the user; don't attempt. |

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

`updateFields` entry supports: `id` (required), `displayName`, `description`, `isRequired`, `isUnique`, `isRbacEnabled`, `isEncrypted`, `defaultValue`, `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision`. The four constraint keys follow the per-type allow-list in [Advanced Field Constraints](#advanced-field-constraints).

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
# List all entities (shows Source: Native or Federated)
uip df entities list --output json

# List only native entities (recommended before any write operation)
uip df entities list --native-only --output json

# Get full schema including all fields
uip df entities get <entity-id> --output json
```

**Key fields in `entities list` response:**

| Field | Description |
|-------|-------------|
| `ID` | Entity UUID — required for all `uip df` record and entity commands |
| `Name` | CamelCase system name (e.g. `BankDetails`) |
| `DisplayName` | Human-readable label shown in the UiPath Data Fabric UI |
| `Source` | `Native` (read/write) or `Federated (ConnectorName)` (read-only) |

**Key fields in `entities get <id>` response:**

| Field | Description |
|-------|-------------|
| `Fields[].FieldName` | Exact field name for use in record bodies and CSV headers |
| `Fields[].Type` | Data type (e.g. `STRING`, `INTEGER`, `CHOICE_SET_SINGLE`, `RELATIONSHIP`) |
| `Fields[].ID` | Field UUID — required for `updateFields` in `entities update` |
| `Fields[].IsRequired` | Whether the field must have a value on insert |

`entities get` echoes the complex-field bindings under each field: `Fields[].ChoiceSetId` for `CHOICE_SET_*`, and `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id` for `RELATIONSHIP` / `FILE`. `Fields[].IsForeignKey` is `true` on relationship/file fields. Use these to recover the binding without asking the user.

Before writing records, identify complex fields by `Type` and resolve lookups: `CHOICE_SET_*` → `choice-sets list-values <choice-set-id>` for `NumberId`s; `RELATIONSHIP` → `records query` on `ReferenceEntity.Id` for target record UUIDs.

**Example — discover an entity before writing records:**
```bash
# 1. Find the entity ID and confirm it is Native
uip df entities list --native-only --output json
# e.g. response: { "Name": "Customer", "ID": "abc-123", "Source": "Native" }

# 2. Get field names for use in record bodies
uip df entities get abc-123 --output json
# e.g. Fields: [{"FieldName": "FullName", "Type": "STRING"}, {"FieldName": "Score", "Type": "INTEGER"}]

# 3. Insert using exact field names
uip df records insert abc-123 --body '{"FullName":"Alice","Score":95}' --output json
```

## Native vs Federated Entities

The `entities list` output includes a `Source` field:

- `Native` — data stored in Data Fabric, full read/write access
- `Federated (ConnectorName)` — backed by an external connector (e.g. Salesforce, Azure AD), read-only

**Only native entities support record creation, update, delete, and import.**

> Creating federated entities or linking entities to external connectors is **not currently supported**. This cannot be done via the CLI or the UiPath portal.
