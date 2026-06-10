# Delete Multiple Entity Records

`UiPath.DataService.Activities.DeleteMultipleEntityRecords<TEntity>`

**Package:** `UiPath.DataService.Activities`

Deletes multiple records from a Data Fabric entity by their IDs.

**Category:** Data Service.Batch

> **Batch vs single — use this for N record IDs.** For exactly one record, use [DeleteEntityRecord](DeleteEntityRecord.md) — it takes a single `RecordId` directly. Picking batch for one ID adds collection construction for no gain. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<Guid>>` | Yes | — | Collection of record GUIDs to delete (`[RequiredArgument]`) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `FailedRecords` | `OutArgument<IList<Guid>>` | No | — | GUIDs of records that failed to delete |

### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | If `true`, continues deleting remaining records when one fails |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

No `ExpansionDepth` or `OutputRecords` — delete returns only failed record IDs, not entity objects.

## XAML Example

```xml
<uda:DeleteMultipleEntityRecords
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Delete Multiple ENTITY_NAME Records"
    EntityId="ENTITY_GUID"
    ContinueBatchOnFailure="True"
    InputRecords="[recordIdCollection]"
    FailedRecords="[failedRecordIds]"
    TimeoutInMs="30000" />
```

## Key Rules

- `InputRecords` is a collection of `Guid` values (record IDs), not entity objects
- `FailedRecords` is a list of `Guid` values — the IDs of records that failed to delete
- If any records fail, the activity throws after processing all records
