# Get Field

`UiPath.Terminal.Activities.TerminalGetField`

Reads the text content of a specific input field on the terminal screen. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Field

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `LabeledBy` | LabeledBy | `InArgument` | `string` | | | Text of the label that immediately precedes the target field. |
| `Index` | Index | `InArgument` | `int` | | | Zero-based index used to disambiguate when multiple fields match the label criteria. Cannot be used without `LabeledBy` or `FollowedBy`. |
| `FollowedBy` | FollowedBy | `InArgument` | `string` | | | Text of the label that immediately follows the target field. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text content read from the identified field. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `5000` | Milliseconds to wait for the operation to complete. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen before reading. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

- `NONE` — Do not wait; read immediately.
- `READY` — Wait for the keyboard to be unlocked (screen ready for input).
- `COMPLETE` — Wait for all data to arrive on the screen.

## Notes

At least one of `LabeledBy` or `FollowedBy` must be provided. Both can be specified together for a more precise match. `Index` is a secondary criterion used to disambiguate when multiple fields share the same label — it cannot be used alone without `LabeledBy` or `FollowedBy`.

## XAML Example

**By preceding label:**

```xml
<t:TerminalGetField DisplayName="Get Field"
                    LabeledBy="[&quot;Username:&quot;]"
                    Text="[usernameValue]" />
```

**By both labels with index to disambiguate:**

```xml
<t:TerminalGetField DisplayName="Get Field"
                    LabeledBy="[&quot;Amount:&quot;]"
                    FollowedBy="[&quot;USD&quot;]"
                    Index="[1]"
                    Text="[fieldValue]" />
```
