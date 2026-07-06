# Data Fabric Reference — Scopes, Conventions, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/entities/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { Entities, ChoiceSets } from '@uipath/uipath-typescript/entities';
```

Types, options, and enums export from the same subpath as their service class.

## Scopes

- Schema reads: `DataFabric.Schema.Read`
- Data reads: `DataFabric.Data.Read`
- Data writes: `DataFabric.Data.Write`

## Anti-shapes & gotchas (read first)

Data Fabric does NOT behave like a typical RDBMS. These differences trip up agents that pattern-match on familiar SQL/ORM shapes. Before writing analytics, filters, or update logic, call `entities.getById(id)` and inspect `fields[].name` + `fieldDataType`. Pick your data strategy from what's actually there — do NOT assume.

1. **Choice values come back as `numberId` integers on every read path.** Including ungrouped `getRecordById` and `queryRecordsById` items, not just `groupBy` results. Code like `record.Priority.toLowerCase()` will throw or produce `"5"`. Build `numberId → name` maps via `choiceSets.getById(<csId>)` and translate every read.
2. **DF auto-creates audit fields that look like domain fields but aren't.** Every entity has `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`, `Id`, `RecordOwner` — these are **row metadata** (when DF inserted/wrote the row), not the business event the row represents. When you need a domain-level "created at" / "updated at" / "owner", look for a custom field with a domain-specific name; if none exists, flag it back to the user rather than silently using the audit column. When writing your own historical timestamp field, name it something distinct from `CreateTime` / `UpdateTime` to avoid the conflict at write time.
3. **Unknown keys on insert are silently dropped.** A typo in a field name in `insertRecordsById` does NOT raise an error — the value is just discarded. Always introspect the schema and validate keys before bulk operations.
4. **No `IsNull` filter operator.** `queryRecordsById` filters can't ask "where field is null". Filter client-side after fetching, or design queries with explicit non-null sentinels.
5. **Field name casing is preserved verbatim on writes.** If the entity field is `Subject` (PascalCase), record payloads must use `Subject`, not `subject`. The SDK does NOT pascalize keys for you — DF rejects mismatched casing as missing required field.
6. **Filter `value` for choice fields must be the `numberId` as a string.** `{ fieldName: 'Status', operator: Equals, value: 'Resolved' }` matches nothing — use `value: String(numberIdForResolved)`.
7. **Aggregates require server-side `aggregates` + `groupBy`.** Don't fetch raw rows and `.length` / `.reduce` client-side — every list call returns one page (see [pagination.md](pagination.md)) and you'll silently truncate. Use `{ aggregates: [{ function: EntityAggregateFunction.Count, field: 'Id' }] }` (string literal `'COUNT'` works equivalently).
8. **`field.fieldDataType` is an OBJECT, not a string.** It's `{ name: 'DECIMAL', lengthLimit?: ..., maxValue?: ..., ... }`. Code like `String(field.fieldDataType).toUpperCase()` produces `"[object Object]"` and silently rejects every field. Always read `field.fieldDataType?.name`. Same applies to `field.fieldDisplayType` — but that one IS a plain string enum (`'ChoiceSetSingle'`, `'File'`, etc.).
9. **File-type fields (`fieldDisplayType === 'File'`) aren't strings.** The record carries only metadata (`{ id, name, size, contentType }`); stringifying gives `"[object Object]"`. To display, call `entities.downloadAttachment(entityId, recordId, fieldName)` → `Blob` → `URL.createObjectURL` for an `<img src>`. **Neither `contentType` nor filename extension is reliable for detecting kind** — DF often returns `application/octet-stream`, and the stored `name` is frequently a bare UUID with no extension. To decide whether to render inline or fall back to a download link, either (a) sniff the blob's magic bytes after download (PNG starts `89 50 4E 47`, JPEG `FF D8 FF`, GIF `47 49 46 38`, PDF `25 50 44 46`, etc.), or (b) optimistically attempt `<img src={objectUrl}>` and swap to a download link in `onError`. Writes: `uploadAttachment(entityId, recordId, fieldName, file)`, not `insertRecordById` / `updateRecordById`.

## Traps

### Trigger events — single-record methods fire them, bulk methods don't

| Operation | Fires Data Fabric trigger events | Does NOT fire trigger events |
|---|---|---|
| Insert | `insertRecordById` / `entity.insertRecord` | `insertRecordsById` / `entity.insertRecords` |
| Update | `updateRecordById` / `entity.updateRecord` | `updateRecordsById` / `entity.updateRecords` |
| Delete | `deleteRecordById` / `entity.deleteRecord` | `deleteRecordsById` / `entity.deleteRecords` |

Use the single-record variant when trigger events must fire for the affected record.

### Batch update payload requires `Id`

`updateRecordsById(id, data, options?)`: each record in `data` MUST include an `Id` field.

### Writes

> **Choice-set fields take the integer `numberId`, not the value name.** Sending `status: "Open"` fails with `Single choiceset value Open is not integer`. Build a `name → numberId` map from `choiceSets.getById(<choiceSetId>)`; get the `<choiceSetId>` from `entities.getById(id).fields[].referenceChoiceSet?.id` (or `.choiceSetId`).

> **Record keys must match the schema's exact casing.** The SDK does NOT pascalize record keys. If your entity's fields are `Subject`, `Status`, `CustomerEmail` (PascalCase, the DF UI default), you must send `{ Subject: …, Status: 1, CustomerEmail: … }` — sending `{ subject, status, customerEmail }` produces `Required field "Subject" is not provided` because DF's required-field check is case-sensitive. Read the schema via `entities.getById(id)` and use `field.name` verbatim as the record key.

> **Unknown keys are silently dropped.** If your record contains a key that isn't in the entity schema (typo, removed field, audit-column name conflict), `insertRecordsById` does NOT error — the field is just ignored. Always introspect the schema with `entities.getById(id)` before seeding bulk data; keys that don't show up in `entity.fields` will be discarded without warning.

> **DF auto-manages `CreateTime` / `UpdateTime` / `CreatedBy` / `UpdatedBy` / `Id` audit columns.** They appear in the entity schema but you cannot write to them — DF sets `CreateTime` to the moment of insert and `UpdateTime` to the moment of last write. If you need to seed historical timestamps (e.g., for an analytics demo where tickets must look 1–21 days old), add a **custom** `DATETIME_WITH_TZ` field (e.g., `OriginalCreatedTime`) and write to that. Do NOT name your custom field `CreateTime` or `CreatedTime` — the audit name conflict will cause silent drops or schema rejection.

### Queries (`queryRecordsById` / `entity.queryRecords`)

> **For counts and chart data, use server-side `aggregates` + `groupBy`.** Don't fetch raw rows and aggregate in JS — every list call returns one page (see [pagination.md](pagination.md)), so `result.items.length` after `queryRecordsById({ filter })` returns at most one page's worth, no matter how many rows match. Use `aggregates: [{ function: 'COUNT', field: 'Id' }]` (with `groupBy` for per-bucket counts).

> **Choice-set values come back as `numberId` integers in read responses — translate them yourself.** This applies to `groupBy` results AND ungrouped `queryRecordsById`/`getRecordById` items. Build a `numberId → name` map per choice field from `choiceSets.getById(<choiceSetId>)` once on app load and translate every time you read a choice field for display, comparison, or filter logic. Do NOT assume the SDK has already converted to a string name — it has not. A common silent failure: code that does `if (record.Status === "Resolved")` always evaluates false because `record.Status` is `5` (the numberId). Same for any logic doing `record.Priority.toLowerCase()` — it'll read `(5).toLowerCase`, throw, or coerce to `"5"` and miss every lookup keyed on names.

> **Filter `value` for a choice field must be the `numberId`** (as a string, per the operator type). `{ fieldName: 'Status', operator: Equals, value: 'Resolved' }` matches nothing — use `value: String(numberIdForResolved)`. This rule applies to **every** filter touching a choice-set field, including `NotEquals`, `In`, `NotIn`. Failing to translate filter values is silent: the API returns 0 rows or all rows depending on operator, so a "0 records" or "all records" symptom that ignores your filter usually means a missing translation.

> **Three paths require choice-value translation. Don't miss any.**
> | Path | Direction | What to do |
> |---|---|---|
> | Writes (`insertRecordsById`, `updateRecordById`, `updateRecordsById`) | name → `numberId` | translate before sending |
> | Filter values (any `queryRecordsById` filter on a choice field) | name → `numberId` (as a string) | translate before sending |
> | `groupBy` result keys | `numberId` → name | translate after receiving for display |
>
> Best practice: on app load, fetch each choice set once and build **both** maps (`byName` and `byNumberId`). Reuse across all paths.

> **`value` is always a string.** For numeric, boolean, or date fields, pass the string form (e.g., `"42"`, `"true"`, `"2026-05-01T00:00:00Z"`). For `In`/`NotIn`, use `valueList: string[]` instead of `value`.

Server-side behavior the types don't show: `EntityAggregateFunction` is string-valued (`'COUNT'`, `'SUM'`, … — string literals work in place of the enum). For `Count`, any non-null field works — typically `'Id'`. `expansionLevel` defaults to 0.

```typescript
import { EntityAggregateFunction } from '@uipath/uipath-typescript/entities';

// Aggregate: count per status
await entities.queryRecordsById(entityId, {
  selectedFields: ['status'],
  groupBy: ['status'],
  aggregates: [{ function: EntityAggregateFunction.Count, field: 'Id', alias: 'total' }],
});
```

### Attachments take positional arguments

`downloadAttachment(entityId, recordId, fieldName)`, `uploadAttachment(entityId, recordId, fieldName, file, options?)`, and `deleteAttachment(entityId, recordId, fieldName)` take **positional arguments, not an options object.** `entityId` is the UUID of the entity (not the entity name).

### Attached methods

Objects returned by `Entities.getAll()`/`getById()` carry attached operation methods (`entity.insertRecord()`, `entity.queryRecords()`, `entity.uploadAttachment()` …) bound to the entity's id — prefer them over re-calling the service with ids. The full list is the `EntityMethods` type in the `.d.ts`. Trigger-event semantics match the service methods (see table above).

### ChoiceSets

`choiceSets.getById(<choiceSetId>)` returns the set's values — each carries `name` and `numberId` — and is the source for the translation maps required by the choice-value traps above.
