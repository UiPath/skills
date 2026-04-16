# QueryEntityRecords

Queries records from a Data Fabric entity with optional filtering, sorting, and pagination. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `OutputRecords` | `OutArgument<IList<TEntity>>` | Yes | — | Output | Variable to receive the list of matching records |
| `TotalRecords` | `OutArgument<long>` | No | — | Pagination | Variable to receive total count (before pagination) |
| `FilterArguments` | `FilterArgument` | No | — | — | Filter definition (set via Studio designer; `[Browsable(false)]`) |
| `FilterValues` | `IList<InArgument>` | No | — | — | Filter parameter values (set via Studio designer; `[Browsable(false)]`) |
| `QueriedEntityId` | `Guid` | No | — | — | Entity GUID for query scope; `00000000-0000-0000-0000-000000000000` for all |
| `Top` | `InArgument<int>` | No | `100` | Pagination | Maximum records to return (range: 0–1000) |
| `Skip` | `InArgument<long>` | No | `0` | Pagination | Number of records to skip (pagination offset) |
| `SortByField` | `InArgument<string>` | No | — | Options | Field name to sort by |
| `SortAscending` | `InArgument<bool>` | No | `true` | Options | Sort direction |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion (range: 1–3) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

No `RecordState` or `IsInRecordView` — read-only operation.

## Filter Operators

The filter system supports these operators (from `QueryFilterOperator` enum):

| Operator | Description |
|----------|-------------|
| `Contains` | Field contains value |
| `NotContains` | Field does not contain value |
| `Equals` | Exact match |
| `NotEqual` | Not equal |
| `StartsWith` | Field starts with value |
| `EndsWith` | Field ends with value |
| `MoreThan` | Greater than (`>`) |
| `LessThan` | Less than (`<`) |
| `NoMoreThan` | Less than or equal (`<=`) |
| `NoLessThan` | Greater than or equal (`>=`) |
| `IsEmpty` | Field is empty |
| `IsNotEmpty` | Field is not empty |
| `In` | Field value in list |
| `NotIn` | Field value not in list |
| `IsTrue` | Boolean is true |
| `IsFalse` | Boolean is false |
| `IsNull` | Field is null |
| `IsNotNull` | Field is not null |

Filters use `FilterLogicalOperator`: `AND` (0) or `OR` (1) to combine conditions.

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

## Key Rules

- `FilterArguments` and `FilterValues` are designer-managed properties (`[Browsable(false)]`) — they are configured through Studio's query builder UI, not typically hand-written in XAML
- For programmatic filtering without the designer, use the query builder wizard in Studio to generate the filter XAML structure
- `Top` defaults to 100, capped at 1000 — use `Skip` for pagination beyond 1000 records
- `TotalRecords` returns the total count matching the filter, regardless of `Top`/`Skip` — useful for pagination logic
