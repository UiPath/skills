# Modify Text

`UiPath.Core.Activities.ModifyText`

Applies one or more text modification operations to a source string and returns the modified text.

**Package:** `UiPath.System.Activities`
**Category:** Programming > String

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SourceText` | Text to modify | `InArgument` | `string` | Yes | - | The source text used by the child text modification operations. |

### Output

| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `OutputText` | Save result as | `OutArgument` | `string` | Yes | The final text after all child modifications are applied. |

### Body

| Name | Type | Description |
|------|------|-------------|
| `Body` | `ActivityAction` | Container for text modification child activities. |

## Child Text Modifications

The designer supports text modification child activities that populate the modification descriptor:

| Child Activity | Description |
|----------------|-------------|
| `CombineTextModification` | Adds text before or after the current text. |
| `FindAndReplaceTextModification` | Replaces occurrences of a search string. |
| `ToUpperLowerTextModification` | Converts text to uppercase or lowercase. |
| `TrimTextModification` | Trims whitespace from the beginning and/or end. |

## XAML Example

```xml
<ui:ModifyText
    DisplayName="Modify Text"
    SourceText="[rawText]"
    OutputText="[cleanText]">
  <ui:ModifyText.Body>
    <ActivityAction>
      <Sequence>
        <uitm:TrimTextModification TrimBefore="True" TrimAfter="True" />
        <uitm:ToUpperLowerTextModification ModificationType="Uppercase" />
      </Sequence>
    </ActivityAction>
  </ui:ModifyText.Body>
</ui:ModifyText>
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`
`xmlns:uitm="clr-namespace:UiPath.Core.Activities.TextModifications;assembly=UiPath.System.Activities"`

## Notes

- `SourceText` must resolve to a non-null string.
- Child operations are applied in order.
