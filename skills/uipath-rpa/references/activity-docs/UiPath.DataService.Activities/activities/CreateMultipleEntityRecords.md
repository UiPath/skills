# Create Multiple Entity Records

`UiPath.DataService.Activities.CreateMultipleEntityRecords<TEntity>`

**Package:** `UiPath.DataService.Activities`

Creates multiple records in a Data Fabric entity in a single batch operation.

**Category:** Data Service.Batch

> **Batch vs single — use this for N records.** For exactly one record with design-time field bindings, use [CreateEntityRecord](CreateEntityRecord.md) — it exposes Studio's card UI via `RecordState.SelectedFields`. Picking batch for a single known record adds collection construction and `Tuple<string, TEntity>` unpacking for no gain. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<TEntity>>` | Yes | — | Collection of entity objects to create (`[RequiredArgument]`) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion in response (range: 1–3, max `3`). On write, relationship fields on each input entity take **only** the target record's Id GUID — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputRecords` | `OutArgument<IList<TEntity>>` | No | — | Successfully created records |
| `FailedRecords` | `OutArgument<IList<Tuple<string, TEntity>>>` | No | — | Failed records with error messages |

### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | If `true`, continues processing remaining records when one fails; if `false`, stops on first failure |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example

```xml
<uda:CreateMultipleEntityRecords
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Create Multiple ENTITY_NAME Records"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    ContinueBatchOnFailure="True"
    InputRecords="[recordsCollection]"
    OutputRecords="[successRecords]"
    FailedRecords="[failedRecords]"
    TimeoutInMs="30000" />
```

## Key Rules

- `FailedRecords` contains `Tuple<string, TEntity>` — `Item1` is the error message, `Item2` is the failed record
- If any records fail and `ContinueBatchOnFailure` is `true`, the activity throws after processing all records with a message indicating how many failed
- The `InputRecords` collection must contain fully constructed entity objects (same as `InputEntity` for single creates)
