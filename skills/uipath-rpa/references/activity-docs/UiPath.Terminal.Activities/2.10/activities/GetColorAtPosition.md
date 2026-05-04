# Get Color at Position

`UiPath.Terminal.Advanced.Activities.TerminalGetColorAtPosition`

Returns the foreground color of the character at the specified row and column on the terminal screen. Useful for detecting highlighted fields, error indicators, or status colors.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row of the character (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column of the character (1-based). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TerminalColor` | Color | `OutArgument` | `System.Drawing.Color` | The foreground color of the character at the specified position. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before reading. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

Color availability depends on the terminal provider and emulation type. Not all providers support color information (see BlueZone's `colorsAvailable` flag).

## XAML Example

```xml
<ta:TerminalGetColorAtPosition DisplayName="Get Color at Position"
                                Row="[3]"
                                Column="[5]"
                                TerminalColor="[charColor]" />
```
