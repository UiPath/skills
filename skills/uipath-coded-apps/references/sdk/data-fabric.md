# Data Fabric Reference

## Imports

```typescript
import { Entities, ChoiceSets } from '@uipath/uipath-typescript/entities';
```

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
## Scopes

- Schema reads: `DataFabric.Schema.Read`
- Data reads: `DataFabric.Data.Read`
- Data writes: `DataFabric.Data.Write`

## Types to Import

```typescript
import type {
  EntityGetResponse,
  RawEntityGetResponse,
  EntityMethods,
  EntityRecord,
  EntityFileType,
  EntityGetAllRecordsOptions,
  EntityGetRecordByIdOptions,
  EntityInsertRecordOptions,
  EntityInsertResponse,
  EntityInsertRecordsOptions,
  EntityBatchInsertResponse,
  EntityUpdateRecordOptions,
  EntityUpdateRecordResponse,
  EntityUpdateRecordsOptions,
  EntityUpdateResponse,
  EntityDeleteRecordsOptions,
  EntityDeleteResponse,
  EntityUploadAttachmentOptions,
  EntityUploadAttachmentResponse,
  EntityDeleteAttachmentResponse,
  EntityOperationResponse,
  EntityQueryRecordsOptions,
  EntityQueryRecordsResponse,
  EntityQueryFilter,
  EntityQueryFilterGroup,
  EntityQuerySortOption,
  EntityAggregate,
  FailureRecord,
  ChoiceSetGetAllResponse,
  ChoiceSetGetResponse,
  ChoiceSetGetByIdOptions,
} from '@uipath/uipath-typescript/entities';
```

## Enums

```typescript
import {
  EntityFieldDataType,     // UUID, STRING, INTEGER, DATETIME, DATETIME_WITH_TZ, DECIMAL, FLOAT, DOUBLE, DATE, BOOLEAN, BIG_INTEGER, MULTILINE_TEXT
  EntityType,              // Entity, ChoiceSet, InternalEntity, SystemEntity
  FieldDisplayType,        // Basic, Relationship, File, ChoiceSetSingle, ChoiceSetMultiple, AutoNumber
  LogicalOperator,         // And, Or
  QueryFilterOperator,     // Equals, NotEquals, GreaterThan, LessThan, ... (used in queryRecordsById filters)
  EntityAggregateFunction, // Count, Sum, Avg, Min, Max — string-valued enum ('COUNT', 'SUM', ...)
} from '@uipath/uipath-typescript/entities';
```

## Entities Service

### getAll()

Returns `Promise<EntityGetResponse[]>`. Each entity has attached methods.

### getById(id: string)

Returns `Promise<EntityGetResponse>` with attached methods.

### getAllRecords(entityId: string, options?: EntityGetAllRecordsOptions)

Returns `NonPaginatedResponse<EntityRecord>` or `PaginatedResponse<EntityRecord>` when pagination options are passed. Options: `expansionLevel?: number`, plus `pageSize`, `cursor`, `jumpToPage`.

### getRecordById(entityId: string, recordId: string, options?: EntityGetRecordByIdOptions)

Returns `Promise<EntityRecord>`. Options: `expansionLevel?: number`.

### insertRecordById(id: string, data: Record<string, any>, options?: EntityInsertRecordOptions)

Returns `Promise<EntityInsertResponse>` (which is `EntityRecord` — the inserted record with generated ID). Triggers Data Fabric trigger events.

### insertRecordsById(id: string, data: Record<string, any>[], options?: EntityInsertRecordsOptions)

Returns `Promise<EntityBatchInsertResponse>` with `{ successRecords, failureRecords }`. Does NOT trigger events. Options: `expansionLevel`, `failOnFirst`.

> **Choice-set fields take the integer `numberId`, not the value name.** Sending `status: "Open"` fails with `Single choiceset value Open is not integer`. Build a `name → numberId` map from `choiceSets.getById(<choiceSetId>)`; get the `<choiceSetId>` from `entities.getById(id).fields[].referenceChoiceSet?.id` (or `.choiceSetId`).

> **Record keys must match the schema's exact casing.** The SDK does NOT pascalize record keys. If your entity's fields are `Subject`, `Status`, `CustomerEmail` (PascalCase, the DF UI default), you must send `{ Subject: …, Status: 1, CustomerEmail: … }` — sending `{ subject, status, customerEmail }` produces `Required field "Subject" is not provided` because DF's required-field check is case-sensitive. Read the schema via `entities.getById(id)` and use `field.name` verbatim as the record key.

> **Unknown keys are silently dropped.** If your record contains a key that isn't in the entity schema (typo, removed field, audit-column name conflict), `insertRecordsById` does NOT error — the field is just ignored. Always introspect the schema with `entities.getById(id)` before seeding bulk data; keys that don't show up in `entity.fields` will be discarded without warning.

> **DF auto-manages `CreateTime` / `UpdateTime` / `CreatedBy` / `UpdatedBy` / `Id` audit columns.** They appear in the entity schema but you cannot write to them — DF sets `CreateTime` to the moment of insert and `UpdateTime` to the moment of last write. If you need to seed historical timestamps (e.g., for an analytics demo where tickets must look 1–21 days old), add a **custom** `DATETIME_WITH_TZ` field (e.g., `OriginalCreatedTime`) and write to that. Do NOT name your custom field `CreateTime` or `CreatedTime` — the audit name conflict will cause silent drops or schema rejection.

### updateRecordById(entityId: string, recordId: string, data: Record<string, any>, options?: EntityUpdateRecordOptions)

Returns `Promise<EntityUpdateRecordResponse>` — the updated single record. **Triggers Data Fabric trigger events** (unlike the bulk `updateRecordsById`). Use this when you need trigger events to fire for the updated record. Options: `expansionLevel`.

### updateRecordsById(id: string, data: EntityRecord[], options?: EntityUpdateRecordsOptions)

Returns `Promise<EntityUpdateResponse>` with `{ successRecords, failureRecords }`. Each record in `data` MUST include an `Id` field. Options: `expansionLevel`, `failOnFirst`. **Does NOT trigger events** — use `updateRecordById` if you need trigger events.

### deleteRecordsById(id: string, recordIds: string[], options?: EntityDeleteRecordsOptions)

Returns `Promise<EntityDeleteResponse>` with `{ successRecords, failureRecords }`. Options: `failOnFirst`. **Does NOT trigger events** — use `deleteRecordById` if you need trigger events.

### deleteRecordById(entityId: string, recordId: string)

Returns `Promise<void>`. **Triggers Data Fabric trigger events.** Use this for single deletes when triggers must fire (the bulk `deleteRecordsById` does not fire triggers).

### queryRecordsById(id: string, options?: EntityQueryRecordsOptions)

Returns `NonPaginatedResponse<EntityRecord>` or `PaginatedResponse<EntityRecord>` when pagination options are passed. Supports server-side filters, sort, field selection, aggregates, and group-by.

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

`EntityQueryRecordsOptions`:
- `filterGroup?: EntityQueryFilterGroup` — `{ logicalOperator?: LogicalOperator.And | Or, queryFilters?: EntityQueryFilter[], filterGroups?: EntityQueryFilterGroup[] }` (nested groups allowed). Each filter: `{ fieldName, operator: QueryFilterOperator, value?: string, valueList?: string[] }`.
- `selectedFields?: string[]` — fields to return (omit for all)
- `sortOptions?: EntityQuerySortOption[]` — `[{ fieldName, isDescending }]`
- `aggregates?: EntityAggregate[]` — `[{ function: EntityAggregateFunction.Count | Sum | Avg | Min | Max, field, alias }]` (string literals `'COUNT'` / `'SUM'` / etc. also work — the enum is string-valued). For `Count`, any non-null field works — typically `'Id'`.
- `groupBy?: string[]` — group aggregate results
- `expansionLevel?: number` — default 0
- Pagination (`pageSize`, `cursor`, `jumpToPage`) — when supplied, returns `PaginatedResponse`

`QueryFilterOperator` values: `Equals` `'='`, `NotEquals` `'!='`, `GreaterThan` `'>'`, `LessThan` `'<'`, `GreaterThanOrEqual` `'>='`, `LessThanOrEqual` `'<='`, `Contains` `'contains'`, `NotContains` `'not contains'`, `StartsWith` `'startswith'`, `EndsWith` `'endswith'`, `In` `'in'`, `NotIn` `'not in'`.

> **`value` is always a string.** For numeric, boolean, or date fields, pass the string form (e.g., `"42"`, `"true"`, `"2026-05-01T00:00:00Z"`). For `In`/`NotIn`, use `valueList: string[]` instead of `value`.

```typescript
import { LogicalOperator, QueryFilterOperator, EntityAggregateFunction } from '@uipath/uipath-typescript/entities';

// Filter + sort
const result = await entities.queryRecordsById(entityId, {
  filterGroup: {
    logicalOperator: LogicalOperator.And,
    queryFilters: [{ fieldName: 'status', operator: QueryFilterOperator.Equals, value: 'active' }],
  },
  sortOptions: [{ fieldName: 'createdTime', isDescending: true }],
});

// Aggregate: count per status
await entities.queryRecordsById(entityId, {
  selectedFields: ['status'],
  groupBy: ['status'],
  aggregates: [{ function: EntityAggregateFunction.Count, field: 'Id', alias: 'total' }],
});
```

### downloadAttachment(entityId: string, recordId: string, fieldName: string)

Returns `Promise<Blob>`. **Positional arguments, not an options object.** `entityId` is the UUID of the entity (not the entity name).

### uploadAttachment(entityId: string, recordId: string, fieldName: string, file: EntityFileType, options?: EntityUploadAttachmentOptions)

Returns `Promise<EntityUploadAttachmentResponse>`. `file` accepts `Blob | File | Uint8Array`. Options: `expansionLevel`.

### deleteAttachment(entityId: string, recordId: string, fieldName: string)

Returns `Promise<EntityDeleteAttachmentResponse>`. Positional arguments.

## Entity-Attached Methods (EntityMethods)

Returned by `getAll()` and `getById()` on each `EntityGetResponse`:

- `entity.insertRecord(data, options?)` -> `Promise<EntityInsertResponse>` (fires trigger events)
- `entity.insertRecords(data[], options?)` -> `Promise<EntityBatchInsertResponse>` (no trigger events)
- `entity.updateRecord(recordId, data, options?)` -> `Promise<EntityUpdateRecordResponse>` (fires trigger events)
- `entity.updateRecords(data: EntityRecord[], options?)` -> `Promise<EntityUpdateResponse>` (no trigger events)
- `entity.deleteRecords(recordIds: string[], options?)` -> `Promise<EntityDeleteResponse>` (no trigger events)
- `entity.deleteRecord(recordId)` -> `Promise<void>` (fires trigger events)
- `entity.getAllRecords(options?)` -> `NonPaginatedResponse<EntityRecord>` or `PaginatedResponse<EntityRecord>`
- `entity.getRecord(recordId, options?)` -> `Promise<EntityRecord>`
- `entity.queryRecords(options?)` -> `NonPaginatedResponse<EntityRecord>` or `PaginatedResponse<EntityRecord>` (filters, sort, aggregates — see `queryRecordsById` above)
- `entity.uploadAttachment(recordId, fieldName, file, options?)` -> `Promise<EntityUploadAttachmentResponse>`
- `entity.downloadAttachment(recordId, fieldName)` -> `Promise<Blob>`
- `entity.deleteAttachment(recordId, fieldName)` -> `Promise<EntityDeleteAttachmentResponse>`

## ChoiceSets Service

### getAll()

Returns `Promise<ChoiceSetGetAllResponse[]>`. Each item has: `name`, `displayName`, `description`, `folderId`, `createdBy`, `updatedBy`, `createdTime`, `updatedTime`.

### getById(choiceSetId: string, options?: ChoiceSetGetByIdOptions)

Returns `NonPaginatedResponse<ChoiceSetGetResponse>` or `PaginatedResponse<ChoiceSetGetResponse>`. Each value has: `id`, `name`, `displayName`, `numberId`, `createdTime`, `updatedTime`.

## Usage Example

```typescript
import { useMemo, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Entities } from '@uipath/uipath-typescript/entities';
import type { EntityGetResponse, EntityRecord } from '@uipath/uipath-typescript/entities';

function EntityRecords({ entityId }: { entityId: string }) {
  const { sdk } = useAuth();
  const entities = useMemo(() => new Entities(sdk), [sdk]);
  const [records, setRecords] = useState<EntityRecord[]>([]);

  useEffect(() => {
    const load = async () => {
      const entity = await entities.getById(entityId);
      const result = await entity.getAllRecords({ pageSize: 50 });
      setRecords(result.items);
    };
    load();
  }, [entities, entityId]);

  return <div>{records.map(r => <div key={r.id}>{JSON.stringify(r)}</div>)}</div>;
}
```
