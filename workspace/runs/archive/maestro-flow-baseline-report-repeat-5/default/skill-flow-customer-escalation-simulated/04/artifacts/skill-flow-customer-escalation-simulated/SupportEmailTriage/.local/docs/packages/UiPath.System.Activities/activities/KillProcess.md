# Kill Process

`UiPath.Core.Activities.KillProcess`

Terminates a specified process.

**Package:** `UiPath.System.Activities`
**Category:** System.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Process | Process | InArgument | `Process` | No | — | A `System.Diagnostics.Process` object identifying the process to kill. Use this or `ProcessName`, not both. |
| ProcessName | Process Name | InArgument | `string` | No | — | The name of the process to kill (without the `.exe` extension). Kills all matching processes. Use this or `Process`, not both. |
| AppliesTo | Applies To | InArgument | `KillProcessApplyOn` | No | `KillProcessApplyOn.All` | Filters which instances of a named process to kill (All, current user, current session, or current desktop). Windows projects support all modes. |
| ContinueOnError | Continue On Error | InArgument | `bool` | No | — | When `True`, execution continues to the next activity even if this activity throws an error. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## Valid Configurations

Exactly one of `Process` or `ProcessName` must be provided (they belong to separate overload groups).

| Scenario | Use |
|----------|-----|
| Have a `Process` object from Get Processes | `Process` argument |
| Know only the process name | `ProcessName` argument |

## Enum Reference

### KillProcessApplyOn

| Value | Description |
|-------|-------------|
| `All` | Kill all processes matching the name, regardless of owner |
| `User` | Kill only processes owned by the current user (Windows only) |
| `Session` | Kill only processes in the current Windows session |
| `Desktop` | Kill only processes on the current Windows desktop |

## XAML Example

```xml
<!-- Kill by name -->
<ui:KillProcess ProcessName="notepad" AppliesTo="All" />

<!-- Kill a specific process object -->
<ui:KillProcess>
  <ui:KillProcess.Process>
    <InArgument x:TypeArguments="sd:Process">[myProcess]</InArgument>
  </ui:KillProcess.Process>
</ui:KillProcess>
```

## Notes

- In Windows projects all `AppliesTo` filtering modes are available. In cross-platform projects only `All` is supported.
- Killing a process by name terminates every running instance that matches; supply a `Process` object (from Get Processes) to target a single instance.
- A `ProcessName` match is case-insensitive and should not include the `.exe` suffix.
