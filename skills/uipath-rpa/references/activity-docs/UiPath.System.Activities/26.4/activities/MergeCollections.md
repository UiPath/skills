# Merge Collections

`UiPath.Activities.System.Collections.MergeCollections`1``

Combine collections in a new collection that contains all the elements.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The first collection to merge. |
| `SecondCollection` | Second Collection | `InArgument` | `ICollection<T>` | Yes | — | The second collection to merge. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `List<T>` | A new list containing all elements from `Collection` followed by all elements from `SecondCollection`. |

## XAML Example

```xml
<usc:MergeCollections x:TypeArguments="x:String"
    DisplayName="Merge Collections"
    Collection="[firstList]"
    SecondCollection="[secondList]"
    Result="[mergedList]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

When `Result` is bound to the same variable as `Collection` or `SecondCollection`, the activity appends the other collection's elements in-place to avoid an unnecessary copy. In all other cases a new `List<T>` is allocated via `Enumerable.Concat`.
