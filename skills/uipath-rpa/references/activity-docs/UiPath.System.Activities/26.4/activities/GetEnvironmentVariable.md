# Get Environment Variable

`UiPath.Core.Activities.GetEnvironmentVariable`

Gets the contents of the specified environment variable.

**Package:** `UiPath.System.Activities`
**Category:** System.Environment

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Variable | Variable | InArgument | `string` | Yes | — | The name of the environment variable to retrieve. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| VariableValue | Variable Value | OutArgument | `string` | The value of the specified environment variable. Returns an empty string if the variable does not exist. |

## XAML Example

```xml
<ui:GetEnvironmentVariable Variable="PATH">
  <ui:GetEnvironmentVariable.VariableValue>
    <OutArgument x:TypeArguments="x:String">[pathValue]</OutArgument>
  </ui:GetEnvironmentVariable.VariableValue>
</ui:GetEnvironmentVariable>
```

## Notes

- Environment variable names are case-insensitive on Windows but case-sensitive on Linux/macOS.
- Reads from the combined scope of Process, User, and Machine variables in the standard .NET resolution order.
- Use **Set Environment Variable** to create or update a variable, and **Get Environment Folder** to retrieve well-known system folder paths.
