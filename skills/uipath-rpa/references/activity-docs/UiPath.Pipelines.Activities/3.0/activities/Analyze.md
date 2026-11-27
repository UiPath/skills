# Analyze

`UiPath.Pipelines.Activities.Analyze`

Analyzes a project against workflow analysis rules.

Delegates to the `PipelinesWrapper` child process which calls `uipcli` internally. When an `AnalyzePolicy` is provided, the activity retrieves the governance policy data from AutomationOps and passes it to the analyzer. The analysis result is returned as a `DataTable` with columns: `Level`, `ErrorCode`, `RuleName`, `FilePath`, `Recommendation`.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `RepositoryPath` | Repository path | `InArgument` | `string` | Yes | — | — | Absolute path to the cloned repository. |
| `ProjectPath` | Project path | `InArgument` | `string` | No | `project.json` | — | Relative path to the `project.json` file. Defaults to `project.json` in the repository root. |
| `AnalyzePolicy` | Policy | `InArgument` | `AnalyzePolicy` | No | — | — | The governance policy containing the workflow analyzer rules to check. Accepts a string policy identifier (implicit conversion). |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `AnalysisResult` | Analysis result | `DataTable` | Result of the analysis. Columns: `Level`, `ErrorCode`, `RuleName`, `FilePath`, `Recommendation`. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |

## XAML Example

```xml
<pip:Analyze
    RepositoryPath="[repoPath]"
    ProjectPath="src/project.json"
    AnalysisResult="[analysisResult]"
    DisplayName="Analyze" />
```

## Notes

- `RepositoryPath` is required; `ProjectPath` and `AnalyzePolicy` are optional.
- If `AnalyzePolicy` is not provided, default workflow analysis rules apply.
- If `AnalyzePolicy` is provided, the activity contacts the AutomationOps service to download the governance policy rules file before running the analyzer.
- When analysis finds rule violations, the `AnalysisResult` table is still populated but an `AnalyzeErrorException` is thrown unless `ContinueOnError` is `true`.
- The `Analyze` activity does **not** require an Orchestrator `Tenant` argument. It inherits from `ContinuableAsyncCodeActivity`.
