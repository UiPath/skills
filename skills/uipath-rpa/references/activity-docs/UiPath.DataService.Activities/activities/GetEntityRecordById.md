# Get Entity Record By Id

`UiPath.DataService.Activities.GetEntityRecordById<TEntity>`

**Package:** `UiPath.DataService.Activities`

Retrieves a single record from a Data Fabric entity by its ID.

**Category:** Data Service.Entity Record

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | GUID of the record to retrieve (validated — null produces error) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion in response (range: 1–3, max `3`). Controls relationship-field shape on the returned record — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputEntity` | `OutArgument<TEntity>` | Yes | — | Variable to receive the retrieved record |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

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
