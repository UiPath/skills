# DeleteEntityRecord

Deletes a record from a Data Fabric entity by record ID. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | Input | Entity GUID from `EntitiesStore.json` (marked `[RequiredArgument]`) |
| `RecordId` | `InArgument<Guid>` | Yes | — | — | GUID of the record to delete |
| `InputEntity` | `InArgument<TEntity>` | No | — | Input | Entity object (alternative to RecordId for type resolution) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

No `RecordState`, `IsInRecordView`, or `ExpansionDepth` — delete does not set field values or return an entity.

## XAML Example

```xml
<uda:DeleteEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Delete ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    RecordId="[recordIdVariable]"
    TimeoutInMs="30000" />
```
