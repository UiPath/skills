# Append Items to Collection

`UiPath.Activities.System.Collections.AppendItemToCollection`1``

Appends one or more items at the end of the specified collection.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection to which items are appended. |
| `Items` | Items | `InArgument` | `IEnumerable<InArgument<T>>` | Yes | — | One or more items to append to the collection. At least one item must be provided. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `List<T>` | The updated collection after appending. When bound, a new `List<T>` is returned containing all original elements plus the appended items and the original collection is not modified. When not bound, items are appended directly to the existing collection object. |

## XAML Example

```xml
<usc:AppendItemToCollection x:TypeArguments="x:String"
    DisplayName="Append Items to Collection"
    Collection="[myList]"
    Result="[updatedList]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

Throws an error if the target collection is fixed-size (e.g., an array). Use a `List<T>` when mutation is required.
