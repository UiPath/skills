# XAML Data Service Activities

Activity patterns for `UiPath.DataService.Activities`. All activities are generic (`<TEntity>`) and operate on Data Fabric entity records.

## Package

`UiPath.DataService.Activities`

## Prerequisites

1. **Package dependency**: `UiPath.DataService.Activities` in `project.json` `dependencies`
2. **Entity import**: Use Studio > Data Service tab > "Import Entities" to pull entity definitions from the tenant. This generates a compiled assembly at `.local/.entities/<hash>/DataService.<ProjectName>.dll`
3. **`entitiesStores` in project.json**:
   ```json
   "entitiesStores": [
     {
       "serviceDocument": ".entities/EntitiesStore.json",
       "namespace": "<ProjectName>"
     }
   ]
   ```
4. **Entity metadata** lives in `.entities/EntitiesStore.json` — use it to look up entity IDs, field IDs, field names, types, and required flags

Only entities explicitly imported via Studio are available as CLR types in the generated DLL. An entity present in `EntitiesStore.json` but not imported produces: `Cannot create unknown type '{clr-namespace:...}EntityName'`.

## XAML Namespace Declarations

```xml
xmlns:uda="clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
xmlns:udam="clr-namespace:UiPath.DataService.Activities.Models;assembly=UiPath.DataService.Activities.Core"
xmlns:udd="clr-namespace:UiPath.DataService.Definition;assembly=UiPath.DataService.Definition"
xmlns:local="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"
```

The `local` namespace **must** include `assembly=DataService.<ProjectName>`. Without the assembly qualifier, the XAML parser cannot locate entity types: `Cannot create unknown type '{clr-namespace:<ProjectName>}EntityName'`.

Namespace imports for `TextExpression.NamespacesForImplementation`:
```xml
<x:String>UiPath.DataService.Activities</x:String>
<x:String>UiPath.DataService.Activities.Models</x:String>
<x:String>UiPath.DataService.Definition</x:String>
<x:String><ProjectName></x:String>
```

Assembly references for `TextExpression.ReferencesForImplementation`:
```xml
<AssemblyReference>UiPath.DataService.Activities.Core</AssemblyReference>
<AssemblyReference>UiPath.DataService.Definition</AssemblyReference>
<AssemblyReference>DataService.<ProjectName></AssemblyReference>
```

## Activity Categories

| Category | Activities | Description |
|----------|-----------|-------------|
| **DataService.Entity Record** | `CreateEntityRecord`, `UpdateEntityRecord`, `DeleteEntityRecord`, `GetEntityRecordById`, `QueryEntityRecords` | Single-record CRUD operations |
| **DataService.Batch** | `CreateMultipleEntityRecords`, `UpdateMultipleEntityRecords`, `DeleteMultipleEntityRecords` | Bulk operations on multiple records |
| **DataService.File** | `UploadFileToRecordField`, `DownloadFileFromRecordField`, `DeleteFileFromRecordField` | File attachment operations on entity fields |

## Generic Type Argument

All activities use `x:TypeArguments` — the value **must** be a concrete entity type from the `local:` namespace, never `udd:IEntity`:

```xml
<!-- Wrong — interface is rejected -->
<uda:CreateEntityRecord x:TypeArguments="udd:IEntity" ... />

<!-- Right — concrete entity type -->
<uda:CreateEntityRecord x:TypeArguments="local:YourEntityName" ... />
```

Using `udd:IEntity` produces: `Selected Entity type (UiPath.DataService.Definition.IEntity) is not valid`.

## Shared Properties (All Activities)

| Property | Type | Default | Category | Description |
|----------|------|---------|----------|-------------|
| `EntityId` | `InArgument<Guid>` | — | — | Entity GUID from `EntitiesStore.json` → `Entities[].Id` |
| `ContinueOnError` | `InArgument<bool>` | `false` | Common | Continue workflow on activity error |
| `TimeoutInMs` | `InArgument<int>` | `30000` | Common | Timeout in milliseconds |

## Entity Metadata — EntitiesStore.json

`EntitiesStore.json` structure for looking up entity and field identifiers:

```json
{
  "Entities": [
    {
      "Id": "<entity-guid>",
      "Name": "EntityName",
      "Fields": [
        {
          "Id": "<field-guid>",
          "Name": "FieldName",
          "IsSystemField": false,
          "IsRequired": true,
          "SqlType": { "Name": "NVARCHAR" },
          "FieldDisplayType": "Basic"
        }
      ]
    }
  ]
}
```

**System fields** (`IsSystemField: true`) — `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy` — are managed by Data Service. Skip them when building field bindings for Create/Update activities.

## SqlType to XAML Type Mapping

| SqlType.Name | x:TypeArguments | Notes |
|-------------|-----------------|-------|
| `NVARCHAR` | `x:String` | Text fields |
| `MULTILINE` | `x:String` | Multi-line text |
| `INT` | `x:Int32` | Integer |
| `BIGINT` | `x:Int64` | Long integer |
| `FLOAT` | `x:Double` | Floating-point |
| `DECIMAL` | `x:Decimal` | Decimal number |
| `BIT` | `x:Boolean` | True/false |
| `DATETIMEOFFSET` | `x:String` | Pass as ISO 8601 string |
| `DATE` | `x:String` | Pass as ISO 8601 date string |
| `UNIQUEIDENTIFIER` | `x:String` | Pass as GUID string |

## FieldDisplayType Values

| FieldDisplayType | Meaning |
|-----------------|---------|
| `Basic` | Standard scalar field (text, number, boolean, date) |
| `Relationship` | Foreign key reference to another entity (ManyToOne) |
| `File` | File attachment field |
| `ChoiceSetSingle` | Single-select choice set |
| `ChoiceSetMultiple` | Multi-select choice set |
| `AutoNumber` | Auto-incrementing numeric field |

## Common Pitfalls

- `x:TypeArguments` must be a concrete entity type — `udd:IEntity` is rejected at validation
- The `local` xmlns must include the full `assembly=DataService.<ProjectName>` qualifier
- `EntitiesStore.json` contains all tenant entities, but only explicitly imported ones have CLR types in the generated DLL
- For Create/Update activities: `InputEntity`, `IsInRecordView`, and `RecordState.SelectedFields` must all be set together — omitting any one fails validation (see individual activity docs)
- Entity fields are NOT WF4 properties on the activity — they must be set via `InputEntity` expression and `RecordState.SelectedFields`, not as `<uda:CreateEntityRecord.FieldName>`
