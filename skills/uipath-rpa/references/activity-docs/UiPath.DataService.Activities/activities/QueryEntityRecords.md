# Query Entity Records

`UiPath.DataService.Activities.QueryEntityRecords<TEntity>`

**Package:** `UiPath.DataService.Activities`

Queries records from a Data Fabric entity with optional filtering, sorting, and pagination.

**Category:** Data Service.Entity Record

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `Top` | `InArgument<int>` | No | `100` | Maximum records to return (range: 1–1000; use `Skip` for pagination beyond 1000) |
| `Skip` | `InArgument<long>` | No | `0` | Number of records to skip (pagination offset, `>= 0`). If `Skip` exceeds the total matching records, the result is empty. |
| `SortByField` | `InArgument<string>` | No | — | Field name to sort by |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion (range: 1–3, max `3`). Controls relationship-field shape on returned records and gates dot-notation filterability — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |
| `FilterArguments` | `FilterArgument` | No | — | Filter definition (set via Studio designer; `[Browsable(false)]`) |
| `FilterValues` | `IList<InArgument>` | No | — | Filter parameter values (set via Studio designer; `[Browsable(false)]`) |
| `SortAscending` | `InArgument<bool>` | No | `true` | Sort direction |
| `QueriedEntityId` | `Guid` | No | — | **Deprecated — do not use.** Legacy design-time entity tracking (`[Browsable(false)]`). Use `EntityId` instead. |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputRecords` | `OutArgument<IList<TEntity>>` | Yes | — | Variable to receive the list of matching records |
| `TotalRecords` | `OutArgument<long>` | No | — | Variable to receive total count (before pagination) |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example (no filter)

```xml
<uda:QueryEntityRecords
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Query ENTITY_NAME Records"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    Top="100"
    Skip="0"
    SortByField="[&quot;Name&quot;]"
    SortAscending="True"
    OutputRecords="[resultsVariable]"
    TotalRecords="[totalCountVariable]"
    TimeoutInMs="30000" />
```

## Filter XAML Generation

`FilterArguments` and `FilterValues` are `[Browsable(false)]` — they do not appear in the Studio properties panel but can be generated in XAML. For structure, operator-string mappings, XML escaping, value-slot typing, nested-group templates, and worked examples, see [data-service-filter-builder-guide](../guides/data-service-filter-builder-guide.md).

## Key Rules

- `TotalRecords` returns the total count matching the filter, regardless of `Top`/`Skip` — useful for pagination logic
