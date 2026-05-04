# Get Screen Area

`UiPath.Terminal.Advanced.Activities.TerminalGetScreenArea`

Reads all text within a rectangular region of the terminal screen, defined by a start position (Row/Column) and an end position (EndRow/EndColumn).

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | Starting row of the region (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | Starting column of the region (1-based). |
| `EndRow` | EndRow | `InArgument` | `int` | Yes | | Ending row of the region (1-based, inclusive). |
| `EndColumn` | EndColumn | `InArgument` | `int` | Yes | | Ending column of the region (1-based, inclusive). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text read from the specified screen region. |

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
<ta:TerminalGetScreenArea DisplayName="Get Screen Area"
                           Row="[3]"
                           Column="[1]"
                           EndRow="[10]"
                           EndColumn="[80]"
                           Text="[areaText]" />
```
