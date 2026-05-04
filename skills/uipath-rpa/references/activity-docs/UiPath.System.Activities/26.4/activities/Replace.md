# Replace Matching Patterns

`UiPath.Core.Activities.Replace`

Within a specified input string, replaces strings that match a regular expression pattern with a specified replacement string.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Input` | Text to replace | InArgument | `String` | Yes | — | The string in which to search for matches and perform replacements. |
| `Pattern` | Pattern | InArgument | `String` | Yes | — | The regular expression pattern that identifies the substrings to replace. |
| `Replacement` | Replace with text | InArgument | `String` | Yes | — | The replacement string. Supports regex substitution syntax (e.g. `$1` for capture group references). |
| `TimeoutMS` | Timeout (ms) | InArgument | `Int32` | No | — | Maximum time in milliseconds allowed per match operation. Leave empty for no timeout. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RegexOption` | Pattern options | `RegexOptions` | `IgnoreCase, Compiled` | Flags that control regular expression matching behavior. Multiple flags can be combined. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The resulting string after all pattern matches have been replaced. |

### Enum Reference

**`RegexOptions`** (flags, combinable): `None`, `IgnoreCase`, `Multiline`, `ExplicitCapture`, `Compiled`, `Singleline`, `IgnorePatternWhitespace`, `RightToLeft`, `ECMAScript`, `CultureInvariant`

## XAML Example

```xml
<ui:Replace
  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
  Input="[sourceText]"
  Pattern="[&quot;\s+&quot;]"
  Replacement="[&quot; &quot;]"
  RegexOption="IgnoreCase, Compiled"
  Result="[cleanedText]" />
```

## Notes

- The `Replacement` string can reference captured groups using `$1`, `$2`, etc. or named groups using `${name}`.
- If `TimeoutMS` is not set, the match timeout defaults to `Regex.InfiniteMatchTimeout`.
- All occurrences of the pattern in `Input` are replaced; the original string is not modified (strings are immutable in .NET).
- The activity uses the .NET `Regex.Replace` static method, which caches the 15 most recently used patterns automatically.
