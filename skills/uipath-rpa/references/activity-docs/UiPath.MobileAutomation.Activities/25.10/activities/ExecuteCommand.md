# ExecuteCommandDisplayNameDisplayName

`UiPath.MobileAutomation.Activities.ExecuteCommand`

Executes Appium mobile commands.
WARNING: Please check the available commands for your Appium version.

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Command` | Execute Command | InArgument | `string` | Yes | | Executes Appium mobile commands. WARNING: Please check the available commands for your Appium version. |
| `Parameters` | Parameters | Property | `InArgument<Dictionary<string,object>>` | | | Arguments of the command |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Output` | Output | `object` | The result of the executed command |

## XAML Example

```xml
<ma:ExecuteCommand DisplayName="Execute Command"
                   Command="[&quot;mobile: shell&quot;]"
                   Output="[commandOutput]">
  <ma:ExecuteCommand.Parameters>
    <InArgument x:TypeArguments="scg:Dictionary(x:String, x:Object)">[New Dictionary(Of String, Object) From {{"command", "echo"}, {"args", New String() {"Hello"}}}]</InArgument>
  </ma:ExecuteCommand.Parameters>
</ma:ExecuteCommand>
```

## Notes

- This activity allows execution of any Appium mobile command directly
- The available commands depend on your Appium server version
- Use with caution as incorrect commands can cause unexpected behavior
- The Parameters property accepts a dictionary of command arguments
- Refer to the Appium documentation for available commands: http://appium.io/docs/
- The Output returns the result of the command as an object, which may need to be cast to the appropriate type
