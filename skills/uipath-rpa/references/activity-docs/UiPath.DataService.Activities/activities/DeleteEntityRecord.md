# Delete Entity Record

`UiPath.DataService.Activities.DeleteEntityRecord<TEntity>`

**Package:** `UiPath.DataService.Activities`

Deletes a record from a Data Fabric entity by record ID.

**Category:** Data Service.Entity Record

> **Single vs batch — use this only for ONE record.** For N records, use [DeleteMultipleEntityRecords](DeleteMultipleEntityRecords.md) — accepts an `ICollection<Guid>`, makes one HTTP call, and returns failed IDs via `FailedRecords`. Deleting inside a `ForEach` loop is a performance anti-pattern. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | Input | Entity GUID from `EntitiesStore.json` (marked `[RequiredArgument]`) |
| `RecordId` | `InArgument<Guid>` | Yes | — | — | GUID of the record to delete |
| `InputEntity` | `InArgument<TEntity>` | No | — | Input | Entity object (alternative to RecordId for type resolution) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

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
