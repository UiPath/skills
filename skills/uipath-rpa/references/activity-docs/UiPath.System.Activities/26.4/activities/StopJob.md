# Stop Job

`UiPath.Core.Activities.StopJob`

Stops or kills a job on Orchestrator.

**Package:** `UiPath.System.Activities`
**Category:** Jobs

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Job` | Job | InArgument | `OrchestratorJob` | Yes | — | The Orchestrator job to stop. Typically obtained from **Get Jobs**. |
| `Strategy` | Strategy | InArgument | `StopStrategy` | No | — | Controls how the job is stopped: gracefully or forcibly. |
| `FolderPath` | Folder Path | InArgument | `string` | No | — | The Orchestrator folder path to use. Overrides the robot's default folder. |

### Enum Reference

**StopStrategy**

| Value | Description |
|-------|-------------|
| `SoftStop` | Sends a stop signal to the robot. The robot will finish its current activity and then stop gracefully. |
| `Kill` | Forcibly terminates the robot process immediately without waiting for it to finish. |

## XAML Example

```xml
<!-- Soft stop -->
<ui:StopJob
    Job="[jobToStop]"
    Strategy="SoftStop"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />

<!-- Kill -->
<ui:StopJob
    Job="[jobToStop]"
    Strategy="Kill"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Use **Get Jobs** to retrieve an `OrchestratorJob` object to pass to the `Job` property.
- `SoftStop` requests a graceful stop: the target robot will complete its currently executing activity before stopping. The job ends with status **Stopped**.
- `Kill` forces immediate process termination. The job ends with status **Stopped** but the robot may not clean up resources properly. Use only when a graceful stop is not responding.
- This activity does not wait for the job to actually stop — it only submits the stop request to Orchestrator. Poll with **Get Jobs** if you need to confirm the job has reached a terminal state.
