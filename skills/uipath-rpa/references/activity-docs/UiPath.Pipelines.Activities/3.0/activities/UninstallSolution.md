# Uninstall Solution

`UiPath.Pipelines.Activities.UninstallSolution`

Uninstalls a deployed solution.

Calls the Solutions API to trigger uninstallation of the specified deployment, then polls the deployment instance status until a terminal state is reached (`SuccessfulUninstall` or `FailedUninstall`). Transient server errors are retried automatically (up to 3 times via Polly).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionDeploymentName` | Solution deployment name | `InArgument` | `string` | Yes | — | — | Name of the solution deployment to be uninstalled. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:UninstallSolution
    Tenant="[tenant]"
    SolutionDeploymentName="MyDeployment"
    DisplayName="Uninstall Solution" />
```

## Notes

- Both `Tenant` and `SolutionDeploymentName` are required.
- The activity polls the deployment instance status until the uninstallation reaches a terminal state.
- Throws `UninstallSolutionException` on failure, timeout, or invalid status (e.g. if the deployment is in an install or activate state).
- Valid terminal success status: `SuccessfulUninstall`.
- Inherits from `BaseSolutionsActivity`.
