# Entity Schema Reference

## Creating an Entity

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `entities create` — or any `entities update` that adds, updates, or removes fields — render the full proposed schema (entity name, displayName, description, every field with normalized type and all extras) as a table or formatted JSON block and wait for explicit user approval. Don't run the CLI until the user confirms.

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
- Response: `{ Code: "EntityCreated", Data: { Id: "<entity-id>" } }` — save `Data.Id` for subsequent operations.
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
- **Not** be a SQL, C#, or VB reserved keyword — full list, error string (`"cannot be a reserved word in C# or VB"` / `RESERVED_LANGUAGE_KEYWORDS`), and rename examples are in **data-fabric.md Rule 4**.

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

`entities get` echoes the current constraint values on each field under `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` — read these before authoring an `updateFields` call.

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
- `referenceFolderKey` — **only when the target lives in a different folder** than the parent entity. UUID of the target's folder. Omit when the target is tenant-level OR in the same folder as the parent. See [Cross-folder references](#cross-folder-references) for the full lookup flow.
- The field lives on the *child* (many-side) and points at the *parent* (one-side) — no reverse field on the parent.
- Record value is **always the target record's UUID `Id`**, regardless of which field's UUID was passed as `referenceFieldId` (it controls the join, not the stored value). If the user supplies an email / label, resolve it first via `records query` on the target entity.
- Same shape applies to `FILE` fields: `referenceEntityId` + `referenceFieldId` are both required (and `referenceFolderKey` for cross-folder targets).
- Cue phrases that signal a `RELATIONSHIP` (never substitute `STRING`/`UUID` — **data-fabric.md Rule 12**): *"each order has a Customer"*, *"each report has a Supplier"*, *"each issue belongs to a Project"*.
- If the user didn't name a target entity OR the named one doesn't exist, follow the **pick-or-create flow in data-fabric.md Rule 13** — list candidates via `entities list --native-only`, ask, create only with approval.

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

### Cross-folder references

Folder-scoped entities can hold RELATIONSHIP, FILE, or CHOICE_SET_* fields whose target lives in a **different folder** (or at the tenant level). Use the per-field `referenceFolderKey` to disambiguate; omit it when the target is tenant-level or in the same folder as the parent.

| Target location | Per-field key |
|---|---|
| Same folder as parent (or both tenant-level) | Omit `referenceFolderKey` |
| Different folder | `"referenceFolderKey": "<target-folder-guid>"` |
| Tenant level (target outside any folder) | Omit `referenceFolderKey` |

**Lookup sequence:**

```bash
# 1. Find the target's folder and IDs
uip df entities list --include-folders --output json          # → target entity's Id + FolderId
uip df entities get <target-entity-id> --folder-key <target-folder-key> --output json   # → target field's Id

# 2. Create the parent in its folder, with the cross-folder reference
uip df entities create OrderLine \
  --folder-key <parent-folder-key> \
  --body '{
    "fields":[
      {"fieldName":"order","type":"RELATIONSHIP",
       "referenceEntityId":"<target-entity-uuid>",
       "referenceFieldId":"<target-field-uuid>",
       "referenceFolderKey":"<target-folder-key>",
       "isRequired": true}
    ]
  }' --output json
```

Same shape applies to `addFields` inside `entities update`. For `CHOICE_SET_*` fields whose choice set is folder-scoped in another folder, set `referenceFolderKey` to the choice set's folder key (look it up via `choice-sets list --include-folders`).

### FILE Fields

> **Never include a FILE-typed key in `records insert` or `records update` payloads (data-fabric.md Rule 6).** Expected behavior: the platform silently strips FILE values — UUID, file path, filename, base64, `null` — and returns `Result: Success` with no error. Do not read Success as "the file changed." `records update receipt:null` does **not** clear. `records update receipt:"<uuid>"` does **not** swap. Required path: `files upload` to attach or replace, `files delete` to clear, `files download` to retrieve. Sequence to seed a file on a new row: `records insert` without the FILE column → `files upload <entity-id> <record-id> <field-name> --file <path>` against the returned `Id`. CSV `records import` drops FILE columns too (Rule 20).

```json
{ "fieldName": "EvidenceFile", "type": "FILE", "referenceEntityId": "<EntityAttachment-uuid>", "referenceFieldId": "<EntityAttachment-Name-field-uuid>" }
```

- Point `referenceEntityId` at the tenant's internal `EntityAttachment` entity and `referenceFieldId` at its `Name` field (NVARCHAR). Any other binding produces a field that renders broken in the UiPath Data Fabric UI and rejects subsequent `files upload` calls. The CLI requires both as **UUIDs** — `referenceEntityName` / `referenceFieldName` are rejected with *"Field '…' of type FILE requires both referenceEntityId and referenceFieldId (UUIDs of the target entity and field)"*.
- **The two UUIDs are tenant-specific but shared across every FILE field in that tenant.** Capture them once and reuse on every subsequent FILE field create.
- **`EntityAttachment` is a system entity hidden from CLI access** — it doesn't appear in `entities list` (even with `--include-folders`), and `entities get <EntityAttachment-id>` returns *"Entity '…' not found"*. The only CLI-reachable source is **any existing entity that already has a working FILE field** — read the UUIDs off its `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id`:
  ```bash
  uip df entities list --output json \
    | python3 -c "
  import json, sys
  for e in json.load(sys.stdin)['Data']:
      for f in (e.get('Fields') or []):
          if (f.get('FieldDataType') or {}).get('Name') == 'FILE' \
             and (f.get('ReferenceEntity') or {}).get('Name') == 'EntityAttachment':
              print('referenceEntityId:', f['ReferenceEntity']['Id'])
              print('referenceFieldId :', f['ReferenceField']['Id'])
              sys.exit(0)
  sys.exit(1)
  "
  ```
- **If the scan finds nothing** (no entity in this tenant has a FILE field yet), the CLI cannot bootstrap the UUIDs on its own. Stop and ask the user — they can either supply the `referenceEntityId` + `referenceFieldId` pair directly (e.g. captured from a sibling tenant or from internal docs), or hand off this one-time bootstrap to another channel that has the values. Do NOT guess UUIDs and do NOT fall back to a different field type.
- `files upload` is functional once the binding is correct. Sequence: `entities create` with the FILE field bound → `records insert` (no FILE column) → `files upload <entity-id> <record-id> <field-name> --file <path>` → `records get` echoes the field populated with the server-assigned attachment UUID. Verified end-to-end on `@uipath/data-fabric-tool@1.197.0-alpha.20260617`. Full surface: [`file-attachments.md`](file-attachments.md).

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
uip df entities delete <entity-id> [--folder-key <…>] --yes --reason "<why>" --output json
```

Irreversible — deletes the entity and every record in it. **Before invoking, discover and surface every dependent to the user:**

1. **Inbound relationship references** — run `entities list --output json` and pull every entry whose `Fields[].ReferenceEntity.Id == <entity-id>`. Those entities have FK columns pointing here; after delete, their relationship values become orphaned UUIDs. Ask the user explicitly for each one: *"Entity X has a `<field>` field pointing at this one — delete X, leave it (with dangling FKs), or stop?"*
2. **Choice sets used by this entity's fields** — from `entities get <entity-id>`, pull every `Fields[].ChoiceSetId`. Choice sets are shared resources; they're NOT deleted automatically. Ask the user explicitly for each one: *"Choice set Y is used by this entity's `<field>`. Delete it too (it may be in use by other entities), leave it, or stop?"*

Apply only the choices the user confirms — never cascade silently. If the user is uncertain about any dependent, default to "leave it" rather than deleting.

## Deleting a Field

```bash
uip df entities update <entity-id> \
  [--folder-key <…>] \
  --body '{"removeFields":[{"fieldName":"<exact-field-name>"}]}' \
  --yes --reason "<why>" \
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

Record-level writes against FILE fields (insert / update / import) are anti-patterns documented in data-fabric.md Rule 6 and [`records-query.md` → FILE fields](records-query.md#file-fields--never-write-through-insertupdate). This file covers schema only.

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

`updateFields` identifies fields by their **field ID** (UUID), not by name. Retrieve field IDs from `entities get <entity-id> --output json` — each field in the `Fields` array exposes the UUID as `Id`. **Re-emit it as `id` (lowercase) in the `updateFields` body** — the body key and the response key differ only by case, and a mistyped `Id` is silently treated as missing.

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
# List all entities (includes user, system, and any federated rows)
uip df entities list --output json

# List only native entities (recommended before any write operation)
uip df entities list --native-only --output json

# Get full schema including all fields
uip df entities get <entity-id> --output json
```

**Key fields in `entities list` response:**

| Field | Description |
|-------|-------------|
| `Id` | Entity UUID — required for all `uip df` record and entity commands |
| `Name` | System name (e.g. `BankDetails`) |
| `DisplayName` | Human-readable label shown in the UiPath Data Fabric UI |
| `EntityType` | Row class — observed values: `Entity` (native, read/write), `SystemEntity` (e.g. `SystemUser`; hidden by `--native-only`). Federated rows surface here too. There is **no** `Source` field. |
| `EntityTypeId` | Numeric type code paralleling `EntityType` |
| `FolderId` | Folder GUID, or all-zeros UUID for tenant level |
| `RecordCount`, `StorageSizeInMB`, `UsedStorageSizeInMB` | Storage metrics |

**Key fields in `entities get <id>` response:**

> The GET response is **not** symmetric with the create payload — the type is nested under `FieldDataType.Name`, not a flat `Type`. Parsers that assume symmetry will KeyError. Use the exact keys below.

| Field | Description |
|------------------------|-------------|
| `Fields[].Name` | Exact field name for use in record bodies and CSV headers |
| `Fields[].FieldDataType.Name` | Data type (e.g. `STRING`, `INTEGER`, `CHOICE_SET_SINGLE`, `RELATIONSHIP`, `FILE`) |
| `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | Type-specific constraint values |
| `Fields[].Id` | Field UUID — required for `updateFields` in `entities update` |
| `Fields[].IsRequired` | Whether the field must have a value on insert |
| `Fields[].ChoiceSetId` | Bound choice set UUID (set on `CHOICE_SET_*` fields) |
| `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id` | Target entity/field UUIDs (set on `RELATIONSHIP` / `FILE` fields) |
| `Fields[].FieldDisplayType` | Render hint (`ChoiceSetSingle`, `ChoiceSetMultiple`, `File`, …) — set on complex fields |
| `Fields[].IsForeignKey` | `true` on `RELATIONSHIP` / `FILE` fields |

Before writing records, identify complex fields by `FieldDataType.Name` and resolve lookups: `CHOICE_SET_*` → `choice-sets list-values <choice-set-id>` for `NumberId`s; `RELATIONSHIP` → `records query` on `ReferenceEntity.Id` for target record UUIDs.

**Example — discover an entity before writing records:**
```bash
# 1. Find the entity ID and confirm it is Native (EntityType == "Entity")
uip df entities list --native-only --output json
# e.g. response row: { "Name": "Customer", "Id": "abc-123", "EntityType": "Entity", "DisplayName": "Customer" }

# 2. Get field names for use in record bodies
uip df entities get abc-123 --output json
# e.g. Fields: [{"Name": "FullName", "FieldDataType": {"Name": "STRING"}}, {"Name": "Score", "FieldDataType": {"Name": "INTEGER"}}]

# 3. Insert using exact field names
uip df records insert abc-123 --body '{"FullName":"Alice","Score":95}' --output json
```

## Native vs Federated Entities

Each `entities list` row carries an `EntityType` field (no `Source` field exists):

- `Entity` — native, data stored in Data Fabric, full read/write access
- `SystemEntity` — internal entity (e.g. `SystemUser`); hidden by `--native-only`, not writable
- Federated rows (backed by external connectors like Salesforce, Azure AD) surface here as well — read-only. The exact `EntityType` value for federated rows depends on the connector; verify by listing the tenant. `--native-only` filters them out alongside `SystemEntity`.

**Only native entities support record creation, update, delete, and import.**

> Creating federated entities or linking entities to external connectors is **not currently supported**. This cannot be done via the CLI or the UiPath portal.
