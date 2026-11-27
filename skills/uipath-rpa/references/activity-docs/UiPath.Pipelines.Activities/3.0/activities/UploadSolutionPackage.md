# Upload Solution Package

`UiPath.Pipelines.Activities.UploadSolutionPackage`

Uploads a solution package zip archive to Orchestrator.

Reads the specified zip file and uploads it via the Solutions API. The activity then polls the package version state until it leaves `Pending` (reaching `Ready`, `Active`, or `Failed`). Transient server errors are retried automatically (up to 3 times via Polly).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `PathToSolutionPackage` | Path to solution package | `InArgument` | `string` | Yes | — | — | Absolute file path to the solution package zip archive. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:UploadSolutionPackage
    Tenant="[tenant]"
    PathToSolutionPackage="[packageZipPath]"
    DisplayName="Upload Solution Package" />
```

## Notes

- Both `Tenant` and `PathToSolutionPackage` are required.
- The file at `PathToSolutionPackage` must be a valid solution package zip archive.
- Throws `SolutionPackageStateException` if the package ends up in `Failed` or `Pending` state after polling.
- Throws `UploadSolutionPackageException` if the upload API call fails.
- Inherits from `BaseSolutionsActivity`.
