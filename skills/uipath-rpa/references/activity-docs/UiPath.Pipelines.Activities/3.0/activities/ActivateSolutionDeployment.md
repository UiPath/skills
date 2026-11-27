# Activate Solution Deployment

`UiPath.Pipelines.Activities.ActivateSolutionDeployment`

Activates a solution deployment.

Calls the Solutions API to trigger the activation of an existing deployment, then polls for the activation status until a terminal state is reached (success or failure). Transient server errors are retried automatically (up to 3 times via Polly).

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionDeploymentName` | Solution deployment name | `InArgument` | `string` | Yes | — | — | Name of the solution deployment to be activated. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:ActivateSolutionDeployment
    Tenant="[tenant]"
    SolutionDeploymentName="MyDeployment"
    DisplayName="Activate Solution Deployment" />
```

## Notes

- Both `Tenant` and `SolutionDeploymentName` are required.
- The activity polls the deployment instance status until the activation reaches a terminal state. If the status is `ActivateProgress`, the activity waits and polls again.
- Throws `ActivateSolutionException` on activation failure, timeout, or invalid status transitions.
- Valid terminal success status: `SuccessfulActivate`.
- Inherits from `BaseSolutionsActivity`.
