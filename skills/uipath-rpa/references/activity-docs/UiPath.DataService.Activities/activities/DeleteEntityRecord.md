# Delete Entity Record

`UiPath.DataService.Activities.DeleteEntityRecord<TEntity>`

**Package:** `UiPath.DataService.Activities`

Deletes a record from a Data Fabric entity by record ID.

**Category:** Data Service.Entity Record

> **Single vs batch — use this only for ONE record.** For N records, use [DeleteMultipleEntityRecords](DeleteMultipleEntityRecords.md) — accepts an `ICollection<Guid>`, makes one HTTP call, and returns failed IDs via `FailedRecords`. Deleting inside a `ForEach` loop is a performance anti-pattern. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` (marked `[RequiredArgument]`) |
| `RecordId` | `InArgument<Guid>` | Yes | — | GUID of the record to delete |
| `InputEntity` | `InArgument<TEntity>` | No | — | Entity object (alternative to RecordId for type resolution) |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

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
