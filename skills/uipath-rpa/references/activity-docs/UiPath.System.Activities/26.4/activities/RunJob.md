# Run Job

`UiPath.Activities.System.Jobs.RunJob`

Initiates any type of job (Agent, Agentic process, RPA workflows, API workflow, Testing process, etc.) via Orchestrator to be picked up by any available robots. It allows for flexible configuration of the execution mode (Do not wait, Wait for job completion or Suspend execution until job completion). It returns output arguments unless started in the Do not wait mode.

**Package:** `UiPath.System.Activities`
**Category:** Run

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name | InArgument | `string` | Yes | — | The name of the Orchestrator process to start. Supports auto-complete from available processes in the configured folder. |
| `Machine` | Machine | InArgument | `string` | No | — | The machine on which the job will execute. If not specified, any available machine is used. |
| `Account` | Account | InArgument | `string` | No | — | The account used to execute the job. If not specified, the default account associated with the machine is used. |
| `TimeoutMS` | Timeout MS | InArgument | `int` | No | `600000` (10 min) | Maximum time in milliseconds to wait for the job to complete. Only applicable when `ExecutionMode` is `Busy` (Wait for job completion). Read-only for other modes. |
| `ContinueOnError` | Continue On Error | InArgument | `bool` | No | `false` | When `True`, execution continues even if this activity encounters an error. Read-only when `ExecutionMode` is `None`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExecutionMode` | Execution mode | `JobExecutionMode` | `JobExecutionMode.Busy` | Determines how the initiated job is processed. See Valid Configurations below. |
| `ContinueWhenFaulted` | Continue when job fails | `bool` | `false` (i.e., fail when faulted) | When `True`, a faulted job is ignored and execution continues. When `False`, a faulted job causes this activity to throw an error. Read-only when `ExecutionMode` is `None`. |
| `FolderPath` | Folder Path | `string` | — | The Orchestrator folder containing the process. Leave empty to use the folder of the current process. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Job` | Job data | OutArgument | `OrchestratorJob` | An object containing information about the initiated job (e.g., Job ID, status, output arguments). Not populated when `ExecutionMode` is `None`. |

## Valid Configurations

The behavior and available properties depend on the `ExecutionMode` value:

| `ExecutionMode` | Behavior | `TimeoutMS` | `ContinueOnError` | `ContinueWhenFaulted` | Output |
|---|---|---|---|---|---|
| `None` (Do not wait) | Starts the job and returns immediately without waiting. | Read-only | Read-only | Read-only | `Job` is populated with basic job info; no output arguments. |
| `Busy` (Wait for job completion) | Starts the job and blocks the current robot until the job completes or times out. | Editable | Editable | Editable | `Job` is fully populated including output arguments. |
| `Suspend` (Suspend until job completion) | Starts the job and suspends the current workflow (persistence required). Resumes when the job completes. | Read-only | Editable | Editable | `Job` is fully populated including output arguments on resume. |

### Enum Reference

**`JobExecutionMode`**

| Value | Description |
|-------|-------------|
| `None` | Do not wait — fire and forget. |
| `Busy` | Wait for job completion by blocking the robot thread. |
| `Suspend` | Suspend the workflow until the job completes (requires persistence infrastructure). |

## XAML Example

```xml
<!-- Wait for job completion -->
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    ProcessName="[&quot;InvoiceProcessor&quot;]"
    ExecutionMode="Busy"
    TimeoutMS="[600000]"
    ContinueWhenFaulted="False"
    Job="{x:Reference jobData}" />
```

```xml
<!-- Fire and forget -->
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    ProcessName="[&quot;BackgroundReporter&quot;]"
    ExecutionMode="None" />
```

## Notes

- Requires an active Orchestrator connection. The process must be published and available in the specified (or current) Orchestrator folder.
- **Suspend mode** requires a persistence-enabled environment. The calling workflow is suspended and resumed by the Orchestrator persistence infrastructure once the triggered job finishes. This allows the calling robot to be freed while waiting.
- Input and output arguments for the triggered process are configured via the dynamic **Arguments** / **Input** / **Output** properties in the designer. The designer auto-imports the argument schema from the selected process when `ProcessName` is set to a literal string.
- The input can be provided in three modes selectable via the designer menu: **Data Mapper** (structured schema), **Object** (single typed variable), or **Dictionary** (key-value pairs of arguments).
- `ContinueWhenFaulted` is the inverse of the underlying `FailWhenFaulted` property: setting `ContinueWhenFaulted = True` sets `FailWhenFaulted = False`.
- `Machine` and `Account` support auto-complete from Orchestrator-connected data sources. Leave empty to allow Orchestrator to assign automatically.
- `FolderPath` supports Orchestrator modern folder paths (e.g., `Finance/Invoices`).
