# Wait Field Text

`UiPath.Terminal.Activities.TerminalWaitFieldText`

Waits until a specific input field on the terminal screen contains the expected text. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

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

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults **`30000`** / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). The higher `TimeoutMS` default is appropriate for host responses that take seconds; raise further for slow scripted flows.

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
