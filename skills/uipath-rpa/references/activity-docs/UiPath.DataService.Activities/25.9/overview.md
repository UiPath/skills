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
2. Read the `serviceDocument` path from `entitiesStores[0]` and check that the file exists. If the file is missing → **stop and tell the user**: "EntitiesStore.json not found. The project has no imported entities. Import at least one entity via Studio > Data Service tab > Import Entities, then retry."
3. Read `EntitiesStore.json` and check `Entities`. If the array is empty → **stop and tell the user**: "EntitiesStore.json contains no entities. The tenant may have no entities, or none were imported. Import entities via Studio, then retry."

Do not attempt to create Data Service XAML without a valid, non-empty `EntitiesStore.json` — the generated code will fail validation.

Only entities explicitly imported via Studio are available as CLR types in the generated DLL. An entity present in `EntitiesStore.json` but not imported produces: `Cannot create unknown type '{clr-namespace:...}EntityName'`.

### Entity Lookup Scope

**Only read `EntitiesStore.json` from the current project.** Resolve the path via `project.json` → `entitiesStores[0].serviceDocument`. Do not search for `EntitiesStore.json` in sibling directories, parent folders, or other projects — even if multiple projects are open in Studio. If the entity you need is not in the project's own `EntitiesStore.json`, ask the user to import it via Studio > Data Service tab > "Import Entities" rather than looking elsewhere.

## XAML Namespace Declarations

```xml
xmlns:uda="clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
xmlns:udam="clr-namespace:UiPath.DataService.Activities.Models;assembly=UiPath.DataService.Activities.Core"
xmlns:udd="clr-namespace:UiPath.DataService.Definition;assembly=UiPath.DataService.Definition"
xmlns:upr="clr-namespace:UiPath.Platform.ResourceHandling;assembly=UiPath.Platform"
xmlns:local="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"
```

- The `local` namespace **must** include `assembly=DataService.<ProjectName>`. Without the assembly qualifier, the XAML parser cannot locate entity types: `Cannot create unknown type '{clr-namespace:<ProjectName>}EntityName'`.
- The `upr` namespace is required for file activity variables — `DownloadFileFromRecordField.DownloadedFileResource` outputs `upr:ILocalResource`. See [DownloadFileFromRecordField](activities/DownloadFileFromRecordField.md).

Namespace imports for `TextExpression.NamespacesForImplementation`:
```xml
<x:String>UiPath.DataService.Activities</x:String>
<x:String>UiPath.DataService.Activities.Models</x:String>
<x:String>UiPath.DataService.Definition</x:String>
<x:String>UiPath.Platform.ResourceHandling</x:String>
<x:String><ProjectName></x:String>
```

Assembly references for `TextExpression.ReferencesForImplementation`:
```xml
<AssemblyReference>UiPath.DataService.Activities.Core</AssemblyReference>
<AssemblyReference>UiPath.DataService.Definition</AssemblyReference>
<AssemblyReference>UiPath.Platform</AssemblyReference>
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

These three properties exist on every activity's base class but Studio only renders the higher-level controls that *write* them when the project has a non-empty `SolutionId`. For standalone projects, leave them unset (Studio omits them entirely). They are never user-typed — they are populated by Studio rules from the scope radio + entity picker. See [Solution Context](#solution-context-folder-vs-tenant-scope).

| Property | Type | Default | Set by | Read at |
|----------|------|---------|--------|---------|
| `ScopeValue` | `InArgument<string>` | (unset) | Scope radio (`"Folder"` / `"Tenant"`) | Design time: gates `BindingsKey`. Not sent to API. |
| `SolutionEntityKey` | `InArgument<string>` | `{x:Null}` | Entity picker — `key` field of the selected solution resource | Design time only: fetches entity schema JSON via solution resources. **Not used at runtime.** |
| `SolutionEntityName` | `InArgument<string>` | `{x:Null}` | Entity picker — `name` field of the selected solution resource | Both: design time for the entity binding contract; runtime as the lookup key for `Entity.<name>.folderPath` (see [Runtime mechanism](#runtime-mechanism-folder-vs-tenant)). |

## Entity Metadata — EntitiesStore.json

`EntitiesStore.json` structure for looking up entity and field identifiers:

```json
{
  "StoreUrl": "https://<tenant-url>/datafabric/<TenantName>/dataservice_/entities",
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
          "SqlType": { "Name": "NVARCHAR", "LengthLimit": 300, "MaxValue": null, "MinValue": null, "DecimalPrecision": null },
          "FieldDisplayType": "Basic",
          "ReferenceEntity": null
        },
        {
          "Id": "<field-guid>",
          "Name": "RelationshipFieldName",
          "IsSystemField": false,
          "IsRequired": false,
          "SqlType": { "Name": "UNIQUEIDENTIFIER" },
          "FieldDisplayType": "Relationship",
          "ReferenceEntity": { "Name": "ReferencedEntityName", "Id": "<referenced-entity-guid>", "FolderId": "<folder-guid>" }
        }
      ]
    }
  ]
}
```

> `EntitiesStore.json` contains **all entities in the tenant** after the first entity import — not just the imported one. However, only explicitly imported entities have CLR types in the generated DLL.

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

Activities behave differently when the host project lives inside a `.uipx` solution. The switch is `IUserDesignContext.SolutionId` (Studio Desktop or Web — product does not matter). When non-empty, Studio renders solution-aware controls; runtime resolves the folder path from bindings injected by Orchestrator.

### What Studio renders

Studio never exposes the three raw XAML properties (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) in the property grid. They stay `IsVisible=false` and are written by rules from these higher-level controls:

| Control | Visible when | Type | Writes |
|---------|--------------|------|--------|
| `Scope` | `SolutionId` is non-empty | `RadioGroup` — `Folder` / `Tenant` (resource keys `EntityFolderScope`, `EntityTenantScope`) | `ScopeValue` |
| `SolutionEntity` | `SolutionId` non-empty AND `Scope == "Folder"` | `SolutionResourcesWidget` (`ResourceType="entity"`, `ExpectedProperties=["name","key"]`) | `SolutionEntityKey` ← `key`, `SolutionEntityName` ← `name`, and re-morphs the generic `TEntity` type via `EntityJitter` + `IDesignerCustomTypesService` |
| `Entity` (legacy picker) | `SolutionId` empty OR `Scope == "Tenant"` | Studio's classic entity dropdown (populated from `IDesignerDataService.GetEntities()`) | `EntityId` + assembly-cached entity DTO |

Toggling `Scope` Folder→Tenant clears `SolutionEntity.Value`, `SolutionEntityKey.Value`, `SolutionEntityName.Value`, `Entity.Value` and re-initializes the entity picker (`BaseSolutionResourceActivityViewModel.UpdateEntityChoiceOnScope`).

### Runtime mechanism (Folder vs Tenant)

Runtime ignores `SolutionEntityKey` entirely. The activity computes `BindingsKey` from `SolutionEntityName` only when `ScopeValue == "Folder"`:

```text
BindingsKey = (ScopeValue == "Folder") ? SolutionEntityName.literal : null
folderPath  = BindingsHelper.GetBindingValue($"Entity.{BindingsKey}.folderPath", ...)
            // resolves from Orchestrator's resourceOverwrites for the current process
if (folderPath != null) headers["X-UiPath-FolderPath"] = folderPath
```

- **Folder scope, binding present** → `X-UiPath-FolderPath: <folderPath>` injected on every HTTP call (Create/Update/Delete/Query/File). Data Service routes the operation to that folder's entity instance.
- **Folder scope, binding missing** → no header; falls through to tenant resolution by entity name.
- **Tenant scope** → `BindingsKey` is `null`; no header; tenant-level routing.
- **Standalone** → identical to Tenant scope. If a XAML happens to contain stale `ScopeValue="Folder"` + `SolutionEntityName=<x>` literals from a previous solution context, the runtime still does the bindings lookup — but `resourceOverwrites` won't contain a matching entry outside a deployed solution, so the header is omitted and behavior collapses to Tenant. Not destructive, but leave the three properties unset to avoid confusion.

`SolutionEntityKey` is design-time only: it's the lookup key for `ISolutionResources.GetResourceConfigurationAsync(key)`, which returns the entity schema JSON (used to JIT-compile the `TEntity` CLR type into the in-memory `DataService.<ProjectName>` assembly).

### `bindings_v2.json` round-trip

The runtime binding that feeds `folderPath` is declared in each project's `bindings_v2.json` (one entry per solution-scoped entity):

```json
{
  "resourceType": 6,
  "originalResourceType": "Entity",
  "dynamicValues": {
    "name":       { "defaultValue": "<SolutionEntityName>", "isExpression": false },
    "folderPath": { "defaultValue": "<folder-or-special>",  "isExpression": false }
  }
}
```

- `dynamicValues.name.defaultValue` matches the XAML `SolutionEntityName` and is the lookup key.
- `dynamicValues.folderPath.defaultValue` is the value injected as `X-UiPath-FolderPath`. The sentinel values `"."` and `"solution_folder"` are normalized to undefined → tenant scope.
- At deploy time, `uip solution resource refresh` reads each project's `bindings_v2.json`, creates a matching solution resource (kind `Entity`), and packs everything into the `.uipx`. At runtime, Orchestrator hydrates `resourceOverwrites` from the deployment's resource bindings.

### Discovering values for XAML

When authoring a solution-scoped Data Service activity, the agent should NOT hand-pick GUIDs or names. Use the solution CLI to list the entities available in the host solution:

```bash
uip solution resource list --kind Entity --output json
```

Each entry's `Key` field is the `SolutionEntityKey` (resource key UUID); `Name` is the `SolutionEntityName`. For the full resource spec:

```bash
uip solution resource get <KEY> --output json
```

After editing a project's `bindings_v2.json` (e.g., adding a new entity reference), sync into the solution:

```bash
uip solution resource refresh --output json
```

These commands live in the `uipath-solution` skill — see [develop-solution.md](../../../../../uipath-solution/references/operate/develop-solution.md) for the full lifecycle (init → project add → resource refresh → pack → publish → deploy).

> **Cross-skill scope.** The `uip df` CLI in `uipath-data-fabric` is tenant-only — no `--solution-id`, no `--folder-path`. Do not use `uip df entities list` to populate `SolutionEntityKey` / `SolutionEntityName`. Use `uip solution resource list --kind Entity` instead.

### Key rule

`SolutionId` presence is the only signal. Do not branch on Studio Desktop vs Studio Web, or on `targetFramework`. If the project has a non-empty `SolutionId` and the entity lives in solution resources, Folder scope is the default; otherwise Tenant.

## Common Pitfalls

- `x:TypeArguments` must be a concrete entity type — `udd:IEntity` is rejected at validation
- The `local` xmlns must include the full `assembly=DataService.<ProjectName>` qualifier
- `EntitiesStore.json` contains all tenant entities, but only explicitly imported ones have CLR types in the generated DLL. If validation returns `Cannot create unknown type '{clr-namespace:...}EntityName'` — **stop and ask the user** to import the entity via Studio > Data Service tab > "Import Entities". Do not attempt to fix this by changing namespaces or assembly references.
- For Create/Update activities, set `IsInRecordView="[False]"` and populate two things:
  1. **`InputEntityInFieldView`** — object-initializer expression (runtime reads this)
  2. **`RecordState.SelectedFields`** — field GUIDs and values (Studio card UI reads this)
  - Do NOT use `InputEntity` — Studio syncs `SelectedFields` → `InputEntityInFieldView` on load but never syncs `SelectedFields` → `InputEntity`, causing desync bugs
- Entity fields are NOT WF4 properties on the activity — they must be set via `InputEntityInFieldView` expression and `RecordState.SelectedFields`, not as `<uda:CreateEntityRecord.FieldName>`
