# Find Text

`UiPath.Terminal.Advanced.Activities.TerminalFindTextInScreen`

Searches the terminal screen for a text string, starting from an optional position, and returns the row and column coordinates where the text was found.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text string to search for. |
| `StartRow` | StartRow | `InArgument` | `int` | | | Row to start searching from (1-based). Defaults to the beginning of the screen if not set. |
| `StartColumn` | StartColumn | `InArgument` | `int` | | | Column to start searching from (1-based). Defaults to the beginning of the screen if not set. |
| `IgnoreCase` | Ignore Case | `Property` | `bool` | | `false` | When `true`, the search is case-insensitive. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Row` | Row | `OutArgument` | `int` | The row where the text was found (1-based). |
| `Column` | Column | `OutArgument` | `int` | The column where the text was found (1-based). |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before searching. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

- If the text is not found, the activity throws an `InvalidCoordinates` exception.
- Use the output `Row` and `Column` values as inputs to other position-based activities.
- To find text and move the cursor there in one step, use **Move Cursor to Text** instead.

## XAML Example

```xml
<uit:TerminalFindTextInScreen DisplayName="Find Text"
                              Text="[&quot;ERROR&quot;]"
                              IgnoreCase="True"
                              Row="[foundRow]"
                              Column="[foundCol]"
                              WaitType="READY"
                              DelayMS="300" />
```
