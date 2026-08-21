# Update List Item

`UiPath.Activities.System.Arrays.UpdateListItem<T>`

Updates the value of a specific item in a list. Add a Read List Item activity after it to ensure you are using the updated value going forward.

**Package:** `UiPath.System.Activities`
**Category:** Data.Lists

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| List | List | InArgument | `IList<T>` | Yes | — | The list containing the item to update. The list object is mutated in place (no reassignment needed). |
| Index | Index | InArgument | `int` | Yes | — | The zero-based index of the item to update. |
| Value | Value | InArgument | `T` | Yes | — | The new value to set at the specified index. |

### Configuration

_No configuration properties._

### Output

_No output properties. The list variable passed to `List` is updated in place._

## XAML Example

```xml
<!-- Replace the item at index 1 in a list of strings -->
<ui:UpdateListItem x:TypeArguments="x:String">
  <ui:UpdateListItem.List>
    <InArgument x:TypeArguments="scg:IList(x:String)">[myStringList]</InArgument>
  </ui:UpdateListItem.List>
  <ui:UpdateListItem.Index>
    <InArgument x:TypeArguments="x:Int32">1</InArgument>
  </ui:UpdateListItem.Index>
  <ui:UpdateListItem.Value>
    <InArgument x:TypeArguments="x:String">"updated value"</InArgument>
  </ui:UpdateListItem.Value>
</ui:UpdateListItem>
```

## Notes

- This is a generic activity; the element type `T` is determined at design time.
- `List` is an `InArgument` — the list is passed in by reference and mutated in place. No reassignment of the variable occurs.
- An `ArgumentOutOfRangeException` is thrown if `Index` is out of the list's bounds.
- Follow this activity with a **Read List Item** to obtain the updated value for use in downstream activities, as variables bound before the update will hold stale references in some workflow engines.
