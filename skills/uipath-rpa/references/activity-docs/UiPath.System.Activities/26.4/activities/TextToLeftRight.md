# Text to Left/Right

`UiPath.Core.Activities.TextToLeftRight`

Gets the text before and after the first occurrence of the indicated subtext.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FullText` | Text to split | InArgument | `String` | Yes | — | The full text to split at the separator. |
| `Separator` | Separator | InArgument | `String` | Yes | — | The separator string used to split the text. Supports a dropdown of common predefined separators. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `CaseSensitiveSeparator` | Case sensitive separator | `Boolean` | `true` | If checked, the separator is case sensitive. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `TextToLeft` | Extracted text before the separator | OutArgument | `String` | The text that appears before the first occurrence of the separator. |
| `TextToRight` | Extracted text after the separator | OutArgument | `String` | The text that appears after the first occurrence of the separator, including any additional occurrences joined back together. |

## Valid Configurations

The `Separator` field supports a dropdown of predefined values as well as a free-form custom string. When a predefined separator is selected the internal `SeparatorKey` property is set automatically and is not exposed in the designer.

### Enum Reference

**`DefaultSeparators`**: `Custom`, `NewLine`, `Space`, `Tab`, `Comma`, `Colon`, `SemiColon`, `EqualsSign`

## XAML Example

```xml
<ui:TextToLeftRight
  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
  FullText="[fullText]"
  Separator="[&quot;,&quot;]"
  CaseSensitiveSeparator="True"
  TextToLeft="[leftPart]"
  TextToRight="[rightPart]" />
```

## Notes

- If the separator is not found in the text, `TextToLeft` receives the full original text and `TextToRight` is set to an empty string.
- When the separator appears more than once, `TextToRight` contains everything after the first occurrence, with subsequent occurrences preserved.
- When `CaseSensitiveSeparator` is `false`, matching is performed case-insensitively but the original casing of the source text is preserved in the output.
