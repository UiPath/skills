# Download Package

`UiPath.Pipelines.Activities.DownloadPackage`

Downloads a package from Orchestrator.

The activity resolves the target Orchestrator feed based on the `Folder` and `IsLibrary` arguments (see feed selection logic below), then downloads the specified package version as a `.nupkg` file to the user profile packages directory (`~/packages`).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | The Orchestrator tenant to connect to. Accepts an `OrchestratorTenant` object or a plain tenant name string. |
| `PackageName` | Package name | `InArgument` | `string` | Yes | — | — | Name of the package to be downloaded. |
| `Folder` | Orchestrator folder | `InArgument` | `OrchestratorFolder` | No | — | — | Orchestrator folder. If not provided, the Orchestrator Tenant feed will be used. |
| `PackageVersion` | Package version | `InArgument` | `string` | No | Latest | — | Version of the package to be downloaded. If not provided, the latest version is downloaded. |
| `IsLibrary` | Is library | `InArgument` | `bool` | No | `false` | — | Specifies package type so the package is searched on the proper feed. `false` = process feed, `true` = libraries feed. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PackagePath` | Package path | `string` | Absolute path of the downloaded package file (e.g. `~/packages/PackageName.Version.nupkg`). |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `60000` | Timeout in milliseconds. |

## Feed Selection Logic

- If `IsLibrary = true`: uses the Tenant Libraries feed.
- If `IsLibrary = false` and `Folder` is provided: uses the Folder feed (falls back to Tenant Processes feed if no folder-specific feed exists).
- If `IsLibrary = false` and no `Folder`: uses the Tenant Processes feed.

## XAML Example

```xml
<pip:DownloadPackage
    Tenant="[tenant]"
    PackageName="MyProcess"
    PackageVersion="1.0.0"
    PackagePath="[packagePath]"
    DisplayName="Download Package" />
```

## Notes

- `Tenant` and `PackageName` are required.
- If `PackageVersion` is omitted, the activity automatically fetches the latest available version.
- Downloaded packages are saved to `~/packages/{PackageName}.{PackageVersion}.nupkg`.
- Inherits from `CicdBaseOrchestratorPackageActivity`.
