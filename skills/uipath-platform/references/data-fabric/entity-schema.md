# Entity Schema Reference

## Creating an Entity

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `entities create` — or any `entities update` that adds, updates, or removes fields — render the full proposed schema (entity name, displayName, description, every field with normalized type and all extras) as a table or formatted JSON block and wait for explicit user approval. Don't run the CLI until the user confirms.

```bash
uip df entities create "MyEntity" \
  --body '{
    "displayName": "My Entity",
    "description": "Optional description",
    "fields": [
      {"name": "Title", "type": "STRING", "isRequired": true},
      {"name": "Score", "type": "DECIMAL", "decimalPrecision": 0},
      {"name": "Active", "type": "BOOLEAN"},
      {"name": "CreatedDate", "type": "DATE"}
    ]
  }' \
  --output json
```

- `fields` is required; every entry needs `name`. `displayName`, `description`, and `isRbacEnabled` are optional top-level keys.
- Response: `{ Code: "EntityCreated", Data: { Id: "<entity-id>" } }`; save `Data.Id`. Alternatively pass `--file <path>` containing the same structure.

## Supported Field Types

Pass the exact case-sensitive `EntityFieldDataType` UPPERCASE string and use only this table. The broader SDK enum (`INTEGER`, `BIG_INTEGER`, `FLOAT`, `DOUBLE`, `UUID`, `DATETIME`) renders broken in the UiPath Data Fabric UI; see [UI-broken types](#ui-broken-types-do-not-use).

| CLI type | SQL | Notes |
|---|---|---|
| `STRING` | NVARCHAR | Short text; `lengthLimit` ≤4000 |
| `MULTILINE_TEXT` | NVARCHAR(MAX) | Long text; `lengthLimit` ≤10000 |
| `MULTILINE_MAX` | NVARCHAR(MAX) | Very large text; `lengthLimit` is a UTF-16 byte budget, 1–131072, default 128 KB ≈ 65,536 chars; no filter/sort; list/query returns a preview; see [MULTILINE_MAX fields](#multiline_max-fields) |
| `DECIMAL` | DECIMAL | All numbers; `decimalPrecision: 0` whole, `2` money |
| `BOOLEAN` | BIT | true/false |
| `DATE` | DATE | Date only |
| `DATETIME_WITH_TZ` | DATETIMEOFFSET | Date/time/timezone; only UI-compatible timestamp |
| `FILE` | UNIQUEIDENTIFIER | Attachment; server auto-wires references; see [FILE Fields](#file-fields) |
| `CHOICE_SET_SINGLE` | INT | Requires `choiceSetId`; only valid `INT`-backed field |
| `CHOICE_SET_MULTIPLE` | NVARCHAR | Requires `choiceSetId` |
| `AUTO_NUMBER` | DECIMAL | Auto-incrementing number |
| `RELATIONSHIP` | UNIQUEIDENTIFIER | Requires `referenceEntityId` + `referenceFieldId`; see [Relationship Fields](#relationship-fields) |

### UI-broken types — do NOT use

CLI accepts these and `entities create` returns `Success`, but the UiPath Data Fabric UI cannot render/edit/filter the column. Substitute in the Rule 14 preview and get approval, even if the user names one.

| Never emit | Substitute |
|---|---|
| `INTEGER` / `BIG_INTEGER` | `DECIMAL` with `decimalPrecision: 0` |
| `FLOAT` / `DOUBLE` | `DECIMAL` with required `decimalPrecision` |
| `UUID` | `RELATIONSHIP` (if FK) or `STRING` (opaque id); ask |
| `DATETIME` (no TZ) | `DATETIME_WITH_TZ` |

### Normalizing user-facing type names

CLI needs UPPERCASE enums. Silent case-fold UI-compatible names (`boolean`→`BOOLEAN`, `decimal`→`DECIMAL`, `file`→`FILE`, `relationship`→`RELATIONSHIP`, etc.). For UI-broken or ambiguous names, substitute and confirm:

| User phrasing | Ask |
|---|---|
| `text` / `long text` / `paragraph` / `document body` | `STRING` (≤4000), `MULTILINE_TEXT` (≤10000), or `MULTILINE_MAX` (up to ≈65,536 chars, no filter/sort — see [MULTILINE_MAX fields](#multiline_max-fields)); ask expected length |
| `number` / `int` / `integer` / `float` / `double` | `DECIMAL`; ask decimal places (`0` whole, `2` money) |
| `money` / `price` / `amount` | Default `DECIMAL` with `decimalPrecision: 2`; confirm |
| `timestamp` / `datetime` | Default `DATETIME_WITH_TZ`; confirm |
| `choice` / `enum` / `picklist` | `CHOICE_SET_SINGLE` vs `CHOICE_SET_MULTIPLE`; ask one or many |
| `tags` / `labels` | Default `CHOICE_SET_MULTIPLE`; confirm |
| `link to X` / `belongs to` / `foreign key` | `RELATIONSHIP`; use [pick-or-create](#relationship-fields) |
| `attachment` / `upload` / `document` | `FILE`; confirm |
| `uuid` / `guid` | `RELATIONSHIP` if FK, otherwise `STRING`; ask |

If `--body` fails with *"Cannot read properties of undefined (reading 'sqlTypeName')"*, re-emit with the exact UPPERCASE type from the table; the value almost always had wrong casing or was not a known enum.

### MULTILINE_MAX fields

1. **Not filterable, not sortable.** Any `queryFilters` or `sortOptions` entry naming a `MULTILINE_MAX` field → 400: *"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."* / *"Sort field '<name>' is of type MULTILINE_MAX and cannot be used for sorting."* Never offer the field in filter/sort predicates. See [filter contract](filter-platform-contract.md#operator-support-by-field-type).
2. **List/query reads return a preview, not the guaranteed full value.** Depending on the tenant, `records list` / `records query` return either the value truncated to 10,000 characters with a `...[Truncated]` suffix, or a size marker starting `HasValue=true Length=N` (sometimes with a trailing hint). Encrypted fields always read back `HasValue=true Encrypted=true`. Only `records get <entity-id> <record-id>` returns the full value. Read + write-back rules are in [records-query.md → MULTILINE_MAX fields](records-query.md#multiline_max-fields--preview-vs-full-content).
3. **On a 400 from `entities create` / `addFields` naming the type**, surface the error verbatim — do NOT retry or silently substitute `MULTILINE_TEXT` (Rule 18).

```bash
uip df entities create "Documents" \
  --body '{"fields":[{"name":"Title","type":"STRING","isRequired":true},{"name":"Body","type":"MULTILINE_MAX"}]}' \
  --output json
```

`lengthLimit` is optional: UTF-16 **byte** budget, 1–131072; omitted → 131072 (platform max ≈ 65,536 chars; 65,536-char insert succeeds and 65,537 is rejected with *"value … is 131074 bytes, exceeds the 131072-byte limit"*).

## Field Definition Object

### Name Validation

Entity names must start with a letter (`[a-zA-Z]`), contain only letters, digits, and underscores (`[a-zA-Z0-9_]`), be 3–100 characters, and not be a C# or VB reserved keyword. The CLI also rejects some SQL-reserved words such as `Order`, while `Status` and `Key` are accepted. Surface the actual validation error and ask for a domain-specific rename; do not maintain a speculative local keyword list. See **data-fabric.md Rule 4**.

Field names follow the same length and starting-letter rules but contain **letters and digits only** (`[a-zA-Z0-9]`); underscores are rejected. A field name cannot equal its entity name ignoring case. Reserved field names, case-insensitive: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`.

Within one create/add batch, field names and effective display names must each be unique ignoring case. An entity supports at most 10 `MULTILINE_MAX` fields.

### All Field Options

```json
{
  "name": "AccountNumber",
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
|---|---|---|---|
| `name` | string | required | 3–100 chars, starts with letter, letters/digits only |
| `type` | `EntityFieldDataType` | `STRING` | See type table |
| `displayName` | string | name | Max 128 chars |
| `description` | string | `""` | Max 512 chars |
| `isRequired` | boolean | `false` | Required on insert |
| `isUnique` | boolean | `false` | Unique across records |
| `isRbacEnabled` | boolean | `false` | Field RBAC |
| `isEncrypted` | boolean | `false` | Encrypted at rest |
| `defaultValue` | string | — | Always a string representation |
| `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision` | number | type-specific | See [Advanced Field Constraints](#advanced-field-constraints) |

### Round-trip: `get` shape into `create` / `update`

Pass a field from `entities get` directly into `create` `fields` or `update` `addFields`; the CLI normalizes it. Keep each object wholly one shape. Read-only keys (`Id`, `System`, `PrimaryKey`, …) are dropped.

| Read (`entities get`) | Write (`create` / `addFields`) |
|---|---|
| `Name` | `name` |
| `FieldDataType.Name` | `type` |
| `FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | `lengthLimit`/`maxValue`/`minValue`/`decimalPrecision` |
| `DisplayName`, `Description`, `DefaultValue` | `displayName`, `description`, `defaultValue` |
| `IsRequired`, `IsUnique`, `IsRbacEnabled`, `IsEncrypted`, `IsHiddenField` | `isRequired`, `isUnique`, `isRbacEnabled`, `isEncrypted`, `isHiddenField` |
| `ReferenceEntity.Id`, `ReferenceField.Id`, `ReferenceChoiceSet.Id` | `referenceEntityId`, `referenceFieldId`, `choiceSetId` |

### Advanced Field Constraints

Accepted on `entities create` and `addFields` / `updateFields` in `entities update`. Each applies only to its listed types; unsupported options error with *"Field '<name>' of type <TYPE> does not accept <option>"*. `minValue` must be ≤ `maxValue`.

| Constraint | Allowed type | Range |
|---|---|---|
| `lengthLimit` | `STRING` (1–4000), `MULTILINE_TEXT` (1–10000), `MULTILINE_MAX` (1–131072; UTF-16 **bytes**, ≈2 per char) | — |
| `maxValue` / `minValue` | `DECIMAL` | ±9,007,199,254,740,991 |
| `decimalPrecision` | `DECIMAL` — `0` whole, `2` money | 0–10 |

```bash
uip df entities create "Orders" \
  --body '{
    "fields": [
      {"name": "ProductName", "type": "STRING",  "lengthLimit": 500, "isRequired": true},
      {"name": "Price",       "type": "DECIMAL", "decimalPrecision": 4, "maxValue": 999999, "minValue": 0},
      {"name": "Quantity",    "type": "DECIMAL", "decimalPrecision": 0, "maxValue": 10000, "minValue": 1}
    ]
  }' \
  --output json
```

Change constraints after creation with the field UUID from `entities get`:

```bash
uip df entities update <entity-id> \
  --body '{"updateFields":[{"id":"<field-id>","lengthLimit":1000}]}' \
  --output json
```

`entities get` echoes current values under `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}`; read them before authoring `updateFields`.

### Choice Set Fields

```json
{ "name": "Status", "type": "CHOICE_SET_SINGLE",   "choiceSetId": "<choice-set-id>" }
{ "name": "Tags",   "type": "CHOICE_SET_MULTIPLE", "choiceSetId": "<choice-set-id>" }
```

`choiceSetId` is the UUID from `uip df choice-sets list`. If absent, ask the user, then author it with `choice-sets create` + `choice-set-values create`; do not fall back to `STRING`. Record values are integer `NumberId` (single) or integer array (multi), from `choice-sets list-values`. Filter semantics, including `CHOICE_SET_MULTIPLE` `=` vs `contains`, are in [records-query.md](records-query.md#filtering-on-choice-set-fields). Full workflow: [`choice-sets.md`](choice-sets.md).

### Relationship Fields

```json
{ "name": "customerId", "type": "RELATIONSHIP", "referenceEntityId": "<target-entity-uuid>", "referenceFieldId": "<target-field-uuid>" }
```

- `referenceEntityId` is the target entity UUID from `entities list --native-only` (`Id`); the target must exist and be native.
- `referenceFieldId` is the target **display field**, controlling pickers, lists, and UI rendering. **Always confirm with the user** which field to display (`Name`, `Email`, `Title`, etc.); do not default to target `Id`. List candidates from `entities get <target-entity-id>` (`Fields[].Name`/`DisplayName` for human-readable scalar fields) and raise an `AskUserQuestion` dropdown if more than one fits. Stored values are always target record UUID `Id`; `referenceFieldId` is only the join-and-render hint. Auto Mode does not waive confirmation.
- `referenceFolderKey` applies only to `RELATIONSHIP`; pass it whenever the target is folder-scoped, including same-folder targets; omit for tenant-level targets. `CHOICE_SET_*` resolves scope from `choiceSetId`; `FILE` is auto-wired. See [Cross-folder references](#cross-folder-references).
- The field is on the child (many-side) and points to the parent (one-side); there is no reverse field on the parent.
- If given an email/label, resolve it first via `records query` on the target entity.
- `FILE` fields take no reference fields; see [FILE Fields](#file-fields).
- Phrases such as *"each order has a Customer"*, *"each report has a Supplier"*, and *"each issue belongs to a Project"* signal `RELATIONSHIP`; never substitute `STRING`/`UUID` (**data-fabric.md Rule 12**).
- If no target is named or it does not exist, follow **data-fabric.md Rule 13**: list candidates via `entities list --native-only`, ask, and create only with approval.

### Cross-folder references

`RELATIONSHIP` and `CHOICE_SET_*` bindings require parent and target to share scope class: both tenant-level or both folder-scoped. Folder-to-folder across different folders works; tenant/folder crossing does not. `FILE` is excluded because the server binds it to the platform-managed attachment entity.

- **`RELATIONSHIP`**: pass `referenceFolderKey` whenever the target is folder-scoped, including same-folder bindings; omission makes the server treat it as tenant-level and reject it.
- **`CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE`**: do **NOT** pass `referenceFolderKey` at the API level; the backend resolves the folder from `choiceSetId`, and passing it may be rejected.

| Parent scope | Target scope | Allowed? | `referenceFolderKey` for `RELATIONSHIP` | `referenceFolderKey` for `CHOICE_SET_*` |
|---|---|---|---|---|
| Tenant | Tenant | ✅ | Omit | Omit |
| Folder A | Folder A | ✅ | `<folder-A-guid>` — required | Omit; server resolves from `choiceSetId` |
| Folder A | Folder B | ✅ | `<folder-B-guid>` | Omit; server resolves from `choiceSetId` |
| Folder | Tenant user-authored entity / choice set | ❌ | n/a — not supported | n/a — not supported |
| Tenant | Folder | ❌ | n/a — not supported | n/a — not supported |

Surface the constraint before invoking `entities create` / `addFields` when parent and target cross the tenant ↔ folder boundary. Do not silently fall back to another type — see Rule 18 (no silent substitution).

### FILE Fields

> **Never include a FILE-typed key in `records insert` or `records update` payloads (data-fabric.md Rule 6).** The platform silently strips FILE values — UUID, file path, filename, base64, `null` — and returns `Result: Success` with no error. Do not interpret Success as a file change. `records update receipt:null` does **not** clear; `records update receipt:"<uuid>"` does **not** swap. Run `files upload` to attach/replace, `files delete` to clear, and `files download` to retrieve. Seed a new row by running `records insert` without the FILE column, then run `files upload <entity-id> <record-id> <field-name> --file <path>` using the returned `Id`. CSV `records import` also drops FILE columns (Rule 20).

```json
{ "name": "EvidenceFile", "type": "FILE" }
```

FILE fields require and accept no reference fields: the server auto-wires tenant `EntityAttachment`; supplied `referenceEntityId` / `referenceFieldId` are stripped by the SDK. Never ask which field to bind. Rule 14 display-field selection applies only to `RELATIONSHIP`.

Write sequence: `entities create` (FILE field, no refs) → `records insert` (no FILE column, Rule 6) → `files upload <entity-id> <record-id> <field-name> --file <path>`. Full surface: [`file-attachments.md`](file-attachments.md).

## Deleting an Entity

```bash
uip df entities delete <entity-id> [--folder-key <…>] --yes --reason "<why>" --output json
```

Irreversible; deletes the entity and every record. **Before invoking, discover and surface every dependent:**

1. **Inbound relationship references** — run `entities list --output json` and pull every entry whose `Fields[].ReferenceEntity.Id == <entity-id>`. Those entities have FK columns pointing here; after delete, their relationship values become orphaned UUIDs. Ask explicitly for each: *"Entity X has a `<field>` field pointing at this one — delete X, leave it (with dangling FKs), or stop?"*
2. **Choice sets used by this entity's fields** — from `entities get <entity-id>`, pull every `Fields[].ChoiceSetId`. Choice sets are shared and are NOT deleted automatically. Ask explicitly for each: *"Choice set Y is used by this entity's `<field>`. Delete it too (it may be in use by other entities), leave it, or stop?"*

Apply only confirmed choices; never cascade silently. If the user is uncertain about any dependent, default to "leave it" rather than deleting.

## Deleting a Field

```bash
uip df entities update <entity-id> \
  [--folder-key <…>] \
  --body '{"removeFields":[{"name":"<exact-field-name>"}]}' \
  --yes --reason "<why>" \
  --output json
```

Irreversible; drops the column and every record value. `removeFields` takes `{"name":"..."}`, **not** `{"id":"..."}` (`updateFields` uses `id`); mixing them returns *"Each field in removeFields must include a non-empty 'name' string"*.

Before invoking, surface impact and run the cascade-ask (data-fabric.md Rule 11):

- **CHOICE_SET_*** — resolve `Fields[].ChoiceSetId` from `entities get <id>`; list other bindings with `entities list --output json` and `Fields[].ChoiceSetId == <id>`; raise an `AskUserQuestion` dropdown: `Delete only the field` · `Also delete choice set <Name> (<id>)` · `Stop`. For `Also delete …`, run the choice-set-delete flow ([`choice-sets.md` → Deleting a choice set](choice-sets.md#deleting-a-choice-set)) with dependent discovery.
- **RELATIONSHIP** — warn consumers may depend on it; resolve `Fields[].ReferenceEntity.Id`; list inbound references with `entities list --output json` and `Fields[].ReferenceEntity.Id == <id>`; raise: `Delete only the field` · `Also delete target entity <Name> (<id>)` · `Stop`. For `Also delete …`, run the entity-delete flow (Rule 10) with dependent discovery.
- **FILE** — drop only the column; its `referenceEntityId` is platform-managed FILE storage, so do not offer to delete it.
- **System fields** (`Id`, `CreatedBy`, …) cannot be removed.

Response: `{ Code: "EntityUpdated", Data: { Id, RemovedFields: ["<name>"], Reason } }`.

## Not Supported

| Operation | Action |
|---|---|
| Change a field's data type | Not supported; type is fixed at creation and cannot change via `updateFields` |
| Toggle `isUnique` on an existing field | Not supported; it is fixed at creation. `updateFields` with `isUnique: true/false` returns `Result: Success` but silently ignores it; UI toggle is **disabled**. To enforce uniqueness: confirm recreation, `removeFields` it (drops values; see Rule 11), then `addFields` with `isUnique: true`. Do NOT report success on a no-op `updateFields`; verify via `entities get` (see Verify-after-update below). |
| Field name rejected as reserved | C#/VB keywords return `RESERVED_LANGUAGE_KEYWORDS`; CLI also rejects some SQL words such as `Order`, while `Status` and `Key` are accepted. Surface the actual error and ask for a domain-specific rename. |
| Rename an entity (`name`) | Not supported; name is fixed at creation. `entities update` changes only `displayName` / `description`; top-level `name` is rejected. Create a new entity instead. |

Record-level FILE writes (insert/update/import) are anti-patterns documented in data-fabric.md Rule 6 and [`records-query.md` → FILE fields](records-query.md#file-fields). This file covers schema only.

## Updating an Entity

Use `entities update` to add fields, modify field metadata, or update entity properties.

```bash
# Add new fields
uip df entities update <entity-id> \
  --body '{"addFields":[{"name":"Priority","type":"DECIMAL","decimalPrecision":0},{"name":"Tags","type":"STRING"}]}' \
  --output json

# Update entity display name and description (metadata only)
uip df entities update <entity-id> \
  --body '{"displayName":"Updated Name","description":"New description"}' \
  --output json

# Add fields and update metadata in one call
uip df entities update <entity-id> \
  --body '{"addFields": [{"name":"Region","type":"STRING"}],"displayName": "Regional Entity"}' \
  --output json
```

A metadata update (`description`, `isRbacEnabled`) must also include the current `displayName`; read it from `entities get` and pass it even when only the description changes. Field-only updates (`addFields` / `updateFields` / `removeFields`) do not need it.

### Updating Existing Field Metadata (`updateFields`)

`updateFields` identifies fields by UUID, not name. Run `entities get <entity-id> --output json`, take `Fields[].Id`, and re-emit it as lowercase `id`; `Id` is silently treated as missing.

```bash
uip df entities update <entity-id> \
  --body '{
    "updateFields": [
      { "id": "<field-id>", "displayName": "Unit Price", "isRequired": true }
    ]
  }' \
  --output json
```

Entries support `id` (required), `displayName`, `description`, `isRequired`, `isRbacEnabled`, `isEncrypted`, `defaultValue`, `lengthLimit`, `maxValue`, `minValue`, and `decimalPrecision`; constraints follow [Advanced Field Constraints](#advanced-field-constraints). `isUnique` is not updateable; recreate with `removeFields` → `addFields` and explicit confirmation.

#### Verify-after-update — never trust the Success response alone

`updateFields` can return `Result: Success` while silently ignoring immutable fields (today `isUnique`; potentially future constraints). After **ANY** `updateFields`, run `entities get <entity-id> --output json` and compare every attempted key. If a post-update value differs, surface it verbatim: *"The platform accepted the request but did not apply `isUnique: true` on field X — that toggle is immutable after creation."* Do not report it applied merely because the CLI exit code was 0.

### Supported `entities update` Body Keys

| Key | Description |
|---|---|
| `addFields` | Field definitions, same shape as create |
| `updateFields` | Field updates; each requires `id` (field UUID) |
| `removeFields` | Field-delete entries, each `{"name":"..."}`; see [Deleting a Field](#deleting-a-field) |
| `displayName` | New entity display name |
| `description` | New description |
| `isRbacEnabled` | Entity RBAC toggle |

## System Fields

Every entity has auto-created, read-only system fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. Do not include them in field definitions or CSV imports.

## Listing and Inspecting Entities

```bash
# List all entities (includes user, system, and any federated rows)
uip df entities list --output json

# List only native entities (recommended before any write operation)
uip df entities list --native-only --output json

# Get full schema including all fields
uip df entities get <entity-id> --output json
```

`entities list` fields:

| Field | Description |
|---|---|
| `Id` | Entity UUID required by `uip df` record/entity commands |
| `Name` | System name (e.g. `BankDetails`) |
| `DisplayName` | UI label |
| `EntityType` | Object kind: `Entity`, `SystemEntity` (e.g. `SystemUser`; hidden by `--native-only`), `ChoiceSet`, `InternalEntity`; both native and federated entities are `Entity`; no `Source` field |
| `EntityClass` | Native-vs-federated classification: `Native`, `Federated`, or `Case` — the field that distinguishes federated from native |
| `EntityTypeId` | Numeric type code paralleling `EntityType` |
| `FolderId` | Folder GUID, or all-zeros UUID for tenant level |
| `RecordCount`, `StorageSizeInMB`, `UsedStorageSizeInMB` | Storage metrics |

`entities get <id>` is not symmetric with create: type is under `FieldDataType.Name`, not flat `Type`. Exact useful keys:

| Field | Description |
|---|---|
| `Fields[].Name` | Exact case-sensitive JSON record key |
| `Fields[].DisplayName` | Exact CSV header |
| `Fields[].FieldDataType.Name` | Type; legacy fields may be UI-broken (`INTEGER` / `FLOAT` / `UUID` / `DATETIME` / …) |
| `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | Constraints |
| `Fields[].Id` | Field UUID for `updateFields` |
| `Fields[].IsRequired` | Required on insert |
| `Fields[].ChoiceSetId` | Choice-set UUID (set on `CHOICE_SET_*` fields) |
| `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id` | Target UUIDs on `RELATIONSHIP` / `FILE` |
| `Fields[].FieldDisplayType` | Render hint (`ChoiceSetSingle`, `ChoiceSetMultiple`, `File`, …) |
| `Fields[].IsForeignKey` | `true` on `RELATIONSHIP` / `FILE` |

Before record writes, identify complex fields by `FieldDataType.Name` and resolve lookups: `CHOICE_SET_*` → `choice-sets list-values <choice-set-id>` for `NumberId`s; `RELATIONSHIP` → `records query` on `ReferenceEntity.Id` for target record UUIDs.

## Native vs Federated Entities

`entities list`/`get` rows carry `EntityType` (kind) and `EntityClass` (classification); no `Source` exists. `EntityType` values are `Entity` (normal entity, native or federated), `SystemEntity` (internal, e.g. `SystemUser`; hidden by `--native-only`), `ChoiceSet`, and `InternalEntity`. `EntityClass` values are `Native` (stored in Data Fabric, full read/write), `Federated` (read-only unified view over external/other sources), and `Case`. A federated entity is `EntityType: "Entity"` + `EntityClass: "Federated"`; do not detect it from `EntityType`.

Filter with `--federated-only` / `--native-only` (omit both for all); `--native-only` also drops `SystemEntity`. **Only native entities support record creation, update, delete, and import.** Federated entities are read-only for records: read via `records list` or `records query` (filter/sort/projection supported; aggregates and multi-entity joins are not; see federated-entity-creation.md Rule 9).

> **Creating** a federated entity from an Integration Service connector on the tenant's federated allow-list (`uip df connectors list`) or from another DF entity **is supported** — see [`federated-entity-creation.md`](federated-entity-creation.md) for the create payload, field mapping, `EntityClass: "Federated"`, and `--federated-only` listing. Only **record writes** to a federated entity are unsupported; data lives in the source, so writes happen there.