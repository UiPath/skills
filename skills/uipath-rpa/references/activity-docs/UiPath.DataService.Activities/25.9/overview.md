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

**Before proceeding with any Data Service activity, verify entities are installed via CLI:**

1. Run:
   ```bash
   uip rpa data-fabric-entities list --project-dir "<PROJECT_DIR>" --output json
   ```
2. Check the output for entries with `"installed": true`.
   - Needed entity present with `installed: true` → prerequisites met. Read `EntitiesStore.json` (path: `entitiesStores[0].serviceDocument` in `project.json`) for field metadata, then proceed.
   - Needed entity absent or `installed: false` → go to **Auto-import** below.
   - `list` itself fails → apply error mitigations below.

**Auto-import (run before asking the user):**

a. Resolve the entity name from context (user's request or workflow intent). If no entity name is known from context, ask the user *which entity* to use — not to manually import.
b. Run:
   ```bash
   uip rpa data-fabric-entities install --add "<ENTITY_NAME>" --project-dir "<PROJECT_DIR>" --output json
   ```
c. On success, re-run `data-fabric-entities list` to confirm `installed: true`, then read `EntitiesStore.json` for metadata and proceed.
d. On failure, apply error mitigations below. Escalate to the user only for errors marked **Yes** that the mitigation cannot resolve.

**CLI error paths and mitigations:**

| Error signal | Cause | Mitigation | Escalate? |
|---|---|---|---|
| `errorMessage` contains `"read-only"` or `"cannot edit"` | Project not writable | Tell user: project is read-only; open it in editable mode, then retry | Yes |
| `errorMessage` contains `"does not support entities"` | Tenant has no Data Service | Tell user: tenant doesn't have Data Service enabled | Yes |
| `errorMessage` contains `"context"` or auth/connection keyword | Can't reach cloud tenant | Retry once. If still fails, tell user to check Orchestrator connection | Yes (after retry) |
| `errorMessage` contains `"no project"` or project resolution failure | `--project-dir` wrong | Retry with explicit absolute path to folder containing `project.json` | Only if retry fails |
| Command hangs >30 s with no output | Helm cold NuGet cache | Retry with `--timeout 180` | No — retry first |
| Returned `entities` array missing the requested entity | Name server-deleted or misspelled | Re-run `list` and use exact `name` field from output | If name not in list |
| Any other `isError: true` response | Internal installer failure | Retry once. If fails again, escalate | Yes (after retry) |

Only if CLI fails and mitigation does not resolve it: tell the user "Entity import failed: `<errorMessage>`. Import entities manually via Studio > Data Service tab > Import Entities, then retry."

Do not attempt to create Data Service XAML without first confirming `installed: true` for the needed entity via the CLI — the generated code will fail validation.

Only entities explicitly imported via Studio are available as CLR types in the generated DLL. An entity present in `EntitiesStore.json` but not imported produces: `Cannot create unknown type '{clr-namespace:...}EntityName'`.

### Entity Lookup Scope

**Only read `EntitiesStore.json` from the current project.** Resolve the path via `project.json` → `entitiesStores[0].serviceDocument`. Do not search for `EntitiesStore.json` in sibling directories, parent folders, or other projects — even if multiple projects are open in Studio. If the entity you need does not appear with `installed: true` in `data-fabric-entities list` output, run `uip rpa data-fabric-entities install --add "<ENTITY_NAME>" --project-dir "<PROJECT_DIR>" --output json`. Only if the CLI fails should you ask the user to import via Studio > Data Service tab > "Import Entities". Do not search other projects' `EntitiesStore.json` files.

## XAML Namespace Declarations

```xml
xmlns:uda="clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
xmlns:udam="clr-namespace:UiPath.DataService.Activities.Models;assembly=UiPath.DataService.Activities.Core"
xmlns:udd="clr-namespace:UiPath.DataService.Definition;assembly=UiPath.DataService.Definition"
xmlns:upr="clr-namespace:UiPath.Platform.ResourceHandling;assembly=UiPath.Platform"
xmlns:local="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"
```

- The `local` namespace **must** include `assembly=DataService.<ProjectName>`. Without the assembly qualifier, the XAML parser cannot locate entity types: `Cannot create unknown type '{clr-namespace:<ProjectName>}EntityName'`.
- The `upr` namespace is required for file activity variables — `DownloadFileFromRecordField.DownloadedFileResource` outputs `upr:ILocalResource`. See [DownloadFileFromRecordField](DownloadFileFromRecordField.md).

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

## When to Use Batch vs Single-Record Activities

For Create, Update, and Delete, two activities exist: a single-record variant (`...EntityRecord`) and a batch variant (`...MultipleEntityRecords`). Choose based on **record count** and **error semantics** — not on convenience.

### Pairs

| Operation | Single | Batch |
|---|---|---|
| Create | [CreateEntityRecord](activities/CreateEntityRecord.md) | [CreateMultipleEntityRecords](activities/CreateMultipleEntityRecords.md) |
| Update | [UpdateEntityRecord](activities/UpdateEntityRecord.md) | [UpdateMultipleEntityRecords](activities/UpdateMultipleEntityRecords.md) |
| Delete | [DeleteEntityRecord](activities/DeleteEntityRecord.md) | [DeleteMultipleEntityRecords](activities/DeleteMultipleEntityRecords.md) |

### Decision Rules

| Use **single** when... | Use **batch** when... |
|---|---|
| Exactly one record per invocation | N records collected at runtime (query result, file rows, list variable) |
| Field values and bindings are known at design time | Records are constructed at runtime; no design-time field UI needed |
| You want Studio's card editor to bind fields visually via `RecordState.SelectedFields` | You want a single HTTP round-trip for the whole set |
| Failure should throw immediately and stop the workflow | You need partial-batch tolerance via `ContinueBatchOnFailure` and per-record errors in `FailedRecords` |

### Anti-patterns

- **`ForEach` calling a single-record activity** — the canonical Data Service performance pitfall. N records → N HTTP requests. Replace with the batch variant for one round-trip.
- **Batch for one known record** — adds collection construction and `Tuple<string, TEntity>` unpacking for no gain. Use the single-record activity.
- **Batch to get "softer" error handling on one record** — wrap the single activity in `TryCatch` or set `ContinueOnError` instead.

### Input contract differs between variants

| Activity | Input shape | How fields are bound |
|---|---|---|
| Single Create / Update | `InputEntityInFieldView` expression + `State` / `RecordState.SelectedFields` | Field GUIDs declared in XAML from `EntitiesStore.json` → `Fields[].Id` |
| Batch Create / Update | `InputRecords` — `ICollection<TEntity>` of fully constructed entities | Field values set on the entity objects at runtime; no `RecordState` |
| Single Delete | `RecordId` — single `Guid` | n/a |
| Batch Delete | `InputRecords` — `ICollection<Guid>` | n/a |

Batch variants do NOT use `RecordState.SelectedFields` — they read entity properties directly off the records in the input collection. For Update batch, each entity object must have its `Id` property set.

### Output shape differs

| Activity | Success output | Failure output |
|---|---|---|
| Single Create / Update | `OutputEntity` (single `TEntity`) | Throws on failure (or sets `ContinueOnError`) |
| Batch Create / Update | `OutputRecords` (`IList<TEntity>`) | `FailedRecords` (`IList<Tuple<string, TEntity>>`) — error message + failed record |
| Single Delete | — | Throws on failure |
| Batch Delete | — | `FailedRecords` (`IList<Guid>`) — IDs that failed |

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
- `EntitiesStore.json` contains all tenant entities, but only explicitly imported ones have CLR types in the generated DLL. If validation returns `Cannot create unknown type '{clr-namespace:...}EntityName'` — run `uip rpa data-fabric-entities install --add "<EntityName>" --project-dir "<PROJECT_DIR>" --output json` to install the missing entity type, then retry validation. Only if the CLI fails should you ask the user to import via Studio > Data Service tab > "Import Entities". Do not attempt to fix this by changing namespaces or assembly references.
- For Create/Update activities, set `IsInRecordView="[False]"` and populate two things:
  1. **`InputEntityInFieldView`** — object-initializer expression (runtime reads this)
  2. **`RecordState.SelectedFields`** — field GUIDs and values (Studio card UI reads this)
  - Do NOT use `InputEntity` — Studio syncs `SelectedFields` → `InputEntityInFieldView` on load but never syncs `SelectedFields` → `InputEntity`, causing desync bugs
- Entity fields are NOT WF4 properties on the activity — they must be set via `InputEntityInFieldView` expression and `RecordState.SelectedFields`, not as `<uda:CreateEntityRecord.FieldName>`
