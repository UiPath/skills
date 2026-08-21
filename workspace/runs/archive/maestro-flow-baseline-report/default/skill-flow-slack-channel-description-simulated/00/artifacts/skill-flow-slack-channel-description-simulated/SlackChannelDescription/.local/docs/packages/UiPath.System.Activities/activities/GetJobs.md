# Get Jobs

`UiPath.Core.Activities.GetJobs`

Retrieves a list of Orchestrator jobs according to a custom filter, using the Orchestrator API.

**Package:** `UiPath.System.Activities`
**Category:** Jobs

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Filter` | Filter | InArgument | `string` | No | — | An OData filter expression string applied to the jobs query. Used when `FilterBuilder` is not active. |
| `Skip` | Skip | InArgument | `int` | No | — | The number of jobs to skip for pagination. |
| `Top` | Top | InArgument | `int` | No | — | The maximum number of jobs to return. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FilterBuilder` | Filter Builder | `JobFilterSettings` | — | A structured filter built using the visual Filter Builder widget. Supports filtering by State, JobPriority, Key, ReleaseName, CreationTime, StartTime, and EndTime. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `IEnumerable<OrchestratorJob>` | The list of jobs matching the specified filters. |

## Valid Configurations

- Either `Filter` (OData string expression) or `FilterBuilder` (visual widget) may be used to apply filter criteria. The designer provides a menu toggle to switch between the two modes.
- `FilterBuilder` supports the following criteria fields: **State**, **JobPriority**, **Key**, **ReleaseName**, **CreationTime**, **StartTime**, **EndTime**.
- `Skip` and `Top` provide pagination support for large result sets.

### Enum Reference

**JobFilterField** (available in FilterBuilder)

| Criteria | Supported Operators |
|----------|---------------------|
| `State` | Equals, NotEquals |
| `JobPriority` | Equals, NotEquals |
| `Key` | Equals (GUID) |
| `ReleaseName` | Equals, Contains, StartsWith, EndsWith |
| `CreationTime` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |
| `StartTime` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |
| `EndTime` | OlderThan, NewerThan, OlderThanOrEqual, NewerThanOrEqual |

**JobState** (values available in FilterBuilder State criteria)

| Value | Description |
|-------|-------------|
| `Pending` | Job is queued but not yet started. |
| `Running` | Job is currently executing. |
| `Stopping` | Job has been requested to stop gracefully. |
| `Terminating` | Job is being forcibly terminated. |
| `Faulted` | Job ended with an error. |
| `Successful` | Job completed successfully. |
| `Stopped` | Job was stopped before completion. |
| `Suspended` | Job is suspended. |
| `Resumed` | Job has been resumed from suspension. |

## XAML Example

```xml
<ui:GetJobs
    Top="[20]"
    Result="[jobs]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- `Result` is a collection of `OrchestratorJob` objects. Each object exposes properties such as `Id`, `Key`, `State`, `ReleaseName`, `StartTime`, `EndTime`, and `Info`.
- `FolderPath` is an advanced/hidden property that overrides the Orchestrator folder context for the query.
- Use `Top` to limit result size. Without it, the API may return a large number of records.
