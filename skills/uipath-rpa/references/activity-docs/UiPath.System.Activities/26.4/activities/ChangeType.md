# Change Type

`UiPath.Core.Activities.ChangeType<T>`

Changes the data type of a variable.

**Package:** `UiPath.System.Activities`
**Category:** Programming.String

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Value | Value | InArgument | `object` | Yes | — | The value whose type is to be converted. Accepts any object. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Result | Result | OutArgument | `T` | The input value converted to the generic type parameter `T`. |

## XAML Example

```xml
<!-- Convert a string to Integer -->
<ui:ChangeType x:TypeArguments="x:Int32">
  <ui:ChangeType.Value>
    <InArgument x:TypeArguments="x:Object">[stringVariable]</InArgument>
  </ui:ChangeType.Value>
  <ui:ChangeType.Result>
    <OutArgument x:TypeArguments="x:Int32">[intVariable]</OutArgument>
  </ui:ChangeType.Result>
</ui:ChangeType>
```

## Notes

- This is a generic activity; the target type `T` is set at design time in Studio's type picker.
- Conversion is performed via `System.Convert.ChangeType`, so the input value must implement `IConvertible` or a compatible conversion must exist.
- If the conversion fails at runtime (e.g., converting `"abc"` to `Int32`), a `FormatException` or `InvalidCastException` is thrown.
- Common use cases: converting a `string` read from a file or UI element to a numeric or date type.
