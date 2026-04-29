# Remove Log Fields

`UiPath.Core.Activities.RemoveLogFields`

Removes custom log fields from each Log Message.

**Package:** `UiPath.System.Activities`
**Category:** Logging

## Properties

### Input

_No input arguments._

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Fields | Fields | `List<InArgument<string>>` | — | A list of field name expressions whose entries should be removed from subsequent log messages. |

### Output

_No output properties._

## XAML Example

```xml
<ui:RemoveLogFields>
  <ui:RemoveLogFields.Fields>
    <InArgument x:TypeArguments="x:String">fieldName1</InArgument>
    <InArgument x:TypeArguments="x:String">fieldName2</InArgument>
  </ui:RemoveLogFields.Fields>
</ui:RemoveLogFields>
```

## Notes

- Only fields that were previously added via **Add Log Fields** can be removed here.
- Field names are case-sensitive.
