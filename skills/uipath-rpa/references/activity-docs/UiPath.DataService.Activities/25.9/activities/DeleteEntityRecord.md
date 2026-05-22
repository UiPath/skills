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

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Folder scope writes `ScopeValue="Folder"`, `SolutionEntityKey` (resource UUID, design-time only) and `SolutionEntityName` (binding key + display name); at runtime the activity reads `Entity.<SolutionEntityName>.folderPath` from `bindings_v2.json` → Orchestrator's `resourceOverwrites` and injects `X-UiPath-FolderPath`. Tenant scope leaves the three properties unset. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

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
