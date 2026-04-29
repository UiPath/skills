# Terminal Activities

`UiPath.Terminal.Activities`

Terminal emulation activities for automating interactions with IBM 3270/5250, VT, HP, and other legacy terminal systems. Supports BlueZone, IBM PCOMM, Attachmate, and direct TCP/SSH connections.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/coded-api.md) — Service API for coded C# workflows

## Activities

### App Integration.Terminals

| Activity | Description |
|----------|-------------|
| [Terminal Session](activities/TerminalSession.md) | Container scope that establishes and manages a terminal connection for all child activities. |
| [Get Text](activities/GetText.md) | Reads the entire visible text content of the terminal screen. |
| [Get Field](activities/GetField.md) | Reads the text of a specific input field, identified by label, index, or adjacent label. |
| [Set Field](activities/SetField.md) | Writes text into a specific input field, identified by label, index, or adjacent label. |
| [Get Cursor Position](activities/GetCursorPosition.md) | Returns the current row and column of the terminal cursor. |
| [Send Control Key](activities/SendControlKey.md) | Sends a control key (Tab, F1–F24, Enter, etc.) to the terminal. |
| [Wait Screen Text](activities/WaitScreenText.md) | Waits until a specified text string appears anywhere on the terminal screen. |
| [Wait Field Text](activities/WaitFieldText.md) | Waits until a specific input field contains the expected text. |

### App Integration.Terminals.Advanced

| Activity | Description |
|----------|-------------|
| [Move Cursor](activities/MoveCursor.md) | Moves the terminal cursor to an exact row/column position. |
| [Send Keys](activities/SendKeys.md) | Sends a raw text string or key sequence directly to the terminal. |
| [Send Keys Secure](activities/SendKeysSecure.md) | Sends a `SecureString` (e.g., a password) to the terminal without exposing it as plain text. |
| [Wait Screen Ready](activities/WaitScreenReady.md) | Waits until the terminal keyboard is unlocked and the screen is ready for input. |
| [Get Screen Area](activities/GetScreenArea.md) | Reads the text from a rectangular region of the terminal screen defined by start and end coordinates. |
| [Get Text at Position](activities/GetTextAtPosition.md) | Reads text starting at a specific row/column, optionally limited to a given length. |
| [Get Field at Position](activities/GetFieldAtPosition.md) | Reads the content of the field that starts at the specified row/column position. |
| [Get Color at Position](activities/GetColorAtPosition.md) | Returns the foreground color of the character at the specified row/column. |
| [Set Field at Position](activities/SetFieldAtPosition.md) | Writes text into the field at a specific row/column position. |
| [Wait Text at Position](activities/WaitTextAtPosition.md) | Waits until a specific row/column position contains the expected text. |
| [Find Text](activities/FindText.md) | Searches the screen for a text string, starting from an optional position, and returns the coordinates where it was found. |
| [Move Cursor to Text](activities/MoveCursorToText.md) | Searches the screen for a text string and moves the terminal cursor to the location where it was found. |
