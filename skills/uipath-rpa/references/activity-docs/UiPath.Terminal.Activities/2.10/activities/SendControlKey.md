# Send Control Key

`UiPath.Terminal.Activities.TerminalSendControlKey`

Sends a single control key (such as Tab, Enter/Transmit, F1–F24, arrow keys, or terminal-specific function keys) to the terminal.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Key` | Key | `Property` | `ControlKey` | Yes | | The control key to send. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `1000` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before sending. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

**`ControlKey`** (selected values):

| Value | Description |
|-------|-------------|
| `Transmit` | Submit / Enter (3270) |
| `Tab` | Tab key |
| `BackTab` | Reverse tab |
| `Return` | Carriage return (VT) |
| `Escape` | Escape key (VT) |
| `F1`–`F24` | Function keys F1 through F24 |
| `Shift_F1`–`Shift_F12` | Shift + function keys |
| `Ctrl_F1`–`Ctrl_F12` | Ctrl + function keys |
| `Alt_F1`–`Alt_F12` | Alt + function keys |
| `PA1`, `PA2`, `PA3` | Program Attention keys (3270) |
| `Clear` | Clear screen (3270) |
| `Reset` | Reset (3270) |
| `Attention` | Attention (3270) |
| `BackSpace` | Backspace |
| `Home` | Home key |
| `End` | End key |
| `Insert` | Insert key |
| `Delete` | Delete key |
| `PageUp`, `PageDown` | Page Up / Page Down |
| `Up`, `Down`, `Left`, `Right` | Arrow keys |
| `EraseEOF` | Erase end of field (3270) |
| `EraseInput` | Erase input (3270) |
| `Break` | Break (VT) |
| `System` | System key (VT) |
| `HoldScreen`, `NextScreen`, `PrevScreen` | VT screen navigation |
| `Ctrl_A`–`Ctrl_Z` | Ctrl + letter (VT) |
| `Wyse_Send`, `Wyse_Shift_Tab`, `Wyse_Shift_Enter` | Wyse terminal keys |
| `CursorSelect` | Cursor Select (3270) |
| `FieldPlus`, `FieldMinus`, `FieldExit` | AS400 field keys |
| `Select` | Select (VT) |
| `Do`, `End` | VT Do / End keys |
| `Tandem_Next_Page`, `Tandem_Prev_Page` | Tandem page navigation |
| `Tandem_Left`, `Tandem_Right` | Tandem directional keys |
| `Tandem_Program_Reset`, `Tandem_Soft_Reset` | Tandem reset keys |
| `Tandem_Shift_Next_Page`, `Tandem_Shift_Prev_Page` | Tandem shift page keys |

## XAML Example

```xml
<t:TerminalSendControlKey DisplayName="Send Control Key"
                           Key="Transmit" />
```
