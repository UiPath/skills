# CreateMultipleEntityRecords

Creates multiple records in a Data Fabric entity in a single batch operation. Category: **DataService.Batch**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<TEntity>>` | Yes | — | Input | Collection of entity objects to create (`[RequiredArgument]`) |
| `OutputRecords` | `OutArgument<IList<TEntity>>` | No | — | Output | Successfully created records |
| `FailedRecords` | `OutArgument<IList<Tuple<string, TEntity>>>` | No | — | Output | Failed records with error messages |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | Options | If `true`, continues processing remaining records when one fails; if `false`, stops on first failure |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Folder scope writes `ScopeValue="Folder"`, `SolutionEntityKey` (resource UUID, design-time only) and `SolutionEntityName` (binding key + display name); at runtime the activity reads `Entity.<SolutionEntityName>.folderPath` from `bindings_v2.json` → Orchestrator's `resourceOverwrites` and injects `X-UiPath-FolderPath`. Tenant scope leaves the three properties unset. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

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
