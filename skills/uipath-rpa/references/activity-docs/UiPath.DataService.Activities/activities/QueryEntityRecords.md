# Query Entity Records

`UiPath.DataService.Activities.QueryEntityRecords<TEntity>`

**Package:** `UiPath.DataService.Activities`

Queries records from a Data Fabric entity with optional filtering, sorting, and pagination.

**Category:** Data Service.Entity Record

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
| `Top` | `InArgument<int>` | No | `100` | Pagination | Maximum records to return (range: 1–1000; use `Skip` for pagination beyond 1000) |
| `Skip` | `InArgument<long>` | No | `0` | Pagination | Number of records to skip (pagination offset, `>= 0`). If `Skip` exceeds the total matching records, the result is empty. |
| `SortByField` | `InArgument<string>` | No | — | Options | Field name to sort by |
| `SortAscending` | `InArgument<bool>` | No | `true` | Options | Sort direction |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion (range: 1–3, max `3`). Controls relationship-field shape on returned records and gates dot-notation filterability — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

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

## Filter XAML Structure

`FilterArguments` and `FilterValues` are `[Browsable(false)]` properties — they do not appear in the Studio properties panel but can be generated in XAML. The filter structure uses:

- **`FilterArgument`** wrapping a root **`GroupFilter`** (Operator `AND` or `OR`)
- **`SimpleFilter`** elements inside the GroupFilter for each condition
- A flat **`FilterValues`** list of `InArgument` entries indexed by `SimpleFilter.ValueIndex`

Operator strings used in `SimpleFilter.Operator` (XAML internal names):

| Enum Name | XAML Operator String | Requires Value |
|-----------|---------------------|----------------|
| Contains | `contains` | Yes |
| NotContains | `not contains` | Yes |
| Equals | `=` | Yes |
| NotEqual | `!=` | Yes |
| StartsWith | `startswith` | Yes |
| EndsWith | `endswith` | Yes |
| MoreThan | `>` (XML-escape: `&gt;`) | Yes |
| LessThan | `<` (XML-escape: `&lt;`) | Yes |
| NoMoreThan | `<=` (XML-escape: `&lt;=`) | Yes |
| NoLessThan | `>=` (XML-escape: `&gt;=`) | Yes |
| IsEmpty | `is empty` | No (`<x:Null />`) |
| IsNotEmpty | `not empty` | No (`<x:Null />`) |
| In | `in` | Yes (`s:String[]`) |
| NotIn | `not in` | Yes (`s:String[]`) |
| IsTrue | `Equals true` | Yes (`x:Boolean` → `True`) |
| IsFalse | `Equals false` | Yes (`x:Boolean` → `False`) |
| IsNull | `is null` | No (`<x:Null />`) |
| IsNotNull | `is not null` | No (`<x:Null />`) |

> `IsNull` / `IsNotNull` are available in the Studio filter builder UI and at runtime.

For the complete filter generation guide — including XAML templates, field-type-to-operator mapping, nested group patterns, and worked examples — see [data-service-filter-builder-guide](../guides/data-service-filter-builder-guide.md).

## Key Rules

- `TotalRecords` returns the total count matching the filter, regardless of `Top`/`Skip` — useful for pagination logic
