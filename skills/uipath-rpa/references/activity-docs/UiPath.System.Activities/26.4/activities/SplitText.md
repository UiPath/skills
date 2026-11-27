# Split Text

`UiPath.Activities.System.Text.SplitText`

Split the source text into a list of substrings based on a specified separator.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Source | InArgument | `String` | Yes | — | The text to be split. |
| `Separator` | Separator | InArgument | `String` | Yes | — | The character or text used to divide the source string. Supports a dropdown of common predefined separators. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The first substring produced by the split operation. |
| `Results` | Results | OutArgument | `IEnumerable<String>` | All substrings produced by splitting the source text at every occurrence of the separator. |

## Valid Configurations

The `Separator` field supports a dropdown of predefined values as well as a free-form custom string. When a predefined separator is selected the internal `SeparatorKey` property is set automatically and is not exposed in the designer.

### Enum Reference

**`SeparatorOptions`**: `Custom`, `NewLine`, `Space`, `Tab`, `Comma`, `Colon`, `SemiColon`

## XAML Example

```xml
<ucs:SplitText
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[csvLine]"
  Separator="[&quot;,&quot;]"
  Result="[firstField]"
  Results="[allFields]" />
```

## Notes

- The split is performed using `StringSplitOptions.None`, so consecutive separators produce empty-string entries in `Results`.
- For the `NewLine` separator, the activity splits on `\r\n`, `\r`, and `\n` to handle all common line-ending conventions.
- `Result` is a convenience output that holds only the first element of `Results`.
