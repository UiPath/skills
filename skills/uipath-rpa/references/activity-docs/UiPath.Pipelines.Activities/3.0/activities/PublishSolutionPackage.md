# Publish Solution Package

`UiPath.Pipelines.Activities.PublishSolutionPackage`

Publishes a solution package.

Calls the Solutions API to publish a solution project as a versioned package, then polls the publish status until a terminal state is reached (`Completed` or `Faulted`). Transient server errors are retried automatically (up to 3 times via Polly).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionProjectName` | Solution project name | `InArgument` | `string` | Yes | — | — | Name of the solution project to be published. |
| `SolutionPackageName` | Solution package name | `InArgument` | `string` | Yes | — | — | Name of the published solution package. |
| `SolutionPackageVersion` | Solution package version | `InArgument` | `string` | Yes | — | — | Version of the published solution package. |
| `SolutionPackageDescription` | Solution package description | `InArgument` | `string` | No | — | — | Description for the published solution package. |
| `SolutionRootFolder` | Solution root folder | `InArgument` | `string` | No | — | — | The name given at deployment time for the solution root folder. Administrators may change this during deployment. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:PublishSolutionPackage
    Tenant="[tenant]"
    SolutionProjectName="MySolutionProject"
    SolutionPackageName="MySolution"
    SolutionPackageVersion="1.0.0"
    DisplayName="Publish Solution Package" />
```

## Notes

- `Tenant`, `SolutionProjectName`, `SolutionPackageName`, and `SolutionPackageVersion` are required.
- Throws `PublishSolutionPackageException` if publishing faults or if polling times out with `InProgress` status.
- Inherits from `BaseSolutionsActivity`.
