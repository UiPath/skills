# Get Text at Position

`UiPath.Terminal.Advanced.Activities.TerminalGetTextAtPosition`

Reads text starting at a specific row and column position on the terminal screen. An optional `Length` parameter limits how many characters are read.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | The row to start reading from (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | The column to start reading from (1-based). |
| `Length` | Length | `InArgument` | `int` | | | Number of characters to read. If not set, reads to the end of the line. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text read from the specified position. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before reading. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## XAML Example

```xml
<ta:TerminalGetTextAtPosition DisplayName="Get Text at Position"
                               Row="[5]"
                               Column="[10]"
                               Length="[20]"
                               Text="[fieldText]" />
```
