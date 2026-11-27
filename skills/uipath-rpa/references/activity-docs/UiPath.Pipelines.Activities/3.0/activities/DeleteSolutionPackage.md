# Delete Solution Package

`UiPath.Pipelines.Activities.DeleteSolutionPackage`

Deletes a solution package.

Calls the Solutions API to delete the specified version of a solution package. Transient server errors are retried automatically (up to 3 times via Polly).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionPackageName` | Solution package name | `InArgument` | `string` | Yes | — | — | Name of the solution package to be deleted. |
| `SolutionPackageVersion` | Solution package version | `InArgument` | `string` | Yes | — | — | Version of the solution package to be deleted. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:DeleteSolutionPackage
    Tenant="[tenant]"
    SolutionPackageName="MySolution"
    SolutionPackageVersion="1.0.0"
    DisplayName="Delete Solution Package" />
```

## Notes

- `Tenant`, `SolutionPackageName`, and `SolutionPackageVersion` are all required.
- Throws `DeleteSolutionPackageException` if the deletion fails.
- Inherits from `BaseSolutionsActivity`.
