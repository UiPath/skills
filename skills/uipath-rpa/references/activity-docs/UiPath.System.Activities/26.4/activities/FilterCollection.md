# Filter Collection

`UiPath.Activities.System.Collections.FilterCollection`1``

Filter a collection based on custom conditions.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection to filter. |
| `FilterAction` | Filter Action | `InArgument` | `FilterAction` | No | `KeepMatchingElementsOnly` | Determines whether matching elements are kept or removed. Accepted values: `KeepMatchingElementsOnly`, `RemoveMatchingElements`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Filter` | Filter | `CollectionFilterSettings` | — | The filter conditions configured through the designer's visual filter builder. Contains a logical operator (`And` / `Or`) and one or more individual filter criteria (property path, comparison operator, value). Not directly editable in XAML — use the designer UI to configure conditions. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `List<T>` | The filtered collection. When `Result` is not bound, the original collection object is mutated in-place. When `Result` is bound to a different variable, a new `List<T>` is returned. |

## Valid Configurations

When `Collection` is changed after filter conditions have already been set, the designer resets all conditions to ensure the criteria remain compatible with the new element type. This is enforced by the `EnsureCorrectFilterTypes` rule in `FilterCollectionViewModel`.

For simple types (primitive, string, enum, etc.) the designer exposes a single `CurrentItem` criterion targeting the element value directly. For complex types, each public property (including nested properties up to a configured depth) is offered as a filterable criterion.

## XAML Example

```xml
<usc:FilterCollection x:TypeArguments="x:String"
    DisplayName="Filter Collection"
    Collection="[myList]"
    Result="[filteredList]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

The `Filter` property is persisted in the XAML as a `CollectionFilterSettings` object but should always be configured through the Studio designer's visual filter builder rather than edited directly in XAML.
