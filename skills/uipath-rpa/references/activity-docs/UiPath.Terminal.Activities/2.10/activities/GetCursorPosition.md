# Get Cursor Position

`UiPath.Terminal.Activities.TerminalGetCursorPosition`

Returns the current row and column position of the terminal cursor.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Row` | Row | `OutArgument` | `int` | The current row of the cursor (1-based). |
| `Column` | Column | `OutArgument` | `int` | The current column of the cursor (1-based). |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## XAML Example

```xml
<uit:TerminalGetCursorPosition DisplayName="Get Cursor Position"
                              Row="[cursorRow]"
                              Column="[cursorCol]"
                              WaitType="READY"
                              DelayMS="300" />
```
