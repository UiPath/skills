# Extract Text

`UiPath.Activities.System.Text.ExtractText`

Extracts text from the given input matching the specified criteria. The following extraction options are available: value between two strings, e-mail addresses, URLs, and text from HTML code.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source | InArgument | `String` | Yes | — | The input text from which to extract content. |
| `StartingText` | Starting text | InArgument | `String` | No | — | Text that marks the beginning of the substring to extract. Defaults to start of text when empty. Visible only when `ExtractOptions` is `BetweenStrings`. |
| `EndingText` | Ending text | InArgument | `String` | No | — | Text that marks the ending of the substring to extract. Defaults to end of text when empty. Visible only when `ExtractOptions` is `BetweenStrings`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExtractOptions` | What to extract | `TextExtractOptions` | — | The extraction mode that determines what kind of content is extracted. Required. |
| `IgnoreDuplicates` | Ignore duplicates | `Boolean` | `false` | When enabled, duplicate extracted values are removed from the results. Not visible for `FromHTML` mode. |
| `MatchCase` | Match case | `Boolean` | `false` | When enabled, the search for `StartingText` and `EndingText` is case-sensitive. Visible only when `ExtractOptions` is `BetweenStrings`. |
| `ExtractBaseURLOnly` | Extract base URL only | `Boolean` | `false` | When enabled, only the scheme and host part of each URL is extracted (e.g. `https://example.com`). Visible only when `ExtractOptions` is `URLs`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result / First match | OutArgument | `String` | The first extracted value. Display name changes based on the selected `ExtractOptions`. Not produced in `FromHTML` mode when using the `Results` output. |
| `Results` | Results | OutArgument | `IEnumerable<String>` | All extracted values. Not available in `FromHTML` mode (use `Result` instead for that mode). |

## Valid Configurations

The visible properties change depending on the value of `ExtractOptions`:

| `ExtractOptions` | `StartingText` | `EndingText` | `MatchCase` | `IgnoreDuplicates` | `ExtractBaseURLOnly` | `Results` |
|---|---|---|---|---|---|---|
| `BetweenStrings` | Visible | Visible | Visible | Visible | Hidden | Visible |
| `Email` | Hidden | Hidden | Hidden | Visible | Hidden | Visible |
| `URLs` | Hidden | Hidden | Hidden | Visible | Visible | Visible |
| `FromHTML` | Hidden | Hidden | Hidden | Hidden | Hidden | Hidden |

### Enum Reference

**`TextExtractOptions`**: `BetweenStrings`, `Email`, `URLs`, `FromHTML`

## XAML Example

```xml
<ucs:ExtractText
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[htmlContent]"
  ExtractOptions="BetweenStrings"
  StartingText="[&quot;&lt;b&gt;&quot;]"
  EndingText="[&quot;&lt;/b&gt;&quot;]"
  MatchCase="False"
  IgnoreDuplicates="True"
  Result="[firstBoldText]"
  Results="[allBoldTexts]" />
```

## Notes

- For `BetweenStrings`: if `StartingText` is empty the extraction starts from the beginning of the source; if `EndingText` is empty the extraction runs to the end of the source.
- For `FromHTML`: HTML tags, scripts, and head sections are removed and HTML entities are decoded. Only the `Result` output is populated; `Results` is not used.
- For `Email` and `URLs`, the activity uses built-in regular expressions to identify matching patterns.
- `ExtractBaseURLOnly` (URLs mode) returns only the scheme and authority (e.g. `https://example.com`), discarding any path or query string.
