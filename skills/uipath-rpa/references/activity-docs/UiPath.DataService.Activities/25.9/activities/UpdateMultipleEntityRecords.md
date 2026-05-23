# UpdateMultipleEntityRecords

Updates multiple records in a Data Fabric entity in a single batch operation. Category: **DataService.Batch**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `InputRecords` | `InArgument<ICollection<TEntity>>` | Yes | — | Input | Collection of entity objects to update (`[RequiredArgument]`) |
| `OutputRecords` | `OutArgument<IList<TEntity>>` | No | — | Output | Successfully updated records |
| `FailedRecords` | `OutArgument<IList<Tuple<string, TEntity>>>` | No | — | Output | Failed records with error messages |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `ContinueBatchOnFailure` | `InArgument<bool>` | No | `true` | Options | If `true`, continues processing remaining records when one fails |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Studio writes all three properties as explicit literals on every activity:
>
> - **Folder scope** — `ScopeValue="Folder"`, `SolutionEntityKey="<entity-UUID>"`, `SolutionEntityName="<EntityName>"`, plus `x:TypeArguments="udacsdeb:<EntityName>_<UUID-with-dashes-as-underscores>"`. Entity declaration lives at `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]<EntityName>.json`. At runtime, `Entity.<SolutionEntityName>.folderPath` resolves from Orchestrator's `resourceOverwrites` (hydrated at deploy from the solution's resource artefacts) and is injected as `X-UiPath-FolderPath`.
> - **Tenant scope or standalone** — `ScopeValue="Tenant"`, `SolutionEntityKey="{x:Null}"`, `SolutionEntityName="{x:Null}"`, plus `x:TypeArguments="<initial>:<EntityName>"` via the `xmlns:<initial>="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"` namespace. No `X-UiPath-FolderPath` header at runtime.
>
> The Studio Desktop binding contract lives at `<PROJECT_DIR>/.project/PackageBindingsMetadata.json`. Studio Desktop does NOT produce `bindings_v2.json` — that file is a Studio Web / Maestro Flow / Maestro Case artefact. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope) and [overview — Binding source by surface](../overview.md#binding-source-by-surface).

## XAML Example

```xml
<uda:UpdateMultipleEntityRecords
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Update Multiple ENTITY_NAME Records"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    ContinueBatchOnFailure="True"
    InputRecords="[recordsCollection]"
    OutputRecords="[successRecords]"
    FailedRecords="[failedRecords]"
    TimeoutInMs="30000" />
```

## Key Rules

- Each entity object in `InputRecords` must have its `Id` property set to the record GUID being updated
- `FailedRecords` contains `Tuple<string, TEntity>` — `Item1` is the error message, `Item2` is the failed record
- Same batch failure behavior as `CreateMultipleEntityRecords`
