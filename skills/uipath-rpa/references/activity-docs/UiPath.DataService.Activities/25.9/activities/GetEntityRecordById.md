# GetEntityRecordById

Retrieves a single record from a Data Fabric entity by its ID. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the record to retrieve (validated — null produces error) |
| `OutputEntity` | `OutArgument<TEntity>` | Yes | — | Output | Variable to receive the retrieved record |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Folder scope writes `ScopeValue="Folder"`, `SolutionEntityKey` (resource UUID, design-time only) and `SolutionEntityName` (binding key + display name); at runtime the activity reads `Entity.<SolutionEntityName>.folderPath` from `bindings_v2.json` → Orchestrator's `resourceOverwrites` and injects `X-UiPath-FolderPath`. Tenant scope leaves the three properties unset. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

No `RecordState` or `IsInRecordView` — read-only operation.

## XAML Example

```xml
<uda:GetEntityRecordById
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Get ENTITY_NAME by ID"
    EntityId="ENTITY_GUID"
    RecordId="[recordIdVariable]"
    ExpansionDepth="2"
    OutputEntity="[resultVariable]"
    TimeoutInMs="30000" />
```
