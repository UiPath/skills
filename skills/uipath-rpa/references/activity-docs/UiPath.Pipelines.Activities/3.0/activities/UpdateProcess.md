# Update Process

`UiPath.Pipelines.Activities.UpdateProcess`

Updates a process in Orchestrator to a new package version.

The activity looks up the named process in the specified Orchestrator folder, optionally validates that it is backed by the expected package name, resolves the target version (defaulting to the latest available), and then updates the process version via the Orchestrator API.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | The Orchestrator tenant to connect to. |
| `Folder` | Folder name | `InArgument` | `OrchestratorFolder` | Yes | — | — | Orchestrator folder containing the process. For sub-folders use the full path (e.g. `Parent/Child`). |
| `ProcessName` | Process name | `InArgument` | `string` | Yes | — | — | The name of the process to be updated. |
| `PackageName` | Package name | `InArgument` | `string` | No | — | — | The package name behind the process. If provided and it does not match, the activity fails. If not provided, this check is ignored. |
| `PackageVersion` | Package version | `InArgument` | `string` | No | Latest | — | The version of the package to update the process to. If not provided, defaults to the latest version. Fails if the process already uses this version. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `60000` | Timeout in milliseconds. |

## XAML Example

```xml
<pip:UpdateProcess
    Tenant="[tenant]"
    Folder="[folder]"
    ProcessName="MyProcess"
    PackageVersion="[newVersion]"
    DisplayName="Update Process" />
```

## Notes

- `Tenant`, `Folder`, and `ProcessName` are required.
- If `PackageName` is supplied and does not match the process's backing package key, a `DifferentPackageNameException` is thrown.
- If the resolved `PackageVersion` is the same as the version the process already uses, a `SameVersionUpdateException` is thrown.
- Inherits from `CicdBaseOrchestratorPackageActivity`.
