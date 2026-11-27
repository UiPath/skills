# Find Matching Patterns

`UiPath.Core.Activities.Matches`

Searches an input string for all occurrences of a regular expression and returns all the successful matches.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Input` | Text to search in | InArgument | `String` | Yes | — | The string in which to search for matches. |
| `Pattern` | Pattern | InArgument | `String` | Yes | — | The regular expression pattern to match against. |
| `TimeoutMS` | Timeout (ms) | InArgument | `Int32` | No | — | Maximum time in milliseconds allowed for each individual match operation. Leave empty for no timeout. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RegexOption` | Pattern options | `RegexOptions` | `IgnoreCase, Compiled` | Flags that control regular expression matching behavior. Multiple flags can be combined. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `FirstMatch` | First Match | OutArgument | `String` | The value of the first successful match, or `null` if no match was found. |
| `Matches` | Matches | OutArgument | `IEnumerable<Match>` | A collection of all successful `System.Text.RegularExpressions.Match` objects found in the input. |

### Enum Reference

**`RegexOptions`** (flags, combinable): `None`, `IgnoreCase`, `Multiline`, `ExplicitCapture`, `Compiled`, `Singleline`, `IgnorePatternWhitespace`, `RightToLeft`, `ECMAScript`, `CultureInvariant`

## XAML Example

```xml
<ui:Matches
  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
  Input="[myText]"
  Pattern="[&quot;\b\w+\b&quot;]"
  RegexOption="IgnoreCase, Compiled"
  FirstMatch="[firstMatchResult]"
  Matches="[allMatches]" />
```

## Notes

- The `Matches` output is a collection of `System.Text.RegularExpressions.Match` objects. Access the matched string via `.Value` and capture groups via `.Groups`.
- `FirstMatch` is a convenience output containing only the `.Value` of the first match in the collection.
- If the pattern finds no matches, `Matches` is an empty collection and `FirstMatch` is `null`.
- Setting `TimeoutMS` prevents runaway backtracking on complex patterns. A `RegexMatchTimeoutException` is thrown if the timeout expires.
