# Exists In Collection

`UiPath.Activities.System.Collections.ExistsInCollection`1``

Checks if the given Item exists in the collection.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection to search. |
| `Item` | Item | `InArgument` | `T` | Yes | — | The element to look for. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Exists` | Exists | `OutArgument` | `bool` | `True` if the item is found in the collection; `False` otherwise. |
| `Index` | Index | `OutArgument` | `int` | The zero-based index of the first occurrence of the item, or `-1` if the item is not found. |

## XAML Example

```xml
<usc:ExistsInCollection x:TypeArguments="x:String"
    DisplayName="Exists In Collection"
    Collection="[myList]"
    Item="[&quot;target&quot;]"
    Exists="[itemExists]"
    Index="[itemIndex]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

The activity throws an error if `Collection` or `Item` is null at runtime. Equality is determined by the default `ICollection<T>.Contains` implementation, which uses the type's `Equals` method.
