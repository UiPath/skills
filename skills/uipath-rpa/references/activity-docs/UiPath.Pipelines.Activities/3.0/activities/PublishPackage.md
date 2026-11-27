# Publish Package

`UiPath.Pipelines.Activities.PublishPackage`

Publishes a package to Orchestrator.

The activity inspects the `.nupkg` file to determine its package type (Process, Tests, Library, Template, or Generic), then selects the appropriate Orchestrator feed and uploads the package. Process and Tests packages go to the process feed; Library, Template, and Generic packages go to the library feed.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | The Orchestrator tenant to connect to. |
| `PackagePath` | Package path | `InArgument` | `string` | Yes | — | — | Absolute file path of the package to publish. |
| `Folder` | Folder name | `InArgument` | `OrchestratorFolder` | No | — | — | Orchestrator folder. If not provided, the Orchestrator Tenant feed will be used. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `60000` | Timeout in milliseconds. |

## Feed Selection Logic

The package type is auto-detected from the `.nupkg` file:
- `Library`, `Template`, `Generic` → uploaded to the Libraries feed.
- `Process`, `Tests` → uploaded to the Processes feed.

If `Folder` is provided, the folder's own feed is used (falling back to the Tenant Processes feed). If `Folder` is omitted, the Tenant-level feed is used.

## XAML Example

```xml
<pip:PublishPackage
    Tenant="[tenant]"
    PackagePath="[packagePath]"
    DisplayName="Publish Package" />
```

## Notes

- Both `Tenant` and `PackagePath` are required.
- The activity has no output arguments — it fails with an exception if the upload fails.
- Inherits from `CicdBaseOrchestratorPackageActivity`.
