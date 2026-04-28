# Is Text Matching

`UiPath.Core.Activities.IsMatch`

Indicates whether the specified regular expression finds a match in the specified input string, using the specified matching options.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Input` | Text to search in | InArgument | `String` | Yes | — | The string in which to search for a match. |
| `Pattern` | Pattern | InArgument | `String` | Yes | — | The regular expression pattern to match against. |
| `TimeoutMS` | Timeout (ms) | InArgument | `Int32` | No | — | Maximum time in milliseconds allowed for the match operation. Leave empty for no timeout. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RegexOption` | Pattern options | `RegexOptions` | `IgnoreCase, Compiled` | Flags that control regular expression matching behavior. Multiple flags can be combined. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `Boolean` | `True` if the pattern finds at least one match in the input string; `False` otherwise. |

### Enum Reference

**`RegexOptions`** (flags, combinable): `None`, `IgnoreCase`, `Multiline`, `ExplicitCapture`, `Compiled`, `Singleline`, `IgnorePatternWhitespace`, `RightToLeft`, `ECMAScript`, `CultureInvariant`

## XAML Example

```xml
<ui:IsMatch
  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
  Input="[myText]"
  Pattern="[&quot;\d{3}-\d{4}&quot;]"
  RegexOption="IgnoreCase, Compiled"
  Result="[isMatchResult]" />
```

## Notes

- The default `RegexOption` is `IgnoreCase, Compiled`. Adjust this to change matching behavior (for example, use `None` for a case-sensitive match without JIT compilation overhead on one-off patterns).
- Setting `TimeoutMS` prevents runaway backtracking on complex patterns against large inputs. A `RegexMatchTimeoutException` is thrown if the timeout expires.
- The activity uses the .NET `Regex.IsMatch` static method, which caches the 15 most recently used patterns automatically.
