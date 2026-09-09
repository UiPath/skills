# Entity Schema Reference

## Creating an Entity

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `entities create`—or any `entities update` that adds, updates, or removes fields—render the full proposed schema (entity name, displayName, description, every field with normalized type and all extras) as a table or formatted JSON block and wait for explicit user approval. Don't run the CLI until the user confirms.

Run:

```bash
uip df entities create "MyEntity" \
  --body '{"displayName":"My Entity","description":"Optional description","fields":[{"name":"Title","type":"STRING","isRequired":true},{"name":"Score","type":"DECIMAL","decimalPrecision":0},{"name":"Active","type":"BOOLEAN"},{"name":"CreatedDate","type":"DATE"}]}' \
  --output json
```

`fields` is required and every entry requires `name`. Optional top-level keys are `displayName`, `description`, and `isRbacEnabled`. The response is `{ Code: "EntityCreated", Data: { Id: "<entity-id>" } }`; save `Data.Id`. Run `uip df entities create "MyEntity" --file <path> --output json` with a same-shape JSON file when appropriate.

## Supported Field Types

Pass the exact case-sensitive `EntityFieldDataType` UPPERCASE value. Use only this UI-safe table; the broader SDK enum is not UI-safe.

| CLI type | SQL | Constraints/behavior |
|---|---|---|
| `STRING` | NVARCHAR | Short text; `lengthLimit` ≤4000 |
| `MULTILINE_TEXT` | NVARCHAR(MAX) | Long text; `lengthLimit` ≤10000 |
| `MULTILINE_MAX` | NVARCHAR(MAX) | Very large text; `lengthLimit` is a UTF-16 byte budget, 1–131072; default 128 KB ≈65,536 chars; no filter/sort; list/query returns a size marker |
| `DECIMAL` | DECIMAL | All numbers; `decimalPrecision: 0` whole, `2` money |
| `BOOLEAN` | BIT | true/false |
| `DATE` | DATE | Date only |
| `DATETIME_WITH_TZ` | DATETIMEOFFSET | Date/time/timezone; only UI-compatible timestamp |
| `FILE` | UNIQUEIDENTIFIER | Attachment; server auto-wires; see [FILE Fields](#file-fields) |
| `CHOICE_SET_SINGLE` | INT | Requires `choiceSetId`; only valid `INT`-backed field |
| `CHOICE_SET_MULTIPLE` | NVARCHAR | Requires `choiceSetId` |
| `AUTO_NUMBER` | DECIMAL | Auto-incrementing number |
| `RELATIONSHIP` | UNIQUEIDENTIFIER | Requires `referenceEntityId` + `referenceFieldId`; see [Relationship Fields](#relationship-fields) |

### UI-broken types

The CLI may accept these and return `Success`, but the UiPath Data Fabric UI cannot render, edit, or filter them. Substitute in the Rule 14 preview and obtain approval, even when the user names one.

| Never emit | Substitute |
|---|---|
| `INTEGER` / `BIG_INTEGER` | `DECIMAL` with `decimalPrecision: 0` |
| `FLOAT` / `DOUBLE` | `DECIMAL` with required `decimalPrecision` |
| `UUID` | `RELATIONSHIP` if FK, otherwise `STRING`; ask |
| `DATETIME` (no TZ) | `DATETIME_WITH_TZ` |

Silently case-fold synonyms mapping to one UI-compatible type (`boolean`→`BOOLEAN`, `decimal`→`DECIMAL`, `file`→`FILE`, `relationship`→`RELATIONSHIP`, etc.). For broken or ambiguous mappings, substitute and confirm:

| User phrasing | Ask |
|---|---|
| `text` / `long text` / `paragraph` / `document body` | `STRING` (≤4000), `MULTILINE_TEXT` (≤10000), or `MULTILINE_MAX` (up to ≈65,536 chars, no filter/sort)—expected length? |
| `number` / `int` / `integer` / `float` / `double` | `DECIMAL`—decimal places? (`0` whole, `2` money) |
| `money` / `price` / `amount` | Default `DECIMAL`, `decimalPrecision: 2`; confirm |
| `timestamp` / `datetime` | Default `DATETIME_WITH_TZ`; confirm |
| `choice` / `enum` / `picklist` | `CHOICE_SET_SINGLE` or `CHOICE_SET_MULTIPLE`—one or many? |
| `tags` / `labels` | Default `CHOICE_SET_MULTIPLE`; confirm |
| `link to X` / `belongs to` / `foreign key` | `RELATIONSHIP`; use [pick-or-create](#relationship-fields) |
| `attachment` / `upload` / `document` | `FILE`; confirm |
| `uuid` / `guid` | `RELATIONSHIP` if FK, otherwise `STRING`; ask |

If `--body` fails with *"Cannot read properties of undefined (reading 'sqlTypeName')"*, re-emit the exact UPPERCASE enum; do not use an unknown or incorrectly cased value.

### `MULTILINE_MAX` fields

1. Never include a `MULTILINE_MAX` field in `queryFilters` or `sortOptions`; it is neither filterable nor sortable and produces 400 errors such as *"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."* and *"Sort field '<name>' is of type MULTILINE_MAX and cannot be used for sorting."* See [filter contract](filter-platform-contract.md#operator-support-by-field-type).
2. `records list` / `records query` return a string beginning `HasValue=true Length=N` (live form: `"HasValue=true Length=20000 — call Get Entity Record By Id activity to retrieve content"`); only `records get <entity-id> <record-id>` returns content. Follow read/write-back rules in [records-query.md → MULTILINE_MAX fields](records-query.md#multiline_max-fields--marker-vs-full-content).
3. If `entities create` / `addFields` returns a 400 naming this type, surface it verbatim; do not retry or silently substitute `MULTILINE_TEXT` (Rule 18).

`lengthLimit` is optional, 1–131072 UTF-16 bytes; omitted means 131072. The platform maximum is ≈65,536 characters: 65,536 succeeds and 65,537 is rejected with *"value … is 131074 bytes, exceeds the 131072-byte limit"*.

## Field Definitions

### Names and options

Entity names must start with a letter (`[a-zA-Z]`), contain only letters, digits, and underscores (`[a-zA-Z0-9_]`), and be 3–100 characters. They cannot be C# or VB reserved keywords; the CLI also rejects some SQL-reserved words such as `Order`, while `Status` and `Key` are accepted. Surface the actual error and ask for a domain-specific rename; do not maintain a speculative local keyword list. See **data-fabric.md Rule 4**.

Field names follow the same length and starting-letter rules but allow letters and digits only (`[a-zA-Z0-9]`); underscores are rejected. A field cannot equal its entity name ignoring case. Reserved field names, case-insensitive: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. Within one create/add batch, field names and effective display names must each be case-insensitively unique. An entity supports at most 10 `MULTILINE_MAX` fields.

```json
{"name":"AccountNumber","type":"STRING","displayName":"Account Number","description":"Customer bank account number","isRequired":true,"isUnique":false,"isRbacEnabled":false,"isEncrypted":false,"defaultValue":"","lengthLimit":200}
```

| Option | Type/default | Notes |
|---|---|---|
| `name` | string, required | 3–100 chars, starts with a letter, letters/digits only |
| `type` | `EntityFieldDataType`, default `STRING` | Use the supported-type table |
| `displayName` | string, default name | Max 128 chars |
| `description` | string, default `""` | Max 512 chars |
| `isRequired`, `isUnique`, `isRbacEnabled`, `isEncrypted` | boolean, default `false` | See immutable `isUnique` rule |
| `defaultValue` | string | Always a string representation |
| `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision` | number, type-specific | See constraints |

### Round-trip `get` shape

Pass a field copied from `entities get` directly into `create.fields` or `update.addFields`; the CLI normalizes it. Keep each object wholly in one shape. Read-only keys (`Id`, `System`, `PrimaryKey`, …) are dropped.

| Read | Write |
|---|---|
| `Name` | `name` |
| `FieldDataType.Name` | `type` |
| `FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | `lengthLimit`/`maxValue`/`minValue`/`decimalPrecision` |
| `DisplayName`, `Description`, `DefaultValue` | `displayName`, `description`, `defaultValue` |
| `IsRequired`, `IsUnique`, `IsRbacEnabled`, `IsEncrypted`, `IsHiddenField` | same camel-case keys |
| `ReferenceEntity.Id`, `ReferenceField.Id`, `ReferenceChoiceSet.Id` | `referenceEntityId`, `referenceFieldId`, `choiceSetId` |

### Advanced constraints

Accepted on `entities create`, `addFields`, and `updateFields` in `entities update`. Apply only allowed options; otherwise surface *"Field '<name>' of type <TYPE> does not accept <option>"*. Require `minValue <= maxValue`.

| Constraint | Allowed type | Range |
|---|---|---|
| `lengthLimit` | `STRING` 1–4000; `MULTILINE_TEXT` 1–10000; `MULTILINE_MAX` 1–131072 UTF-16 bytes | — |
| `maxValue` / `minValue` | `DECIMAL` | ±9,007,199,254,740,991 |
| `decimalPrecision` | `DECIMAL` | 0–10; `0` whole, `2` money |

```bash
uip df entities update <entity-id> \
  --body '{"updateFields":[{"id":"<field-id>","lengthLimit":1000}]}' \
  --output json
```

`entities get` reports constraints under `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}`; read them before authoring `updateFields`.

### Choice-set fields

```json
{"name":"Status","type":"CHOICE_SET_SINGLE","choiceSetId":"<choice-set-id>"}
{"name":"Tags","type":"CHOICE_SET_MULTIPLE","choiceSetId":"<choice-set-id>"}
```

Resolve `choiceSetId` from `uip df choice-sets list`. If absent, ask the user, then run `choice-sets create` and `choice-set-values create`; never fall back to `STRING`. Record values are integer `NumberId` (single) or integer arrays (multiple), from `choice-sets list-values`. Filtering, including `CHOICE_SET_MULTIPLE` `=` versus `contains`, is in [records-query.md](records-query.md#filtering-on-choice-set-fields); full workflow: [`choice-sets.md`](choice-sets.md).

### Relationship fields

```json
{"name":"customerId","type":"RELATIONSHIP","referenceEntityId":"<target-entity-uuid>","referenceFieldId":"<target-field-uuid>"}
```

- Run `entities list --native-only` to resolve the target entity UUID; the target must exist and be native.
- Run `entities get <target-entity-id>` and list human-readable scalar `Fields[].Name`/`DisplayName` candidates. Always ask which field to display (`Name`, `Email`, `Title`, etc.); raise an `AskUserQuestion` dropdown when multiple fit. Never default to target `Id`. Auto Mode does not waive this confirmation.
- Store the target record UUID `Id`, regardless of `referenceFieldId`. If the user supplies an email/label, resolve it with `records query` first.
- `referenceFolderKey` applies only to `RELATIONSHIP`; pass it whenever the target is folder-scoped, including the same folder. Omit it for tenant-level targets. See [Cross-folder references](#cross-folder-references).
- The field belongs on the child (many-side) and points to the parent (one-side); add no reverse field.
- `FILE` fields take no reference fields and are auto-wired; see [FILE Fields](#file-fields).
- Treat *"each order has a Customer"*, *"each report has a Supplier"*, and *"each issue belongs to a Project"* as `RELATIONSHIP`; never substitute `STRING`/`UUID` (**data-fabric.md Rule 12**).
- If the target is unnamed or absent, list candidates with `entities list --native-only`, ask the user, and create only with approval, following **data-fabric.md Rule 13**.

### Cross-folder references

`RELATIONSHIP` and `CHOICE_SET_*` bindings require both entities/sets to be tenant-level or both folder-scoped. Folder A↔Folder B is allowed; tenant↔folder is not. `FILE` is excluded because the server binds it to platform-managed attachment storage.

- `RELATIONSHIP`: pass `referenceFolderKey` for every folder-scoped target, including same-folder; omit for tenant targets.
- `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE`: never pass `referenceFolderKey`; the backend resolves scope from `choiceSetId`, and passing it may be rejected.

| Parent | Target | Allowed? | `referenceFolderKey` for `RELATIONSHIP` | `referenceFolderKey` for `CHOICE_SET_*` |
|---|---|---|---|---|
| Tenant | Tenant | ✅ | Omit | Omit |
| Folder A | Folder A | ✅ | `<folder-A-guid>` required | Omit |
| Folder A | Folder B | ✅ | `<folder-B-guid>` | Omit |
| Folder | Tenant user-authored entity/choice set | ❌ | n/a | n/a |
| Tenant | Folder | ❌ | n/a | n/a |

Surface tenant↔folder incompatibility before `entities create` / `addFields`; never silently change type (Rule 18).

### FILE fields

> **Never include a FILE-typed key in `records insert` or `records update` payloads (data-fabric.md Rule 6).** The platform silently strips UUID, path, filename, base64, or `null` values and may return `Result: Success`; `records update receipt:null` does not clear and `records update receipt:"<uuid>"` does not swap. Run `files upload` to attach/replace, `files delete` to clear, and `files download` to retrieve. Seed a new row by running `records insert` without the FILE column, then run `files upload <entity-id> <record-id> <field-name> --file <path>`. CSV `records import` also drops FILE columns (Rule 20).

```json
{"name":"EvidenceFile","type":"FILE"}
```

FILE fields have no accepted reference fields; the server auto-wires them to tenant `EntityAttachment`, and the SDK strips supplied references. Never ask which field to bind. The Rule 14 display-field dropdown applies only to `RELATIONSHIP`.

Run this sequence: `entities create` (FILE field, no refs) → `records insert` (no FILE column, Rule 6) → `files upload <entity-id> <record-id> <field-name> --file <path>`. See [`file-attachments.md`](file-attachments.md).

## Updating an Entity

Run `entities update` to add fields, modify field metadata, or change entity metadata.

```bash
uip df entities update <entity-id> \
  --body '{"addFields":[{"name":"Priority","type":"DECIMAL","decimalPrecision":0},{"name":"Tags","type":"STRING"}]}' \
  --output json

uip df entities update <entity-id> \
  --body '{"displayName":"Updated Name","description":"New description"}' \
  --output json
```

Metadata updates (`description`, `isRbacEnabled`, `isAnalyticsEnabled`) must include the current `displayName`; read it from `entities get`. Field-only `addFields` / `updateFields` / `removeFields` bodies do not need it. Add fields and metadata may be combined.

Run `entities get <entity-id> --output json` before `updateFields`; retrieve field UUIDs from `Fields[].Id` and re-emit them as lowercase `id`; `Id` is silently treated as missing.

Supported `updateFields` keys: `id`, `displayName`, `description`, `isRequired`, `isRbacEnabled`, `isEncrypted`, `defaultValue`, `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision`. Apply the constraint allow-list above.

`isUnique` is immutable. The API may return `Result: Success` while ignoring it, and the UI disables the toggle. To change it: confirm recreation; run `removeFields` (which drops all values); then run `addFields` with the desired `isUnique`. After **every** `updateFields`, run `entities get <entity-id> --output json`, compare every requested key, and report any mismatch verbatim; never infer success from the exit code.

| Body key | Meaning |
|---|---|
| `addFields` | Field definitions as in create |
| `updateFields` | Field updates; each requires field UUID `id` |
| `removeFields` | `{"name":"..."}` entries; see [Deleting a Field](#deleting-a-field) |
| `displayName` | Entity display name |
| `description` | Entity description |
| `isRbacEnabled` | Entity RBAC toggle |

## Deleting an Entity

```bash
uip df entities delete <entity-id> [--folder-key <…>] --yes --reason "<why>" --output json
```

This is irreversible and deletes all records. Before invoking:

1. Run `entities list --output json`; find every inbound relationship where `Fields[].ReferenceEntity.Id == <entity-id>`. For each, ask whether to delete the dependent, leave dangling FKs, or stop.
2. Run `entities get <entity-id>`; find every `Fields[].ChoiceSetId`. For each shared choice set, ask whether to delete it, leave it, or stop; it is not deleted automatically.

Apply only confirmed choices. If uncertain, leave the dependent rather than deleting it.

## Deleting a Field

```bash
uip df entities update <entity-id> \
  [--folder-key <…>] \
  --body '{"removeFields":[{"name":"<exact-field-name>"}]}' \
  --yes --reason "<why>" \
  --output json
```

This irreversibly drops the column and values. `removeFields` requires `{"name":"..."}`, not `{"id":"..."}`; the latter is for `updateFields`, and mixing them returns *"Each field in removeFields must include a non-empty 'name' string"*.

Before invoking, explain impact and run the cascade-ask (data-fabric.md Rule 11):

- **`CHOICE_SET_*`**: resolve `Fields[].ChoiceSetId` with `entities get`; run `entities list --output json` to find other bindings. Ask via `AskUserQuestion`: `Delete only the field` · `Also delete choice set <Name> (<id>)` · `Stop`. If confirmed, run the choice-set deletion flow in [`choice-sets.md` → Deleting a choice set](choice-sets.md#deleting-a-choice-set), including dependent discovery.
- **`RELATIONSHIP`**: resolve `Fields[].ReferenceEntity.Id`; run `entities list --output json` to find inbound references. Ask: `Delete only the field` · `Also delete target entity <Name> (<id>)` · `Stop`. If confirmed, run the entity-delete flow (Rule 10), including dependent discovery.
- **`FILE`**: drop only the column; never offer deletion of platform-managed FILE storage.
- **System fields** (`Id`, `CreatedBy`, …) cannot be removed.

The response is `{ Code: "EntityUpdated", Data: { Id, RemovedFields: ["<name>"], Reason } }`.

## Not Supported

| Operation | Action |
|---|---|
| Change field data type | Not supported; type is fixed at creation |
| Toggle existing `isUnique` | Not supported; `Success` may be a silent no-op. Verify with `entities get`; recreate with confirmed `removeFields` → `addFields` if necessary |
| Reserved field/entity name | Surface actual `RESERVED_LANGUAGE_KEYWORDS` or SQL validation error and ask for a domain-specific rename |
| Rename entity (`name`) | Not supported; `entities update` changes only `displayName` / `description`; a top-level `name` is rejected. Create a new entity instead |

Record writes against FILE fields (insert/update/import) are anti-patterns documented in data-fabric.md Rule 6 and [`records-query.md` → FILE fields](records-query.md#file-fields). This reference covers schema only.

## System Fields

Every entity has auto-created read-only fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. Do not include them in field definitions or CSV imports.

## Listing and Inspecting Entities

Run:

```bash
uip df entities list --output json
uip df entities list --native-only --output json
uip df entities get <entity-id> --output json
```

Run `entities list --native-only` before writes. List rows expose:

| Field | Meaning |
|---|---|
| `Id` | Entity UUID required by entity/record commands |
| `Name` | System name |
| `DisplayName` | UI label |
| `EntityType` | `Entity` (native), `SystemEntity` (internal), or connector-dependent federated value; no `Source` field |
| `EntityTypeId` | Numeric parallel to `EntityType` |
| `FolderId` | Folder GUID, or all-zeros UUID for tenant level |
| `RecordCount`, `StorageSizeInMB`, `UsedStorageSizeInMB` | Storage metrics |

`entities get <id>` is not symmetric with create: use `Fields[].Name`, `Fields[].DisplayName`, `Fields[].FieldDataType.Name`, `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}`, `Fields[].Id`, `Fields[].IsRequired`, `Fields[].ChoiceSetId`, `Fields[].ReferenceEntity.Id`, `Fields[].ReferenceField.Id`, `Fields[].FieldDisplayType`, and `Fields[].IsForeignKey`. Legacy fields may expose UI-broken types (`INTEGER` / `FLOAT` / `UUID` / `DATETIME` / …).

Before record writes, resolve `CHOICE_SET_*` values with `choice-sets list-values <choice-set-id>` and `RELATIONSHIP` values with `records query` on `ReferenceEntity.Id`.

## Native vs Federated Entities

`Entity` is native and supports full read/write access. `SystemEntity` is internal, hidden by `--native-only`, and not writable. Federated rows backed by connectors such as Salesforce or Azure AD are read-only; their exact `EntityType` depends on the connector. `--native-only` excludes federated and `SystemEntity` rows.

Only native entities support record creation, update, delete, and import. Creating federated entities or linking entities to external connectors is not supported via the CLI or UiPath portal.