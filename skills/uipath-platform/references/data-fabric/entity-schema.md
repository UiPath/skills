# Entity Schema Reference

## Creating an Entity

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `entities create` — or any `entities update` that adds, updates, or removes fields — render the full proposed schema (entity name, displayName, description, every field with normalized type and all extras) as a table or formatted JSON block and wait for explicit user approval. Don't run the CLI until the user confirms.

```bash
uip df entities create "MyEntity" \
  --body '{
    "displayName": "My Entity",
    "description": "Optional description",
    "fields": [
      {"name": "Title",       "type": "STRING",   "isRequired": true},
      {"name": "Score",       "type": "DECIMAL",  "decimalPrecision": 0},
      {"name": "Active",      "type": "BOOLEAN"},
      {"name": "CreatedDate", "type": "DATE"}
    ]
  }' \
  --output json
```

- `fields` array is **required**. Each entry must include `name`.
- `displayName`, `description`, and `isRbacEnabled` are optional top-level keys.
- Response: `{ Code: "EntityCreated", Data: { Id: "<entity-id>" } }` — save `Data.Id` for subsequent operations.
- Alternatively use `--file <path>` pointing to a JSON file with the same structure.

## Supported Field Types

Pass the exact `EntityFieldDataType` UPPERCASE string — CLI is case-sensitive. **Only use types from this table.** The SDK enum is broader (`INTEGER`, `BIG_INTEGER`, `FLOAT`, `DOUBLE`, `UUID`, `DATETIME`) but those render broken in the UiPath Data Fabric UI — see [UI-broken types](#ui-broken-types-do-not-use) below.

| CLI type | SQL | Notes |
|---|---|---|
| `STRING` | NVARCHAR | Short text (≤4000 chars via `lengthLimit`) |
| `MULTILINE_TEXT` | NVARCHAR(MAX) | Long text (≤10000 chars via `lengthLimit`) |
| `MULTILINE_MAX` | NVARCHAR(MAX) | Very large text (`lengthLimit` = UTF-16 byte budget, 1–131072; default 128 KB ≈ 65,536 chars max). No filter/sort; list/query reads return a preview, not the guaranteed full value — see [MULTILINE_MAX fields](#multiline_max-fields) |
| `DECIMAL` | DECIMAL | All numbers — `decimalPrecision: 0` for whole; `2` for money |
| `BOOLEAN` | BIT | true/false |
| `DATE` | DATE | Date only |
| `DATETIME_WITH_TZ` | DATETIMEOFFSET | Date + time + timezone (only UI-compatible timestamp) |
| `FILE` | UNIQUEIDENTIFIER | Attachment — no reference fields needed (server auto-wires) — see [FILE Fields](#file-fields) |
| `CHOICE_SET_SINGLE` | INT | Needs `choiceSetId`. Only valid `INT`-backed field. |
| `CHOICE_SET_MULTIPLE` | NVARCHAR | Needs `choiceSetId` |
| `AUTO_NUMBER` | DECIMAL | Auto-incrementing number |
| `RELATIONSHIP` | UNIQUEIDENTIFIER | Needs `referenceEntityId` + `referenceFieldId` — see [Relationship Fields](#relationship-fields) |

### UI-broken types — do NOT use

CLI accepts these and `entities create` returns `Success`, but the UiPath Data Fabric UI can't render / edit / filter the column. Substitute in the Rule 14 preview and get approval — even when the user names one by keyword.

| Never emit | Substitute |
|---|---|
| `INTEGER` / `BIG_INTEGER` | `DECIMAL` with `decimalPrecision: 0` |
| `FLOAT` / `DOUBLE` | `DECIMAL` with required `decimalPrecision` |
| `UUID` | `RELATIONSHIP` (if FK) or `STRING` (opaque id) — ask |
| `DATETIME` (no TZ) | `DATETIME_WITH_TZ` |

### Normalizing user-facing type names

CLI needs UPPERCASE enum. Users write mixed-case + synonyms. Two paths:

- **Silent case-fold** when the word matches a UI-compatible type: `boolean`→`BOOLEAN`, `decimal`→`DECIMAL`, `file`→`FILE`, `relationship`→`RELATIONSHIP`, etc.
- **Substitute-with-confirm** when the word maps to a UI-broken type (see table above) OR to multiple UI-compatible types. Multi-candidate mappings:

| User phrasing | Ask |
|---|---|
| `text` / `long text` / `paragraph` / `document body` | `STRING` (≤4000) vs `MULTILINE_TEXT` (≤10000) vs `MULTILINE_MAX` (up to ≈65,536 chars, but no filter/sort — see [MULTILINE_MAX fields](#multiline_max-fields)) — expected length? |
| `number` / `int` / `integer` / `float` / `double` | `DECIMAL` — how many decimal places? (`0` for whole, `2` for money) |
| `money` / `price` / `amount` | Default `DECIMAL` with `decimalPrecision: 2`; confirm |
| `timestamp` / `datetime` | Default `DATETIME_WITH_TZ`; confirm |
| `choice` / `enum` / `picklist` | `CHOICE_SET_SINGLE` vs `CHOICE_SET_MULTIPLE` — one or many? |
| `tags` / `labels` | Default `CHOICE_SET_MULTIPLE`; confirm |
| `link to X` / `belongs to` / `foreign key` | `RELATIONSHIP` — [pick-or-create](#relationship-fields) the target |
| `attachment` / `upload` / `document` | `FILE`; confirm |
| `uuid` / `guid` | `RELATIONSHIP` if FK else `STRING` — ask |

If the CLI rejects a `--body` with *"Cannot read properties of undefined (reading 'sqlTypeName')"*, the `type` value didn't match a known enum — almost always a casing issue. Re-emit with the exact UPPERCASE value from the table above.

### MULTILINE_MAX fields

Very large text. Contract differs from `MULTILINE_TEXT`:

1. **Not filterable, not sortable.** Any `queryFilters` or `sortOptions` entry naming a `MULTILINE_MAX` field → 400: *"Field '<name>' is of type MULTILINE_MAX and cannot be used in filters."* / *"Sort field '<name>' is of type MULTILINE_MAX and cannot be used for sorting."* Never offer the field in filter/sort predicates. See [filter contract](filter-platform-contract.md#operator-support-by-field-type).
2. **List/query reads return a preview, not the guaranteed full value.** Depending on the tenant, `records list` / `records query` return either the value truncated to 10,000 characters with a `...[Truncated]` suffix, or a size marker starting `HasValue=true Length=N` (sometimes with a trailing hint). Encrypted fields always read back `HasValue=true Encrypted=true`. Only `records get <entity-id> <record-id>` returns the full value. Read + write-back rules in [records-query.md → MULTILINE_MAX fields](records-query.md#multiline_max-fields--preview-vs-full-content).
3. **On a 400 from `entities create` / `addFields` naming the type**, surface the error verbatim — do NOT retry or silently substitute `MULTILINE_TEXT` (Rule 18).

```bash
uip df entities create "Documents" \
  --body '{"fields":[{"name":"Title","type":"STRING","isRequired":true},{"name":"Body","type":"MULTILINE_MAX"}]}' \
  --output json
```

`lengthLimit` optional: UTF-16 **byte** budget, 1–131072; omitted → 131072 (platform max ≈ 65,536 chars — verified: 65,536-char insert succeeds, 65,537 rejected with *"value … is 131074 bytes, exceeds the 131072-byte limit"*).

## Field Definition Object

### Name Validation

Entity names must:
- Start with a letter (`[a-zA-Z]`)
- Contain only letters, digits, and underscores (`[a-zA-Z0-9_]`)
- Be 3–100 characters long
- **Not** be a C# or VB reserved keyword. The CLI also rejects some SQL-reserved words such as `Order`, while ordinary names such as `Status` and `Key` are accepted. Surface the actual validation error and ask for a domain-specific rename; do not maintain a speculative local keyword list. See **data-fabric.md Rule 4**.

Field names follow the same length and starting-letter rules but may contain **letters and digits only** (`[a-zA-Z0-9]`); underscores are rejected. A field name also cannot equal its entity name, ignoring case.

**Reserved field names** (case-insensitive): `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`

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
|--------|------|---------|-------|
| `name` | string | required | 3–100 chars, starts with letter, letters and digits only |
| `type` | `EntityFieldDataType` | `STRING` | See type table above |
| `displayName` | string | name | Human-readable label, max 128 chars |
| `description` | string | `""` | Optional description, max 512 chars |
| `isRequired` | boolean | `false` | Field must have a value on insert |
| `isUnique` | boolean | `false` | Value must be unique across all records |
| `isRbacEnabled` | boolean | `false` | Role-based access control on this field |
| `isEncrypted` | boolean | `false` | Encrypted at rest |
| `defaultValue` | string | — | Default value (always a string representation) |
| `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision` | number | type-specific | Advanced per-type constraints — see below |

### Round-trip: `get` shape into `create` / `update`

Paste a field straight from `entities get` (read shape) into `create` `fields` or `update` `addFields` — the CLI normalizes it to the write shape; no translation layer. Each object must be wholly one shape (a field already carrying `name`/`type` is passed through unchanged). Read-only keys (`Id`, `System`, `PrimaryKey`, …) are dropped.

| Read (`entities get`) | Write (`create` / `addFields`) |
|-----------------------|--------------------------------|
| `Name` | `name` |
| `FieldDataType.Name` | `type` |
| `FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | `lengthLimit`/`maxValue`/`minValue`/`decimalPrecision` |
| `DisplayName`, `Description`, `DefaultValue` | `displayName`, `description`, `defaultValue` |
| `IsRequired`, `IsUnique`, `IsRbacEnabled`, `IsEncrypted`, `IsHiddenField` | `isRequired`, `isUnique`, `isRbacEnabled`, `isEncrypted`, `isHiddenField` |
| `ReferenceEntity.Id`, `ReferenceField.Id`, `ReferenceChoiceSet.Id` | `referenceEntityId`, `referenceFieldId`, `choiceSetId` |

### Advanced Field Constraints

Accepted on `entities create` and on `addFields` / `updateFields` in `entities update`. Each constraint applies only to specific types — passing one to an unsupported type errors with *"Field '<name>' of type <TYPE> does not accept <option>"*. `minValue` must be less than or equal to `maxValue`.

| Constraint | Allowed type | Range |
|------------|--------------|-------|
| `lengthLimit` | `STRING` (1–4000), `MULTILINE_TEXT` (1–10000), `MULTILINE_MAX` (1–131072 — UTF-16 **bytes**, ≈ 2 per char: 131072 ⇒ 65,536 chars max) | — |
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

Change a constraint after creation via `updateFields` (use the field UUID from `entities get`):

```bash
uip df entities update <entity-id> \
  --body '{"updateFields":[{"id":"<field-id>","lengthLimit":1000}]}' \
  --output json
```

`entities get` echoes the current constraint values on each field under `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` — read these before authoring an `updateFields` call.

### Choice Set Fields

```json
{ "name": "Status", "type": "CHOICE_SET_SINGLE",   "choiceSetId": "<choice-set-id>" }
{ "name": "Tags",   "type": "CHOICE_SET_MULTIPLE", "choiceSetId": "<choice-set-id>" }
```

`choiceSetId` is the UUID from `uip df choice-sets list`. If a needed choice set doesn't exist, ask the user — then author it with `choice-sets create` + `choice-set-values create` (do not fall back to `STRING`). Record value is the integer `NumberId` (single) or integer array (multi), from `choice-sets list-values`. Filter semantics — including the `CHOICE_SET_MULTIPLE` `=` vs `contains` distinction — are in [records-query.md](records-query.md#filtering-on-choice-set-fields). Full workflow in [`choice-sets.md`](choice-sets.md).

### Relationship Fields

```json
{ "name": "customerId", "type": "RELATIONSHIP", "referenceEntityId": "<target-entity-uuid>", "referenceFieldId": "<target-field-uuid>" }
```

- `referenceEntityId` — UUID of the target entity. Get it from `entities list --native-only` (the `Id` column). Target must exist and be native (no federated targets).
- `referenceFieldId` — UUID of the **display field** on the target entity. This is a user-visible product decision — it controls which target field renders in pickers, lists, and the Data Fabric UI when the relationship is shown. **Always confirm with the user** which field to display (`Name`, `Email`, `Title`, etc.) — do NOT silently default to the target's `Id` UUID just because it exists. List the target's candidate display fields from `entities get <target-entity-id>` (`Fields[].Name`/`DisplayName` for human-readable scalar fields) and raise an `AskUserQuestion` dropdown if more than one fits. The stored record value is **always the target record's UUID `Id`** regardless of which field is bound here — `referenceFieldId` is purely the join-and-render hint. Auto Mode does NOT waive this confirmation: rendering choices are user-domain, not technical defaults.
- `referenceFolderKey` — applies to **`RELATIONSHIP` only**. Pass it whenever the target is folder-scoped, including when it is in the same folder as the parent. Omit it for tenant-level targets. `CHOICE_SET_*` resolves scope from `choiceSetId`; `FILE` is auto-wired and takes no reference fields. See [Cross-folder references](#cross-folder-references).
- The field lives on the *child* (many-side) and points at the *parent* (one-side) — no reverse field on the parent.
- Record value is **always the target record's UUID `Id`**, regardless of which field's UUID was passed as `referenceFieldId` (it controls the join, not the stored value). If the user supplies an email / label, resolve it first via `records query` on the target entity.
- `FILE` fields do NOT take reference fields — server auto-wires. See [FILE Fields](#file-fields).
- Cue phrases that signal a `RELATIONSHIP` (never substitute `STRING`/`UUID` — **data-fabric.md Rule 12**): *"each order has a Customer"*, *"each report has a Supplier"*, *"each issue belongs to a Project"*.
- If the user didn't name a target entity OR the named one doesn't exist, follow the **pick-or-create flow in data-fabric.md Rule 13** — list candidates via `entities list --native-only`, ask, create only with approval.

### Cross-folder references

`RELATIONSHIP` and `CHOICE_SET_*` bindings require the parent and target to share **scope class**: both tenant-level or both folder-scoped. Folder-to-folder works across different folders; crossing the tenant/folder boundary does not. `FILE` is excluded because the server always binds it to the platform-managed attachment entity.

**Per-field `referenceFolderKey` differs by field type:**

- **`RELATIONSHIP`** — pass `referenceFolderKey` whenever the target is folder-scoped, including same-folder bindings. Omitting it makes the server treat the target as tenant-level and reject the binding.
- **`CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE`** — do **NOT** pass `referenceFolderKey` at the API level. The backend resolves the choice-set's folder server-side from `choiceSetId` alone. Passing it is unnecessary and may be rejected.

| Parent scope | Target scope | Allowed? | `referenceFolderKey` for `RELATIONSHIP` | `referenceFolderKey` for `CHOICE_SET_*` |
|---|---|---|---|---|
| Tenant | Tenant | ✅ | Omit | Omit |
| Folder A | Folder A (same folder) | ✅ | `<folder-A-guid>` — required, even same-folder | Omit (server resolves from `choiceSetId`) |
| Folder A | Folder B (different folder) | ✅ | `<folder-B-guid>` | Omit (server resolves from `choiceSetId`) |
| Folder | Tenant user-authored entity / choice set | ❌ | n/a — not supported | n/a — not supported |
| Tenant | Folder | ❌ | n/a — not supported | n/a — not supported |

Surface this constraint to the user **before** invoking `entities create` / `addFields` whenever the proposed parent and target sit on opposite sides of the tenant ↔ folder boundary. Do not silently fall back to a different field type — see Rule 18 (no silent substitution).

### FILE Fields

> **Never include a FILE-typed key in `records insert` or `records update` payloads (data-fabric.md Rule 6).** Expected behavior: the platform silently strips FILE values — UUID, file path, filename, base64, `null` — and returns `Result: Success` with no error. Do not read Success as "the file changed." `records update receipt:null` does **not** clear. `records update receipt:"<uuid>"` does **not** swap. Required path: `files upload` to attach or replace, `files delete` to clear, `files download` to retrieve. Sequence to seed a file on a new row: `records insert` without the FILE column → `files upload <entity-id> <record-id> <field-name> --file <path>` against the returned `Id`. CSV `records import` drops FILE columns too (Rule 20).

```json
{ "name": "EvidenceFile", "type": "FILE" }
```

- **No reference fields required or accepted.** Server auto-wires to the tenant `EntityAttachment` system entity; any caller-supplied `referenceEntityId` / `referenceFieldId` is stripped by the SDK. Never treat these as user-domain choices — no `AskUserQuestion` about which field to bind. The Rule 14 display-field dropdown fires only for `RELATIONSHIP`.
- Write sequence: `entities create` (FILE field, no refs) → `records insert` (no FILE column, Rule 6) → `files upload <entity-id> <record-id> <field-name> --file <path>`. Full surface: [`file-attachments.md`](file-attachments.md).

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
  --body '{"removeFields":[{"name":"<exact-field-name>"}]}' \
  --yes --reason "<why>" \
  --output json
```

Irreversible — drops the column and every record's value in it. Note the body shape: `removeFields` takes `{"name": "..."}`, **NOT** `{"id": "..."}` (that's `updateFields`). Mixing those forms returns *"Each field in removeFields must include a non-empty 'name' string"*.

Before invoking, surface the impact to the user **and** run the cascade-ask (data-fabric.md Rule 11):

- **CHOICE_SET_* fields** — choice set is shared. Resolve `Fields[].ChoiceSetId` from `entities get <id>`, list other entities binding that choice set (`entities list --output json` → entries whose `Fields[].ChoiceSetId == <id>`), then raise an `AskUserQuestion` dropdown: `Delete only the field` · `Also delete choice set <Name> (<id>)` · `Stop`. On `Also delete …`, run the choice-set-delete flow ([`choice-sets.md` → Deleting a choice set](choice-sets.md#deleting-a-choice-set)) with its own dependent-discovery.
- **RELATIONSHIP fields** — warn that consumers may depend on the field. Resolve `Fields[].ReferenceEntity.Id`, list other inbound references (`entities list --output json` → entries whose `Fields[].ReferenceEntity.Id == <id>`), then raise an `AskUserQuestion` dropdown: `Delete only the field` · `Also delete target entity <Name> (<id>)` · `Stop`. On `Also delete …`, run the entity-delete flow (Rule 10) with its own dependent-discovery.
- **FILE fields** — drop only the column. The `referenceEntityId` points at platform-managed FILE storage; do **not** offer to delete it.
- **System fields** (`Id`, `CreatedBy`, …) can't be removed regardless.

Response: `{ Code: "EntityUpdated", Data: { Id, RemovedFields: ["<name>"], Reason } }`.

## Not Supported

| Operation | Action |
|-----------|--------|
| Change a field's data type | Not supported — type is fixed at creation and cannot be changed via `updateFields` |
| Toggle `isUnique` on an existing field (either direction) | Not supported — `isUnique` is fixed at creation. `updateFields` with `isUnique: true/false` returns `Result: Success` but the server silently ignores the change; the Data Fabric UI renders the toggle as **disabled** on existing fields. To enforce uniqueness on a field that doesn't have it: (1) confirm with the user that the field can be recreated, then (2) `removeFields` it (drops all existing values in that column — see Rule 11), then (3) `addFields` with `isUnique: true`. Do NOT report success on a no-op `updateFields` — verify via `entities get` (see Verify-after-update below). |
| Field name rejected as a reserved keyword | C#/VB keywords return `RESERVED_LANGUAGE_KEYWORDS`; the CLI also rejects some SQL words such as `Order`, while names such as `Status` and `Key` are accepted. Surface the actual error and ask for a domain-specific rename. |
| Rename an entity (change its `name`) | Not supported — the entity name is fixed at creation. `entities update` changes only `displayName` / `description`; a top-level `name` in the body is rejected. To use a different name, create a new entity. |

Record-level writes against FILE fields (insert / update / import) are anti-patterns documented in data-fabric.md Rule 6 and [`records-query.md` → FILE fields](records-query.md#file-fields). This file covers schema only.

---

## Updating an Entity

Use `entities update` to add fields, modify existing field metadata, or update entity-level properties.

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
  --body '{
    "addFields": [{"name":"Region","type":"STRING"}],
    "displayName": "Regional Entity"
  }' \
  --output json
```

> A metadata update (`description`, `isRbacEnabled`, `isAnalyticsEnabled`) must also include the current `displayName` — the backend requires it, so the CLI rejects a metadata body without it. Read it from `entities get` and pass it even when only the description changes (as the metadata-only example above does). Field-only updates (`addFields` / `updateFields` / `removeFields`) don't need it.

### Updating Existing Field Metadata (`updateFields`)

`updateFields` identifies fields by their **field ID** (UUID), not by name. Retrieve field IDs from `entities get <entity-id> --output json` — each field in the `Fields` array exposes the UUID as `Id`. **Re-emit it as `id` (lowercase) in the `updateFields` body** — the body key and the response key differ only by case, and a mistyped `Id` is silently treated as missing.

```bash
uip df entities update <entity-id> \
  --body '{
    "updateFields": [
      { "id": "<field-id>", "displayName": "Unit Price", "isRequired": true }
    ]
  }' \
  --output json
```

`updateFields` entry supports: `id` (required), `displayName`, `description`, `isRequired`, `isRbacEnabled`, `isEncrypted`, `defaultValue`, `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision`. The four constraint keys follow the per-type allow-list in [Advanced Field Constraints](#advanced-field-constraints).

**`isUnique` is NOT updateable** — see Not Supported above. The API accepts it on `updateFields`, returns `Result: Success`, but silently ignores the value (the Data Fabric UI toggle is disabled on existing fields). Recreate the field (`removeFields` → `addFields` with `isUnique: true`) to add or remove uniqueness — with explicit user confirmation, since `removeFields` drops every existing value in the column.

#### Verify-after-update — never trust the Success response alone

`updateFields` can return `Result: Success` while silently ignoring fields the platform doesn't allow to change (today: `isUnique`; previously: any future immutable constraint). After ANY `updateFields` call, re-run `entities get <entity-id> --output json` and compare the response with what you sent. For each key you tried to change, if the post-update value doesn't match what you sent, surface this verbatim to the user — *"The platform accepted the request but did not apply `isUnique: true` on field X — that toggle is immutable after creation."* Do NOT report the change as applied just because the CLI exit code was 0.

### Supported `entities update` Body Keys

| Key | Description |
|-----|-------------|
| `addFields` | Array of field definition objects to add (same shape as create) |
| `updateFields` | Array of field updates — each entry must include `id` (field UUID) |
| `removeFields` | Array of field-delete entries — each takes `{"name":"..."}`; see [Deleting a Field](#deleting-a-field) for full gating |
| `displayName` | New display name for the entity |
| `description` | New description |
| `isRbacEnabled` | Toggle RBAC on the entity |

## System Fields

Every entity has auto-created system fields: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. These are read-only and must not be included in field definitions or CSV imports.

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
| `Fields[].Name` | Exact, case-sensitive field name for JSON record bodies |
| `Fields[].DisplayName` | Exact header required by CSV import |
| `Fields[].FieldDataType.Name` | Data type. Legacy fields may return UI-broken types (`INTEGER` / `FLOAT` / `UUID` / `DATETIME` / …) — see [Supported Field Types](#supported-field-types). |
| `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | Type-specific constraint values |
| `Fields[].Id` | Field UUID — required for `updateFields` in `entities update` |
| `Fields[].IsRequired` | Whether the field must have a value on insert |
| `Fields[].ChoiceSetId` | Bound choice set UUID (set on `CHOICE_SET_*` fields) |
| `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id` | Target entity/field UUIDs (set on `RELATIONSHIP` / `FILE` fields) |
| `Fields[].FieldDisplayType` | Render hint (`ChoiceSetSingle`, `ChoiceSetMultiple`, `File`, …) — set on complex fields |
| `Fields[].IsForeignKey` | `true` on `RELATIONSHIP` / `FILE` fields |

Before writing records, identify complex fields by `FieldDataType.Name` and resolve lookups: `CHOICE_SET_*` → `choice-sets list-values <choice-set-id>` for `NumberId`s; `RELATIONSHIP` → `records query` on `ReferenceEntity.Id` for target record UUIDs.

## Native vs Federated Entities

Each `entities list` row carries an `EntityType` field (no `Source` field exists):

- `Entity` — native, data stored in Data Fabric, full read/write access
- `SystemEntity` — internal entity (e.g. `SystemUser`); hidden by `--native-only`, not writable
- Federated rows (backed by external connectors like Salesforce, Azure AD) surface here as well — read-only. The exact `EntityType` value for federated rows depends on the connector; verify by listing the tenant. `--native-only` filters them out alongside `SystemEntity`.

**Only native entities support record creation, update, delete, and import.**

> Creating federated entities or linking entities to external connectors is **not currently supported**. This cannot be done via the CLI or the UiPath portal.
