# Run Existing Test Set

`UiPath.Pipelines.Activities.RunExistingTestSet`

Runs an existing test set created in Orchestrator. Requires a UiPath Testing license.

This is a **persistent activity** (annotated with `[PersistentActivity]`). After triggering the test set execution on Orchestrator, the Robot suspends the workflow and resumes automatically when the test jobs complete. On resume, it generates a JUnit XML report and an `UiPathTestReport` object.

Unlike `RunTests`, this activity does not build or upload a package — it targets a test set that already exists in Orchestrator and starts execution immediately.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Tenant` | Tenant | `InArgument` | `OrchestratorTenant` | Yes | — | — | The Orchestrator tenant to connect to. |
| `Folder` | Folder name | `InArgument` | `OrchestratorFolder` | Yes | — | — | Orchestrator folder where the tests shall be run. |
| `TestSetName` | Test set name | `InArgument` | `string` | Yes | — | — | Name of the test set to be run. |
| `AttachRobotLogs` | Attach Robot logs | `InArgument` | `bool` | No | `false` | — | Include test set execution logs in the report. |
| `RetryCount` | Number of retries | `InArgument` | `int` | No | `0` | — | Number of times failed test cases should be re-executed. |

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
<pip:RunExistingTestSet
    Tenant="[tenant]"
    Folder="[folder]"
    TestSetName="MyTestSet"
    ResultFilePath="[resultFilePath]"
    TestSetReport="[testReport]"
    DisplayName="Run Existing Test Set" />
```

## Notes

- `Tenant`, `Folder`, and `TestSetName` are required.
- This is a persistent activity: the Robot can be suspended while waiting for Orchestrator to complete the test jobs.
- `ResultFilePath` is always written, even when tests fail or exceptions occur.
- If `RetryCount > 0`, failed test cases are automatically re-executed up to that many times.
- The test set must already exist in Orchestrator under the specified folder. If it does not exist or the robot lacks permissions, a `GetTestSetInvalidNameOrInsufficientPermissionsException` is thrown.
- Inherits from `BaseTestingActivity` → `BasePersistentActivity`.
