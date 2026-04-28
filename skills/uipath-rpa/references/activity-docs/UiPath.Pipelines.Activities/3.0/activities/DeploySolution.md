# Deploy Solution

`UiPath.Pipelines.Activities.DeploySolution`

Deploys a solution.

Calls the Solutions API to install a solution package under a named deployment, using the provided configuration file. It then polls the pipeline deployment status until a terminal state is reached. Transient server errors are retried automatically (up to 3 times via Polly).

The activity reads the configuration file from `PathToSolutionPackageConfiguration`, auto-detects whether it is JSON or YAML, and passes it to the API as the deployment configuration.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | Name of the tenant where the solution operation is executed. |
| `SolutionDeploymentName` | Deployment name | `InArgument` | `string` | Yes | — | — | Name of the solution deployment. |
| `SolutionPackageName` | Solution package name | `InArgument` | `string` | Yes | — | — | Name of the solution package to be deployed. |
| `SolutionPackageVersion` | Solution package version | `InArgument` | `string` | Yes | — | — | Version of the solution package to be deployed. |
| `SolutionRootFolderName` | Solution root folder name | `InArgument` | `string` | Yes | — | — | Name of the solution root folder. |
| `PathToSolutionPackageConfiguration` | Path to solution package configuration | `InArgument` | `string` | Yes | — | — | Path to the solution package configuration file (JSON or YAML) used for deployment. |
| `DestinationOrchestratorFolder` | Destination folder | `InArgument` | `OrchestratorFolder` | No | — | — | Orchestrator folder that will be used as parent for the solution root folder. If empty, the solution is deployed as a new root folder under the tenant. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `120000` | Timeout in milliseconds (default 2 minutes). |

## XAML Example

```xml
<pip:DeploySolution
    Tenant="[tenant]"
    SolutionDeploymentName="MyDeployment"
    SolutionPackageName="MySolution"
    SolutionPackageVersion="1.0.0"
    SolutionRootFolderName="SolutionRoot"
    PathToSolutionPackageConfiguration="[configFilePath]"
    DisplayName="Deploy Solution" />
```

## Notes

- `Tenant`, `SolutionDeploymentName`, `SolutionPackageName`, `SolutionPackageVersion`, `SolutionRootFolderName`, and `PathToSolutionPackageConfiguration` are all required.
- The configuration file format (JSON or YAML) is auto-detected from the file content.
- The activity polls through validation and deployment phases. Polling intervals are controlled by `SolutionsActivitiesSettings.PollingDelay`.
- Throws `DeploySolutionException` on validation failure, conflict-fixing errors, deployment schedule errors, or deployment failure.
- Inherits from `BaseSolutionsActivity`. Uses the `SolutionsClientWrapper` (not the plain `SolutionsClient`) to support the pipeline deployment flow.
