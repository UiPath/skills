# Find and Replace

`UiPath.Activities.System.Text.FindAndReplace`

Search for a specified text and replace all occurrences with a new text.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source | InArgument | `String` | Yes | — | The text in which to search and replace. |
| `ValueToFind` | Value to find | InArgument | `String` | No | — | The text string to search for in the source text. |
| `ReplaceWith` | Replace with | InArgument | `String` | No | — | The text string to substitute for each occurrence of `ValueToFind`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `MatchCase` | Match case | `Boolean` | `false` | When active, the search for `ValueToFind` is case-sensitive. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The resulting string after all occurrences of `ValueToFind` have been replaced with `ReplaceWith`. |

## XAML Example

```xml
<ucs:FindAndReplace
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[inputText]"
  ValueToFind="[&quot;foo&quot;]"
  ReplaceWith="[&quot;bar&quot;]"
  MatchCase="False"
  Result="[outputText]" />
```

## Notes

- All occurrences of `ValueToFind` in the source are replaced; the original string is not modified.
- When `MatchCase` is `false`, the comparison uses `StringComparison.OrdinalIgnoreCase`. When `true`, it uses `StringComparison.Ordinal`.
- Unlike the **Replace Matching Patterns** activity, this activity performs a plain string search with no regular expression syntax.
- If `ValueToFind` is an empty string, the behavior follows standard .NET `String.Replace` semantics (no replacement is performed).
