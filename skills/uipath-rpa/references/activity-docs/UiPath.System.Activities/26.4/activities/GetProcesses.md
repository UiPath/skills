# Get Processes

`UiPath.Core.Activities.GetProcesses`

Gets the list of all running processes.

**Package:** `UiPath.System.Activities`
**Category:** System.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ContinueOnError | Continue On Error | InArgument | `bool` | No | — | When `True`, execution continues to the next activity even if this activity throws an error. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Processes | Processes | OutArgument | `Collection<Process>` | The collection of `System.Diagnostics.Process` objects representing every currently running process. |

## XAML Example

```xml
<ui:GetProcesses>
  <ui:GetProcesses.Processes>
    <OutArgument x:TypeArguments="scg:Collection(sd:Process)">[processList]</OutArgument>
  </ui:GetProcesses.Processes>
</ui:GetProcesses>
```

## Notes

- Returns all processes visible to the current user account. Processes owned by other users may be excluded depending on OS permissions.
- Each `Process` object in the output collection exposes properties such as `ProcessName`, `Id`, `MainWindowTitle`, `StartTime`, etc.
- Use **Kill Process** to terminate a specific process from the returned collection.
