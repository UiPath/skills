# Move Cursor to Text

`UiPath.Terminal.Advanced.Activities.TerminalMoveCursorToText`

Searches the terminal screen for a text string and moves the terminal cursor to the position where the text was found. Also returns the coordinates of the found text.

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
| `Row` | Row | `OutArgument` | `int` | The row where the text was found and the cursor moved to (1-based). |
| `Column` | Column | `OutArgument` | `int` | The column where the text was found and the cursor moved to (1-based). |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before searching. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

- Combines a text search with a cursor move in a single activity. Equivalent to **Find Text** followed by **Move Cursor**.
- If the text is not found, the activity throws an `InvalidCoordinates` exception.

## XAML Example

```xml
<ta:TerminalMoveCursorToText DisplayName="Move Cursor to Text"
                               Text="[&quot;Password:&quot;]"
                               IgnoreCase="True"
                               Row="[foundRow]"
                               Column="[foundCol]" />
```
