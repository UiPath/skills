# Download Solution Package

`UiPath.Pipelines.Activities.DownloadSolutionPackage`

Downloads a solution package.

Checks the state of the specified solution package version (must be `Active` or `Ready`), then downloads the package zip archive via the Solutions API and returns the local file path.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionPackageName` | Solution package name | `InArgument` | `string` | Yes | — | — | Name of the solution package to be downloaded. |
| `SolutionPackageVersion` | Solution package version | `InArgument` | `string` | No | Latest | — | Version of the solution package to be downloaded. Defaults to latest if not specified. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PathToSolutionPackage` | Path to solution package | `string` | Folder path where the solution package is downloaded. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:DownloadSolutionPackage
    Tenant="[tenant]"
    SolutionPackageName="MySolution"
    SolutionPackageVersion="1.0.0"
    PathToSolutionPackage="[downloadPath]"
    DisplayName="Download Solution Package" />
```

## Notes

- `Tenant` and `SolutionPackageName` are required.
- Throws `SolutionPackageStateException` if the package version is in `Pending` or `Failed` state.
- Inherits from `BaseSolutionsActivity`.
