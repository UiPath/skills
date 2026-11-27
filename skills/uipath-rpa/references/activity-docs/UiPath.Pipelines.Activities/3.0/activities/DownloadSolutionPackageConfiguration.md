# Download Solution Package Configuration

`UiPath.Pipelines.Activities.DownloadSolutionPackageConfiguration`

Downloads a solution package configuration file.

Checks the state of the specified solution package version (must be `Active` or `Ready`), then downloads the configuration in the requested format (JSON or YAML) to a temporary file and returns the path.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionPackageName` | Solution package name | `InArgument` | `string` | Yes | — | — | Name of the solution package. |
| `SolutionPackageVersion` | Solution package version | `InArgument` | `string` | No | Latest | — | Version of the solution package. Defaults to latest if not specified. |
| `SolutionPackageConfigurationFormat` | Solution package configuration format | `InArgument` | `ConfigurationFormat` | No | `Json` | — | Format of the downloaded configuration file. Available values: `Json`, `Yaml`. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PathToSolutionPackageConfiguration` | Path to solution package configuration | `string` | Absolute path where the solution package configuration is downloaded (a temp file with extension `.json` or `.yaml`). |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## ConfigurationFormat Enum

| Value | Description |
|-------|-------------|
| `Json` (0) | Configuration file in JSON format. |
| `Yaml` (1) | Configuration file in YAML format. |

## XAML Example

```xml
<pip:DownloadSolutionPackageConfiguration
    Tenant="[tenant]"
    SolutionPackageName="MySolution"
    SolutionPackageVersion="1.0.0"
    SolutionPackageConfigurationFormat="{x:Static pip:ConfigurationFormat.Json}"
    PathToSolutionPackageConfiguration="[configPath]"
    DisplayName="Download Solution Package Configuration" />
```

## Notes

- `Tenant` and `SolutionPackageName` are required.
- `SolutionPackageConfigurationFormat` defaults to `Json`.
- The downloaded file is written to a uniquely-named temporary file in the system temp directory with the appropriate extension.
- Throws `SolutionPackageStateException` if the package version is in `Pending` or `Failed` state.
- Throws `DownloadSolutionPackageConfigurationException` if the download fails.
- Inherits from `BaseSolutionsActivity`.
