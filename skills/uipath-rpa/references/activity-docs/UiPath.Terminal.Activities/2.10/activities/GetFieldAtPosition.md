# Get Field at Position

`UiPath.Terminal.Advanced.Activities.TerminalGetFieldAtPosition`

Reads the content of the input field that starts at the specified row and column position on the terminal screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row of the field start (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column of the field start (1-based). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text content of the field at the specified position. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before reading. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

Unlike **Get Text at Position** (which reads raw character data from a position), this activity reads the structured field at that position as defined by the terminal's field attributes.

## XAML Example

```xml
<uit:TerminalGetFieldAtPosition DisplayName="Get Field at Position"
                                Row="[7]"
                                Column="[15]"
                                Text="[fieldValue]"
                                WaitType="READY"
                                DelayMS="300" />
```
