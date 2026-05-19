# Wait Field Text

`UiPath.Terminal.Activities.TerminalWaitFieldText`

Waits until a specific input field on the terminal screen contains the expected text. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | Yes | | The text string to wait for in the field. |
| `MatchCase` | MatchCase | `InArgument` | `bool` | | `false` | When `true`, the text comparison is case-sensitive. |

### Field

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `LabeledBy` | LabeledBy | `InArgument` | `string` | | | Text of the label that immediately precedes the target field. |
| `Index` | Index | `InArgument` | `int` | | | Zero-based index used to disambiguate when multiple fields match the label criteria. Cannot be used without `LabeledBy` or `FollowedBy`. |
| `FollowedBy` | FollowedBy | `InArgument` | `string` | | | Text of the label that immediately follows the target field. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `30000` | Milliseconds to wait for the field text before throwing a timeout error. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `300` | Milliseconds to wait after executing the activity. |
| `WaitType` | WaitType | `Property` | `WaitMode` | `READY` | Determines how to wait for the terminal screen. |

### Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`

## Notes

At least one of `LabeledBy` or `FollowedBy` must be provided. Both can be specified together for a more precise match. `Index` is a secondary criterion used to disambiguate when multiple fields share the same label — it cannot be used alone without `LabeledBy` or `FollowedBy`.

## XAML Example

```xml
<uit:TerminalWaitFieldText DisplayName="Wait Field Text"
                          LabeledBy="[&quot;Status:&quot;]"
                          Text="[&quot;OK&quot;]"
                          TimeoutMS="[30000]"
                          WaitType="READY"
                          DelayMS="300" />
```
