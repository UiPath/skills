# Move Cursor

`UiPath.Terminal.Advanced.Activities.TerminalMoveCursor`

Moves the terminal cursor to an exact row and column position on the screen.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The target row (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The target column (1-based). |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before moving. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## XAML Example

```xml
<uit:TerminalMoveCursor DisplayName="Move Cursor"
                        Row="[5]"
                        Column="[20]"
                        WaitType="READY"
                        DelayMS="300" />
```
