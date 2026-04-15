# Data Fabric Reference

## Imports

```typescript
import { Entities, ChoiceSets } from '@uipath/uipath-typescript/entities';
```

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
  FailureRecord,
  ChoiceSetGetAllResponse,
  ChoiceSetGetResponse,
  ChoiceSetGetByIdOptions,
} from '@uipath/uipath-typescript/entities';
```

## Enums

```typescript
import {
  EntityFieldDataType,   // UUID, STRING, INTEGER, DATETIME, DATETIME_WITH_TZ, DECIMAL, FLOAT, DOUBLE, DATE, BOOLEAN, BIG_INTEGER, MULTILINE_TEXT
  EntityType,            // Entity, ChoiceSet, InternalEntity, SystemEntity
  FieldDisplayType,      // Basic, Relationship, File, ChoiceSetSingle, ChoiceSetMultiple, AutoNumber
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

### updateRecordById(entityId: string, recordId: string, data: Record<string, any>, options?: EntityUpdateRecordOptions)

Returns `Promise<EntityUpdateRecordResponse>` — the updated single record. **Triggers Data Fabric trigger events** (unlike the bulk `updateRecordsById`). Use this when you need trigger events to fire for the updated record. Options: `expansionLevel`.

### updateRecordsById(id: string, data: EntityRecord[], options?: EntityUpdateRecordsOptions)

Returns `Promise<EntityUpdateResponse>` with `{ successRecords, failureRecords }`. Each record in `data` MUST include an `Id` field. Options: `expansionLevel`, `failOnFirst`. **Does NOT trigger events** — use `updateRecordById` if you need trigger events.

### deleteRecordsById(id: string, recordIds: string[], options?: EntityDeleteRecordsOptions)

Returns `Promise<EntityDeleteResponse>` with `{ successRecords, failureRecords }`. Options: `failOnFirst`.

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
- `entity.deleteRecords(recordIds: string[], options?)` -> `Promise<EntityDeleteResponse>`
- `entity.getAllRecords(options?)` -> `NonPaginatedResponse<EntityRecord>` or `PaginatedResponse<EntityRecord>`
- `entity.getRecord(recordId, options?)` -> `Promise<EntityRecord>`
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
