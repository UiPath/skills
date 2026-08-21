# Read List Item

`UiPath.Activities.System.Arrays.ReadListItem<T>`

Retrieves the value of a specific item in a list.

**Package:** `UiPath.System.Activities`
**Category:** Data.Lists

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| List | List | InArgument | `IList<T>` | Yes | — | The list from which to read the item. |
| Index | Index | InArgument | `int` | Yes | — | The zero-based index of the item to retrieve. |

### Configuration

_No configuration properties._

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Item | Item | OutArgument | `T` | The value at the specified index in the list. |

## XAML Example

```xml
<!-- Read item at index 2 from a list of strings -->
<ui:ReadListItem x:TypeArguments="x:String">
  <ui:ReadListItem.List>
    <InArgument x:TypeArguments="scg:IList(x:String)">[myStringList]</InArgument>
  </ui:ReadListItem.List>
  <ui:ReadListItem.Index>
    <InArgument x:TypeArguments="x:Int32">2</InArgument>
  </ui:ReadListItem.Index>
  <ui:ReadListItem.Item>
    <OutArgument x:TypeArguments="x:String">[itemValue]</OutArgument>
  </ui:ReadListItem.Item>
</ui:ReadListItem>
```

## Notes

- This is a generic activity; the element type `T` is determined at design time.
- An `ArgumentOutOfRangeException` is thrown if `Index` is negative or greater than or equal to the list's count.
- Lists are zero-indexed: the first element is at index `0`.
- Compatible with any `IList<T>` implementation, including `List<T>` and arrays.
