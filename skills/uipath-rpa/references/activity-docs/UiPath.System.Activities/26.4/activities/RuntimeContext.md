# Manual Trigger

`UiPath.Core.Activities.ManualTrigger`

Contains job info such as Process name, Workflow name, User Name, User Email and Timestamp.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Get Current Job Info | `OutArgument` | `CurrentJobInfo` | An object containing runtime information about the current job, including process name, process version, workflow name, robot name, folder name, user email, and execution mode. |

## XAML Example

```xml
<ui:ManualTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Manual Trigger"
    Result="{x:Reference jobInfo}" />
```

## Notes

- **Manual Trigger** is a scope/container activity. Place the automation logic to execute inside its body.
- The trigger fires when a user manually starts the associated process from Orchestrator or the UiPath Assistant.
- `ManualTrigger` inherits from `GetCurrentJobInfo` — the `Result` output is identical to the one produced by the **Get Current Job Info** activity.
- No scheduling or queue configuration is required.
