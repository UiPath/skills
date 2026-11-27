# Set Field

`UiPath.Terminal.Activities.TerminalSetField`

Writes text into a specific input field on the terminal screen. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

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

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

At least one of `LabeledBy` or `FollowedBy` must be provided. Both can be specified together for a more precise match. `Index` is a secondary criterion used to disambiguate when multiple fields share the same label — it cannot be used alone without `LabeledBy` or `FollowedBy`.

### Prefer position-based writes when portability matters

Label-based field identification depends on the terminal provider's idea of "what is a field" — and different providers (`UiPathNew`, `IBM`, `Attachmate`, `BlueZone`, `Generic`/EHLLAPI) use different APIs and field-detection rules. The same screen can split into different field boundaries between providers, so a `SetField` that targets one label-style on a TN3270 session may write to the wrong field, throw, or silently no-op on the same host through an IBM PCOMM session.

For workflows that need to run against more than one provider, or against a host whose field semantics are unclear, prefer the position-based input pattern:

- [`MoveCursor`](MoveCursor.md) to the target row/column (or [`SendControlKey`](SendControlKey.md) with `Key="Tab"` to advance through input fields), then
- [`SendKeys`](SendKeys.md) to type the value.

Alternatively, [`SetFieldAtPosition`](SetFieldAtPosition.md) writes to the field starting at a known `Row` / `Column` — provider-agnostic input without the cursor-move step.

Keep `SetField` for single-provider workflows where you have already validated that `LabeledBy` / `FollowedBy` resolve to the correct input field, and where the label text is stable across screen variants.

## XAML Example

```xml
<uit:TerminalSetField DisplayName="Set Field"
                    LabeledBy="[&quot;Username:&quot;]"
                    Text="[username]"
                    WaitType="READY"
                    DelayMS="300" />
```
