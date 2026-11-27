# Run Tests

`UiPath.Pipelines.Activities.RunTests`

Builds, publishes, and runs a test project against Orchestrator. Requires a UiPath Testing license.

This is a **persistent activity** (annotated with `[PersistentActivity]`). After triggering the test set execution on Orchestrator, the Robot suspends the workflow and resumes automatically when the test jobs complete. On resume, it generates a JUnit XML report and an `UiPathTestReport` object.

Internally, the activity:
1. Validates and builds (packs) the test project using the `PipelinesWrapper` child process.
2. Uploads the package to the specified Orchestrator folder.
3. Creates a transient test set named `CI_{timestamp}_{packageName}_{version}`.
4. Starts execution and suspends until jobs complete.
5. On resume, writes the JUnit XML report file and the `UiPathTestReport` output.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | The Orchestrator tenant to connect to. |
| `Folder` | Folder name | `InArgument` | `OrchestratorFolder` | Yes | — | — | Orchestrator folder where the tests shall be run. |
| `RepositoryPath` | Repository path | `InArgument` | `string` | Yes | — | — | Absolute path to the repository. |
| `ProjectPath` | Project path | `InArgument` | `string` | No | `project.json` | — | Relative path to the `project.json` file. Defaults to `project.json` in the repository root. |
| `Author` | Author | `InArgument` | `string` | No | Current user | — | Author to be set on the package. |
| `Version` | Version | `InArgument` | `string` | No | `major.minor.timestamp` | — | Version of the package. Defaults to `major.minor.timestamp` where major and minor are from the project version. |
| `SkipValidate` | Skip validation | `InArgument` | `bool` | No | `false` | — | Skips project validation. |
| `SeparateRuntimeDependencies` | Separate runtime dependencies | `InArgument` | `bool` | No | `false` | — | Enables the output split to runtime and design libraries. |
| `AttachRobotLogs` | Attach Robot logs | `InArgument` | `bool` | No | `false` | — | Include test set execution logs in the report. |
| `RetryCount` | Number of retries | `InArgument` | `int` | No | `0` | — | Number of times failed test cases should be re-executed. |
| `RepositoryType` | Repository type | `InArgument` | `string` | No | — | — | The used source control type (e.g. `git`, `svn`, `uip`). |
| `RepositoryUrl` | Repository URL | `InArgument` | `string` | No | — | — | Remote repository URL of the `project.json` file. |
| `RepositoryBranch` | Repository branch | `InArgument` | `string` | No | — | — | Source branch for the package. |
| `RepositoryCommit` | Repository commit | `InArgument` | `string` | No | — | — | Commit ID (the commit SHA for git repositories). |
| `ReleaseNotes` | Release notes | `InArgument` | `string` | No | — | — | Release notes for the package. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ResultFilePath` | Results file path | `string` | Absolute path to the test results in JUnit XML format. Always returned, even if tests fail or `ContinueOnError` is set. |
| `TestSetReport` | Test set report | `UiPathTestReport` | Returns the test set report as an object. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |

## XAML Example

```xml
<pip:RunTests
    Tenant="[tenant]"
    Folder="[folder]"
    RepositoryPath="[repoPath]"
    ProjectPath="tests/project.json"
    ResultFilePath="[resultFilePath]"
    TestSetReport="[testReport]"
    DisplayName="Run Tests" />
```

## Notes

- `Tenant`, `Folder`, and `RepositoryPath` are required.
- This is a persistent activity: the Robot can be suspended while waiting for Orchestrator to complete the test jobs, which may take arbitrarily long. This allows the Robot license to be freed during the wait.
- `ResultFilePath` is always written, even when tests fail or exceptions occur.
- If `RetryCount > 0`, failed test cases are automatically re-executed up to that many times.
- The version format must be `major.minor` or `major.minor.patch` using numeric tokens only. The activity appends a timestamp to create the final version (`major.minor.timestamp`).
- Inherits from `BaseTestingActivity` → `BasePersistentActivity`.
