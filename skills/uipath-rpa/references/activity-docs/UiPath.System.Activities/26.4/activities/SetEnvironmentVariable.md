# Set Environment Variable

`UiPath.Core.Activities.SetEnvironmentVariable`

Sets the value of an environment variable.

**Package:** `UiPath.System.Activities`
**Category:** System.Environment

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Name | Name | InArgument | `string` | Yes | — | The name of the environment variable to set. |
| Value | Value | InArgument | `string` | Yes | — | The value to assign to the environment variable. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:SetEnvironmentVariable Name="MY_VAR" Value="HelloWorld" />
```

## Notes

- Changes to Process-scoped variables are visible only within the current process and its children.
- Setting a User or Machine variable requires the appropriate OS-level permissions; modifying Machine variables typically requires elevation.
- To delete an environment variable, set its value to an empty string or `Nothing`.
