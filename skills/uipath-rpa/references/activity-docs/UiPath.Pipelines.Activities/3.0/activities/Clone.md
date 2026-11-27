# Clone

`UiPath.Pipelines.Activities.Clone`

Clones a git repository.

Delegates to the `PipelinesWrapper` child process which calls `uipcli` internally. If no `AccessToken` is supplied, the activity automatically retrieves a robot token from the AutomationOps service. If no `DestinationPath` is specified, the repository is cloned into a uniquely-named subdirectory of the system temp folder. A configurable `TimeoutMS` limits how long the clone may run.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `RepoUrl` | Repository URL | `InArgument` | `string` | Yes | — | — | The URL of the git repository. |
| `CommitSha` | Commit SHA | `InArgument` | `string` | No | — | — | The commit identifier. If empty, will automatically be retrieved from the pipeline run context. |
| `AccessToken` | Access token | `InArgument` | `string` | No | Robot token | — | Security token for accessing the repository. If empty, the robot token is used automatically. **Marked as secret — value is not logged.** |
| `DestinationPath` | Destination path | `InArgument` | `string` | No | System temp folder | — | Directory path where the repository will be cloned. A new directory is created in the system temp folder if not specified. |
| `SkipCertificateCheck` | Skip certificate check | `InArgument` | `bool` | No | `false` | — | If enabled, skips SSL certificate checks when interacting with the version control system. Use with caution — this bypasses an important security feature. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `RepositoryPath` | Repository path | `string` | Absolute path to the cloned repository. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |
| `TimeoutMS` | Timeout (milliseconds) | `InArgument` | `int` | `60000` | Timeout in milliseconds. |

## XAML Example

```xml
<pip:Clone
    RepoUrl="https://github.com/org/repo.git"
    CommitSha="[commitSha]"
    RepositoryPath="[repoPath]"
    DisplayName="Clone" />
```

## Notes

- `RepoUrl` is the only required property.
- `AccessToken` is annotated with `[SecretValue]`, so its value is suppressed in diagnostic logs.
- If `AccessToken` is omitted, the activity calls the AutomationOps service (`IAutomationOpsClient.GetAccessTokenAsync`) to obtain a robot-scoped token automatically.
- When `SkipCertificateCheck` is `true`, a warning is written to the robot log before cloning proceeds.
- The clone operation runs against the `TimeoutMS` deadline; a `TimeoutException` is thrown if exceeded.
- Inherits from `CicdBaseActivity` — no Orchestrator `Tenant` argument required.
