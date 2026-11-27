# Message Box

`UiPath.Core.Activities.MessageBox`

Displays a message box with a specified text and buttons.

**Package:** `UiPath.System.Activities`
**Category:** System.Dialog
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Text | Text | InArgument | `object` | Yes | — | The message to display in the body of the dialog. |
| Caption | Caption | InArgument | `string` | No | — | The title bar text of the message box dialog. |
| Buttons | Buttons | InArgument | `ButtonOptions` | No | `ButtonOptions.Ok` | Specifies which buttons to display. Configurable as a project setting. |
| AutoCloseAfter | Automatically Close After | InArgument | `TimeSpan` | No | — | If set, the dialog closes automatically after this duration without user input. |
| TopMost | TopMost | InArgument | `bool` | No | `true` | If set, always brings the message box to the foreground. Configurable as a project setting. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| ChosenButton | Chosen Button | OutArgument | `string` | The label of the button pressed by the user. Possible values: `Ok`, `Yes`, `No`, `Cancel`. |

## Valid Configurations

`Buttons` controls which buttons are rendered. Only the corresponding `ChosenButton` values are returned.

| ButtonOptions value | Possible ChosenButton values |
|--------------------|------------------------------|
| `Ok` | `Ok` |
| `OkCancel` | `Ok`, `Cancel` |
| `YesNo` | `Yes`, `No` |
| `YesNoCancel` | `Yes`, `No`, `Cancel` |

## Enum Reference

### ButtonOptions

| Value | Buttons shown |
|-------|--------------|
| `Ok` | OK |
| `OkCancel` | OK, Cancel |
| `YesNo` | Yes, No |
| `YesNoCancel` | Yes, No, Cancel |

## XAML Example

```xml
<ui:MessageBox Caption="Confirm" Text="Do you want to continue?" Buttons="YesNo">
  <ui:MessageBox.ChosenButton>
    <OutArgument x:TypeArguments="x:String">[chosenButton]</OutArgument>
  </ui:MessageBox.ChosenButton>
</ui:MessageBox>
```

## Notes

- This activity is only supported on Windows. It uses Win32 dialog APIs.
- `Buttons` and `TopMost` are project-level settings with defaults `ButtonOptions.Ok` and `true` respectively.
- If `AutoCloseAfter` elapses with no user interaction, `ChosenButton` receives the value of the default button for the chosen `Buttons` configuration.
