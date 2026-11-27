# Get Current Job Info

`UiPath.Core.Activities.GetCurrentJobInfo`

Provides runtime job info such as process name and version, workflow name, robot name, and mode of execution.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Get Current Job Info | `OutArgument` | `CurrentJobInfo` | An object containing runtime information about the current job, including process name, process version, workflow name, robot name, and execution mode. |

## XAML Example

```xml
<ui:GetCurrentJobInfo
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Get Current Job Info">
  <ui:GetCurrentJobInfo.Result>
    <OutArgument x:TypeArguments="ui:CurrentJobInfo">[jobInfo]</OutArgument>
  </ui:GetCurrentJobInfo.Result>
</ui:GetCurrentJobInfo>
```

## Notes

- The output `CurrentJobInfo` object exposes properties such as process name, process version, workflow file name, robot name, and the mode of execution (e.g. attended, unattended, debug).
- This activity is useful for logging, branching on execution context, or passing runtime metadata to downstream activities or external systems.
- Coded workflow support is enabled for this activity — it can be used directly in coded automations.
