# GetEntityRecordById

Retrieves a single record from a Data Fabric entity by its ID. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the record to retrieve (validated — null produces error) |
| `OutputEntity` | `OutArgument<TEntity>` | Yes | — | Output | Variable to receive the retrieved record |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3, max `3`). Controls relationship-field shape on the returned record — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

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
