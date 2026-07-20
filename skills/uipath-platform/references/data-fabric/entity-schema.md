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
      {"fieldName": "Score",       "type": "DECIMAL",  "decimalPrecision": 0},
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

CLI-enforced from `@uipath/data-fabric-tool` `1.199.0+`. The exact `EntityFieldDataType` UPPERCASE enum, per-type SQL mapping, and UI-broken substitutions are the CLI's source of truth: [Data Fabric CLI docs → Supported Field Types](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#supported-field-types) and [Client-side validation](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#client-side-validation). Complex types (`CHOICE_SET_*`, `RELATIONSHIP`, `FILE`) still need the extra config documented in the sections below.

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
2. **List/query reads return a size marker, not content.** `records list` / `records query` return a string starting `HasValue=true Length=N` (live form: `"HasValue=true Length=20000 — call Get Entity Record By Id activity to retrieve content"`); only `records get <entity-id> <record-id>` returns the full value. Read + write-back rules in [records-query.md → MULTILINE_MAX fields](records-query.md#multiline_max-fields--marker-vs-full-content).
3. **On a 400 from `entities create` / `addFields` naming the type**, surface the error verbatim — do NOT retry or silently substitute `MULTILINE_TEXT` (Rule 18).

Needs `@uipath/data-fabric-tool` `1.198.0+` (see data-fabric.md → Tool Version Requirements).

```bash
uip df entities create "Documents" \
  --body '{"fields":[{"fieldName":"Title","type":"STRING","isRequired":true},{"fieldName":"Body","type":"MULTILINE_MAX"}]}' \
  --output json
```

`lengthLimit` optional: UTF-16 **byte** budget, 1–131072; omitted → 131072 (platform max ≈ 65,536 chars — verified: 65,536-char insert succeeds, 65,537 rejected with *"value … is 131074 bytes, exceeds the 131072-byte limit"*).

## Field Definition Object

Name validation (format, reserved-field names, C#/VB keywords) is CLI-enforced from `@uipath/data-fabric-tool` `1.199.0+`. See [Data Fabric CLI docs → Client-side validation](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#client-side-validation).

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
| `type` | `EntityFieldDataType` | `STRING` | UPPERCASE enum — see [CLI docs → Supported Field Types](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#supported-field-types) |
| `displayName` | string | fieldName | Human-readable label |
| `description` | string | `""` | Optional description |
| `isRequired` | boolean | `false` | Field must have a value on insert |
| `isUnique` | boolean | `false` | Value must be unique across all records |
| `isRbacEnabled` | boolean | `false` | Role-based access control on this field |
| `isEncrypted` | boolean | `false` | Encrypted at rest |
| `defaultValue` | string | — | Default value (always a string representation) |
| `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision` | number | type-specific | Advanced per-type constraints — see below |

### Advanced Field Constraints

`lengthLimit` / `maxValue` / `minValue` / `decimalPrecision` are CLI-enforced (allowed types + ranges + `minValue < maxValue`). Full matrix: [Data Fabric CLI docs → Client-side validation](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#client-side-validation). `entities get` echoes current values under `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` — read them before authoring an `updateFields` change.

### Choice Set Fields

Body shape (`choiceSetId` required) and per-type write-value forms are CLI-enforced. Agent-side rule: if the needed choice set doesn't exist, follow the pick-or-create flow (data-fabric.md Rule 13); never fall back to `STRING`. Record write value is the integer `NumberId` from `choice-sets list-values` (single field → int, multi field → int[]). `CHOICE_SET_MULTIPLE` filter semantics (`contains` vs `=`): [records-query.md](records-query.md#filtering-on-choice-set-fields).

### Relationship Fields

Body shape (`referenceEntityId` + `referenceFieldId` required) is CLI-enforced. Agent-side rules:

- **`referenceFieldId` is a user-facing display choice** — it controls which target field renders in pickers, lists, and the Data Fabric UI. Always raise an `AskUserQuestion` dropdown with the target's candidate scalar fields (from `entities get <target-id>`); never silently default to `Id`. Auto Mode does NOT waive this — rendering choices are user-domain. The stored record value is **always the target record's UUID `Id`** regardless of which field is bound here.
- **Cue phrases that signal a `RELATIONSHIP`** (never substitute `STRING` / `UUID` — Rule 12): *"each order has a Customer"*, *"each report has a Supplier"*, *"each issue belongs to a Project"*.
- **Missing / ambiguous target entity** — follow pick-or-create (Rule 13); target must be native (no federated).
- **`referenceFolderKey`** — required whenever the target is folder-scoped (even same-folder). Full matrix: [Cross-folder references](#cross-folder-references).
- Record-write value on inserts / updates: always the target's UUID `Id`. If the user supplies an email / label, resolve first via `records query` on the target.

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

`RELATIONSHIP`, `FILE`, and `CHOICE_SET_*` field bindings require the parent and the target to share **scope class** (both tenant, or both folder — possibly different folders). Crossing tenant ↔ folder is rejected for user-authored targets. `CHOICE_SET_*` `referenceFolderKey` is CLI-rejected (data-fabric.md Rule 4 / CLI validator). The matrix:

| Parent scope | Target scope | Allowed? | `referenceFolderKey` for `RELATIONSHIP` / `FILE` |
|---|---|---|---|
| Tenant | Tenant | ✅ | Omit |
| Folder A | Folder A (same folder) | ✅ | `<folder-A-guid>` — required, even same-folder |
| Folder A | Folder B (different folder) | ✅ | `<folder-B-guid>` |
| Folder | Tenant user-authored entity / choice set | ❌ | n/a — not supported |
| Folder | Tenant **system** entity (`EntityAttachment`, `User`) | ✅ | Omit — platform-managed |
| Tenant | Folder | ❌ | n/a — not supported |

> **Same-folder gotcha for `RELATIONSHIP` / `FILE`.** Even when both entities live in the same folder, omitting `referenceFolderKey` errors out with *"Cannot create relationship field from folder-level entity ('<parent>') to tenant-level entity ('')"* — the server reads the absence as "target is tenant" and trips the cross-scope block. Always pass `referenceFolderKey` for folder-to-folder `RELATIONSHIP` / `FILE` bindings. (Not yet CLI-enforced; needs per-target schema fetch.)

Surface this constraint **before** invoking `entities create` / `addFields` whenever the parent and target sit on opposite sides of the boundary AND the target is not a system entity (Rule 18 — no silent substitution).

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

### FILE Fields

> **Never include a FILE-typed key in `records insert` or `records update` payloads (data-fabric.md Rule 6).** Expected behavior: the platform silently strips FILE values — UUID, file path, filename, base64, `null` — and returns `Result: Success` with no error. Do not read Success as "the file changed." `records update receipt:null` does **not** clear. `records update receipt:"<uuid>"` does **not** swap. Required path: `files upload` to attach or replace, `files delete` to clear, `files download` to retrieve. Sequence to seed a file on a new row: `records insert` without the FILE column → `files upload <entity-id> <record-id> <field-name> --file <path>` against the returned `Id`. CSV `records import` drops FILE columns too (Rule 20).

```json
{ "fieldName": "EvidenceFile", "type": "FILE" }
```

- **No reference fields required or accepted.** Server auto-wires to the tenant `EntityAttachment` system entity; any caller-supplied `referenceEntityId` / `referenceFieldId` is stripped by the SDK. Never treat these as user-domain choices — no `AskUserQuestion` about which field to bind. The Rule 14 display-field dropdown fires only for `RELATIONSHIP`.
- **CLI floor:** SDK builds before `@uipath/uipath-typescript` commit `80f9be7a` (branch `fix/df-file-field-refs-optional`, not yet on `main`) throw `Failure / RetryWillNotFix — "Field '<name>' of type FILE requires both referenceEntityId and referenceFieldId"`. On such a build, upgrade the CLI; if that's impossible, pass both UUIDs discovered off any existing FILE field's `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id`.
- Write sequence: `entities create` (FILE field, no refs) → `records insert` (no FILE column, Rule 6) → `files upload <entity-id> <record-id> <field-name> --file <path>`. Read-shape (`expansionLevel` 0 vs 1+) and full write path in [`records-query.md` → FILE fields](records-query.md#file-fields--never-write-through-insertupdate).

### Combined Example — mixing scalar, choice-set, and relationship fields

Complex types accept the same standard field options as scalars — `isRequired`, `isUnique`, `displayName`, `description`, `defaultValue`, `isRbacEnabled`, `isEncrypted`, plus type-specific constraints (`lengthLimit`, `maxValue`/`minValue`, `decimalPrecision`). Extras unique to complex types: `choiceSetId` for `CHOICE_SET_*`, `referenceEntityId` + `referenceFieldId` for `RELATIONSHIP`. `FILE` needs no extras (see [FILE Fields](#file-fields)).

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

## Delete / update entity — agent behavior

Command syntax + response shapes: [Data Fabric CLI docs → `entities` commands](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#common-commands).

- **`entities delete`** — irreversible. Follow data-fabric.md Rule 10 (dependent discovery via inbound `Fields[].ReferenceEntity.Id`, and shared `Fields[].ChoiceSetId`). Ask per dependent; never cascade silently.
- **`entities update removeFields`** — irreversible per column. Follow Rule 11 (cascade-ask for `CHOICE_SET_*` / `RELATIONSHIP` fields; FILE drops column only; system fields can't be removed).
- **`entities update updateFields`** — identifies fields by `id` (UUID, lowercase in body) from `entities get`. Supports: `displayName`, `description`, `isRequired`, `isRbacEnabled`, `isEncrypted`, `defaultValue`, `lengthLimit`, `maxValue`, `minValue`, `decimalPrecision`. `isUnique` is immutable — CLI rejects, no verify-after-update needed. Data type is immutable — recreate the field to change it.
- **System fields** (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`) are read-only and platform-owned; the CLI rejects them in write bodies (Rule 4).

## Inspecting an entity

`entities get <id>` response is **not** symmetric with the create payload — the type lives under `Fields[].FieldDataType.Name`, not a flat `Type`. Use the response for lookups before writes:

| Response key | Use |
|---|---|
| `Fields[].Name` | Exact field name for record bodies / CSV headers (case-sensitive) |
| `Fields[].Id` | Field UUID → `updateFields` |
| `Fields[].FieldDataType.Name` | Data type. Legacy rows may still show UI-broken types (INTEGER / FLOAT / UUID / DATETIME) — CLI blocks new writes of those |
| `Fields[].FieldDataType.{LengthLimit,MaxValue,MinValue,DecimalPrecision}` | Per-type constraint values |
| `Fields[].ChoiceSetId` | Bound choice set UUID → `choice-sets list-values` for `NumberId`s |
| `Fields[].ReferenceEntity.Id` + `Fields[].ReferenceField.Id` | Target entity/field for `RELATIONSHIP` / `FILE` |
| `Fields[].IsForeignKey` / `IsAttachment` | `true` on `RELATIONSHIP` / `FILE` respectively |

Row-level fields on `entities list` (`Id`, `Name`, `DisplayName`, `EntityType`, `FolderId`, `RecordCount`) — full response key list in the CLI docs. Use `--native-only` before any write (Rule 9).

## Native vs Federated Entities

Each `entities list` row carries an `EntityType` field (no `Source` field exists):

- `Entity` — native, data stored in Data Fabric, full read/write access
- `SystemEntity` — internal entity (e.g. `SystemUser`); hidden by `--native-only`, not writable
- Federated rows (backed by external connectors like Salesforce, Azure AD) surface here as well — read-only. The exact `EntityType` value for federated rows depends on the connector; verify by listing the tenant. `--native-only` filters them out alongside `SystemEntity`.

**Only native entities support record creation, update, delete, and import.**

> Creating federated entities or linking entities to external connectors is **not currently supported**. This cannot be done via the CLI or the UiPath portal.
