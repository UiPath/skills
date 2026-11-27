# Combine Text

`UiPath.Activities.System.Text.CombineText`

Combines text from a given collection, with the provided separator.

**Package:** `UiPath.System.Activities`
**Category:** Formatting

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Source` | Text values | InArgument | `IEnumerable<String>` | No | — | The collection of text values to be joined together. |
| `Separator` | Separator | InArgument | `String` | Yes | — | The text inserted between each value in the collection. Supports a dropdown of common predefined separators. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `String` | The single string produced by joining all values in the collection with the separator. |

## Valid Configurations

The `Separator` field supports a dropdown of predefined values as well as a free-form custom string. When a predefined separator is selected the internal `SeparatorKey` property is set automatically and is not exposed in the designer.

### Enum Reference

**`SeparatorOptions`**: `Custom`, `NewLine`, `Space`, `Tab`, `Comma`, `Colon`, `SemiColon`

## XAML Example

```xml
<ucs:CombineText
  xmlns:ucs="clr-namespace:UiPath.Activities.System.Text;assembly=UiPath.System.Activities.Standard"
  Source="[wordList]"
  Separator="[&quot;, &quot;]"
  Result="[combinedText]" />
```

## Notes

- Internally uses `String.Join` semantics: the separator is placed between elements only, not at the start or end of the result.
- If `Source` is an empty collection the result is an empty string.
- If the collection contains a single item the result equals that item (no separator is added).
