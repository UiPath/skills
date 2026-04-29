# Start Job

`UiPath.Core.Activities.StartJob`

Initiates a new job via Orchestrator to be picked up by any available robots. It immediately continues the execution without waiting for the job to finish. It does not return output arguments.

**Package:** `UiPath.System.Activities`
**Category:** Jobs

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name | InArgument | `string` | Yes | — | The name of the process (release) to start in Orchestrator. |
| `JobPriority` | Job Priority | InArgument | `StartProcessDtoJobPriority` | No | Normal | The priority of the started job in the Orchestrator queue. |
| `NumberOfRobots` | Number Of Robots | InArgument | `int` | No | — | The number of robot instances to allocate for the job. |
| `ModernFolder` | Modern Folder | InArgument | `bool` | No | true | Indicates whether the target process is in a modern (non-classic) Orchestrator folder. |
| `ResumeOnSameContext` | Resume On Same Context | InArgument | `bool` | No | false | When true, the job will resume on the same robot/machine context if suspended. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Arguments` | Arguments | `Dictionary<string, Argument>` | `{}` | The inline collection of input arguments to pass to the started process. Keys must match the process's declared input argument names. |
| `ArgumentsVariable` | Arguments Variable | `InArgument<Dictionary<string, object>>` | null | A variable dictionary of input arguments. Alternative to the inline `Arguments` dictionary. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `JobId` | Job Id | OutArgument | `string` | The numeric identifier of the started job in Orchestrator. |
| `Key` | Key | OutArgument | `string` | The GUID key of the started job in Orchestrator. |

## Valid Configurations

- `Arguments` and `ArgumentsVariable` are two ways to supply input arguments. Use `Arguments` for inline design-time mapping and `ArgumentsVariable` to pass a dictionary variable at runtime.
- `NumberOfRobots` controls the number of concurrent robot instances used to run the job.

### Enum Reference

**StartProcessDtoJobPriority**

| Value | Description |
|-------|-------------|
| `Low` | The job is given lower scheduling priority than normal. |
| `Normal` | Default scheduling priority. |
| `High` | The job is given higher scheduling priority than normal. |

## XAML Example

```xml
<ui:StartJob
    ProcessName="&quot;InvoiceProcessing&quot;"
    JobPriority="Normal"
    JobId="[startedJobId]"
    Key="[startedJobKey]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- This activity is **fire-and-forget**: it submits the job to Orchestrator and immediately continues without waiting for the job to complete. Use the **Get Jobs** activity to poll for the job's completion state if needed.
- The started process does not return output arguments to the calling workflow.
- `ProcessName` must exactly match the release name as configured in Orchestrator.
- `FolderPath` is an advanced/hidden property (not shown in designer) that targets the process in a specific Orchestrator folder.
