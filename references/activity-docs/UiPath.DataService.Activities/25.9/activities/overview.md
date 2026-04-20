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

**Stop if prerequisites are not met.** Before proceeding with any Data Service activity:
1. Read `project.json` and check `entitiesStores`. If the array is missing, empty, or has no entries → **stop and tell the user**: "No entity stores configured. Import entities via Studio > Data Service tab > Import Entities, then retry."
2. Check that `{PROJECT_DIR}/.entities/EntitiesStore.json` exists. If the file is missing → **stop and tell the user**: "EntitiesStore.json not found. The project has no imported entities. Import entities via Studio > Data Service tab > Import Entities, then retry."
3. Read `EntitiesStore.json` and check `Entities`. If the array is empty → **stop and tell the user**: "EntitiesStore.json contains no entities. The tenant may have no entities, or none were imported. Import entities via Studio, then retry."

Do not attempt to create Data Service XAML without a valid, non-empty `EntitiesStore.json` — the generated code will fail validation.

Only entities explicitly imported via Studio are available as CLR types in the generated DLL. An entity present in `EntitiesStore.json` but not imported produces: `Cannot create unknown type '{clr-namespace:...}EntityName'`.

### Entity Lookup Scope

**Only read `EntitiesStore.json` from the resolved `PROJECT_DIR`.** The path is always `{PROJECT_DIR}/.entities/EntitiesStore.json`. Do not search for `EntitiesStore.json` in sibling directories, parent folders, or other projects — even if multiple projects are open in Studio. If the entity you need is not in the project's own `EntitiesStore.json`, ask the user to import it via Studio > Data Service tab > "Import Entities" rather than looking elsewhere.

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

### Solution Scope Properties (Conditional)

> **These properties only apply when the project has a SolutionId** (i.e., is part of a Data Service solution). For standalone projects without a SolutionId, **omit these properties entirely** — they have no effect and setting them on a standalone project may cause unexpected behavior. See [Solution Context](#solution-context-folder-vs-tenant-scope) for how to determine scope.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ScopeValue` | `InArgument<string>` | `"Tenant"` | `"Folder"` or `"Tenant"`. Use Folder when project has a SolutionId; Tenant for standalone. See [Solution Context](#solution-context-folder-vs-tenant-scope) |
| `SolutionEntityKey` | `InArgument<string>` | `{x:Null}` | Solution resource key for the entity. Set only when ScopeValue is Folder |
| `SolutionEntityName` | `InArgument<string>` | `{x:Null}` | Entity display name in the solution. Set only when ScopeValue is Folder |

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

## Solution Context (Folder vs Tenant Scope)

Data Service activities support two scoping modes controlled by whether the project has a **Solution ID** (i.e., is part of a Data Service solution). This is determined by `IUserDesignerContext.SolutionId` — NOT by which Studio product (Desktop vs Web) is running.

### When to use each scope

| Condition | ScopeValue | Entity source |
|-----------|-----------|---------------|
| Project has a SolutionId (solution context) | `"Folder"` (default) or `"Tenant"` | Folder scope: entity resolved from solution resources. Tenant scope: entity resolved from tenant-level Data Service API |
| Project has NO SolutionId (standalone) | `"Tenant"` (only option) | Entity resolved from tenant-level Data Service API |

### XAML properties for solution context

| Property | When to set | Value |
|----------|-------------|-------|
| `ScopeValue` | Always | `"Folder"` or `"Tenant"`. Standalone projects: always `"Tenant"` |
| `SolutionEntityKey` | Folder scope only | Solution resource key identifying the entity (e.g., `"entity_key_abc"`) |
| `SolutionEntityName` | Folder scope only | Display name of the entity in the solution |

When scope is **Tenant** or the project is standalone, set `SolutionEntityKey` and `SolutionEntityName` to `{x:Null}`.

### Runtime behavior difference

- **Folder scope**: the activity injects an `X-UiPath-FolderPath` header in API requests, routing the operation to the correct solution folder
- **Tenant scope**: no folder header — the operation targets the tenant-level Data Service directly

### Key rule

Do NOT check for Studio Desktop vs Studio Web to decide scope. The only factor is whether `SolutionId` exists in the project context. If the project is in a solution, default to Folder scope. If standalone, use Tenant scope.

## Common Pitfalls

- `x:TypeArguments` must be a concrete entity type — `udd:IEntity` is rejected at validation
- The `local` xmlns must include the full `assembly=DataService.<ProjectName>` qualifier
- `EntitiesStore.json` contains all tenant entities, but only explicitly imported ones have CLR types in the generated DLL. If validation returns `Cannot create unknown type '{clr-namespace:...}EntityName'` — **stop and ask the user** to import the entity via Studio > Data Service tab > "Import Entities". Do not attempt to fix this by changing namespaces or assembly references.
- For Create/Update activities, set `IsInRecordView="[False]"` and populate two things:
  1. **`InputEntityInFieldView`** — object-initializer expression (runtime reads this)
  2. **`RecordState.SelectedFields`** — field GUIDs and values (Studio card UI reads this)
  - Do NOT use `InputEntity` — Studio syncs `SelectedFields` → `InputEntityInFieldView` on load but never syncs `SelectedFields` → `InputEntity`, causing desync bugs
- Entity fields are NOT WF4 properties on the activity — they must be set via `InputEntityInFieldView` expression and `RecordState.SelectedFields`, not as `<uda:CreateEntityRecord.FieldName>`
