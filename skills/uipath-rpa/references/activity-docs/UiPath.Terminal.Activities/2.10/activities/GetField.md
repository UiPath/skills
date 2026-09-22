# Get Field

`UiPath.Terminal.Activities.TerminalGetField`

Reads the text content of a specific input field on the terminal screen. The field is identified by a label that precedes it (`LabeledBy`), a label that follows it (`FollowedBy`), or both. When multiple fields match the label criteria, `Index` narrows the result.

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

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

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

At least one of `LabeledBy` or `FollowedBy` must be provided. Both can be specified together for a more precise match. `Index` is a secondary criterion used to disambiguate when multiple fields share the same label — it cannot be used alone without `LabeledBy` or `FollowedBy`.

### Prefer position-based reads when portability matters

Label-based field identification depends on the terminal provider's idea of "what is a field" — and different providers (`UiPathNew`, `IBM`, `Attachmate`, `BlueZone`, `Generic`/EHLLAPI) use different APIs and field-detection rules under the hood. The same screen can split into different field boundaries between providers, so a `GetField` that matches one label-style on a TN3270 session may fail or return a different value on the same host through an IBM PCOMM session.

For workflows that need to run against more than one provider, or against a host whose field semantics are unclear, prefer:

- [`GetTextAtPosition`](GetTextAtPosition.md) — read N characters from a known `Row` / `Column` (position is provider-agnostic).
- [`GetScreenArea`](GetScreenArea.md) — read a rectangular region; useful when the field width varies but the screen geometry is stable.
- [`FindText`](FindText.md) → [`GetTextAtPosition`](GetTextAtPosition.md) — anchor on visible label text, then read at the offset where the value lives.

Keep `GetField` for single-provider workflows where you have already validated that `LabeledBy` / `FollowedBy` resolve to the correct field, and where the label text is stable across screen variants.

## XAML Example

**By preceding label:**

```xml
<uit:TerminalGetField DisplayName="Get Field"
                    LabeledBy="[&quot;Username:&quot;]"
                    Text="[usernameValue]"
                    WaitType="READY"
                    DelayMS="300" />
```

**By both labels with index to disambiguate:**

```xml
<uit:TerminalGetField DisplayName="Get Field"
                    LabeledBy="[&quot;Amount:&quot;]"
                    FollowedBy="[&quot;USD&quot;]"
                    Index="[1]"
                    Text="[fieldValue]"
                    WaitType="READY"
                    DelayMS="300" />
```
