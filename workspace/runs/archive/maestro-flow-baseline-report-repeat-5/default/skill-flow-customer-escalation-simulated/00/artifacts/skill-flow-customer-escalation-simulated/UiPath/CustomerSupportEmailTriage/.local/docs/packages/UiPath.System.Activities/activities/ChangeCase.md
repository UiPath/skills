# Change Case

`UiPath.Activities.System.Text.ChangeCase`

Select the desired letter case to convert the text to.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source | InArgument | `String` | Yes | — | The text whose case is to be changed. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ChangeCaseOptions` | Desired letter case | `ChangeCaseOptions` | — | The target case transformation to apply. Required. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The text after the case transformation has been applied. |

### Enum Reference

**`ChangeCaseOptions`**: `LowerCase`, `UpperCase`, `SentenceCase`, `CapitalizeEachWord`

| Value | Behavior |
|-------|----------|
| `LowerCase` | Converts all characters to lower case using the current culture. |
| `UpperCase` | Converts all characters to upper case using the current culture. |
| `SentenceCase` | Capitalizes the first letter after sentence-ending punctuation (`.`, `!`, `?`) and after newlines. If the input is already in `UpperCase` or `CapitalizeEachWord` format, it is first converted to lower case. |
| `CapitalizeEachWord` | Title-cases the string using the current culture's `TextInfo.ToTitleCase`. If the input is entirely in upper case, it is first converted to lower case. |

## XAML Example

```xml
<ucs:ChangeCase
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[inputText]"
  ChangeCaseOptions="CapitalizeEachWord"
  Result="[titleCasedText]" />
```

## Notes

- `SentenceCase` and `CapitalizeEachWord` use the runtime's current culture for Unicode-aware transformations.
- `SentenceCase` detects sentence boundaries at `.`, `!`, and `?` followed by whitespace, as well as at all common newline sequences (`\r\n`, `\r`, `\n`, `\u0085`, `\u2028`, `\u2029`).
- Acronyms and all-caps words are preserved as-is by `SentenceCase` unless the entire input is in upper case.
