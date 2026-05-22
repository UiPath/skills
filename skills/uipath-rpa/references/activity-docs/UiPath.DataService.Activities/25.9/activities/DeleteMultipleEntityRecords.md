# DeleteMultipleEntityRecords

Deletes multiple records from a Data Fabric entity by their IDs. Category: **DataService.Batch**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<Guid>>` | Yes | — | Input | Collection of record GUIDs to delete (`[RequiredArgument]`) |
| `FailedRecords` | `OutArgument<IList<Guid>>` | No | — | Output | GUIDs of records that failed to delete |
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | Options | If `true`, continues deleting remaining records when one fails |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Folder scope writes `ScopeValue="Folder"`, `SolutionEntityKey` (resource UUID, design-time only) and `SolutionEntityName` (binding key + display name); at runtime the activity reads `Entity.<SolutionEntityName>.folderPath` from `bindings_v2.json` → Orchestrator's `resourceOverwrites` and injects `X-UiPath-FolderPath`. Tenant scope leaves the three properties unset. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

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
