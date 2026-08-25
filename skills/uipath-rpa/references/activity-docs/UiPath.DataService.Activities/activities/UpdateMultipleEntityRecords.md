# Update Multiple Entity Records

`UiPath.DataService.Activities.UpdateMultipleEntityRecords<TEntity>`

**Package:** `UiPath.DataService.Activities`

Updates multiple records in a Data Fabric entity in a single batch operation.

**Category:** Data Service.Batch

> **Batch vs single — use this for N records.** For exactly one record with design-time field bindings, use [UpdateEntityRecord](UpdateEntityRecord.md) — it accepts `RecordId` directly and exposes Studio's card UI via `RecordState.SelectedFields`. Batch requires each entity in `InputRecords` to have its `Id` property set. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<TEntity>>` | Yes | — | Collection of entity objects to update (`[RequiredArgument]`) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion in response (range: 1–3, max `3`). On write, relationship fields on each input entity take **only** the target record's Id GUID — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputRecords` | `OutArgument<IList<TEntity>>` | No | — | Successfully updated records |
| `FailedRecords` | `OutArgument<IList<Tuple<string, TEntity>>>` | No | — | Failed records with error messages |

### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | If `true`, continues processing remaining records when one fails |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example

```xml
<uda:UpdateMultipleEntityRecords
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Update Multiple ENTITY_NAME Records"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    ContinueBatchOnFailure="True"
    InputRecords="[recordsCollection]"
    OutputRecords="[successRecords]"
    FailedRecords="[failedRecords]"
    TimeoutInMs="30000" />
```

## Key Rules

- Each entity object in `InputRecords` must have its `Id` property set to the record GUID being updated
- `FailedRecords` contains `Tuple<string, TEntity>` — `Item1` is the error message, `Item2` is the failed record
- Same batch failure behavior as `CreateMultipleEntityRecords`
