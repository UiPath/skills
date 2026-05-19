# Set Field

`UiPath.Terminal.Activities.TerminalSetField`

Writes text into a specific input field on the terminal screen. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text to write into the field. |

### Field

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `LabeledBy` | LabeledBy | `InArgument` | `string` | | | Text of the label that immediately precedes the target field. |
| `Index` | Index | `InArgument` | `int` | | | Zero-based index used to disambiguate when multiple fields match the label criteria. Cannot be used without `LabeledBy` or `FollowedBy`. |
| `FollowedBy` | FollowedBy | `InArgument` | `string` | | | Text of the label that immediately follows the target field. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before writing. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

- `NONE` — Do not wait; write immediately.
- `READY` — Wait for the keyboard to be unlocked (screen ready for input).
- `COMPLETE` — Wait for all data to arrive on the screen.

## Notes

At least one of `LabeledBy` or `FollowedBy` must be provided. Both can be specified together for a more precise match. `Index` is a secondary criterion used to disambiguate when multiple fields share the same label — it cannot be used alone without `LabeledBy` or `FollowedBy`.

## XAML Example

```xml
<uit:TerminalSetField DisplayName="Set Field"
                    LabeledBy="[&quot;Username:&quot;]"
                    Text="[username]"
                    WaitType="READY"
                    DelayMS="300" />
```
