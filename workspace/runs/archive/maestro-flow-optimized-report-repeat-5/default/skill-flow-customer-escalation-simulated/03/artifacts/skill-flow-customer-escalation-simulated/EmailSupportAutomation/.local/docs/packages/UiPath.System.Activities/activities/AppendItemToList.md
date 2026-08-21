# Append Item to List

`UiPath.Activities.System.Arrays.AppendItemToList<T>`

Appends one item to an existing `IList<T>` and returns the index where the item was inserted.

**Package:** `UiPath.System.Activities`
**Category:** Data > Lists

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `List` | List | `InArgument` | `IList<T>` | Yes | - | The list instance to update. The activity generic type `T` is linked to this list type. |
| `ItemToAppend` | Item to append | `InArgument` | `T` | Yes | - | The item to append to the end of the list. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ItemIndex` | Item index | `OutArgument` | `int` | The zero-based index of the appended item. |

## XAML Example

```xml
<ui:AppendItemToList x:TypeArguments="x:String"
    DisplayName="Append Item to List"
    List="[names]"
    ItemToAppend="Ada"
    ItemIndex="[newIndex]" />
```

`xmlns:ui="clr-namespace:UiPath.Activities.System.Arrays;assembly=UiPath.System.Activities"`

## Notes

- `List` must resolve to a non-null mutable list. The activity calls `Add` on the supplied instance.
- The list is modified in place; no new list is created.
