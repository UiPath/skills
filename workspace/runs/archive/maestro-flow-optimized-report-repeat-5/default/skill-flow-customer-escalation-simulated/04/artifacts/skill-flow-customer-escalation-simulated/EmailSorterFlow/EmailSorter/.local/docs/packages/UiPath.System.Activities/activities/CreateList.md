# Create List

`UiPath.Core.Activities.CreateList<T>`

Creates a new empty `List<T>` and stores it in an output variable.

**Package:** `UiPath.System.Activities`
**Category:** Data > Lists

## Properties

### Output

| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `NewList` | New list | `OutArgument` | `IList<T>` | Yes | The newly created empty list. The activity generic type `T` controls the item type. |

## XAML Example

```xml
<ui:CreateList x:TypeArguments="x:String"
    DisplayName="Create List"
    NewList="[names]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- The output value is a `System.Collections.Generic.List<T>` exposed as `IList<T>`.
- Use this activity before list operations such as **Append Item to List** when you need a new mutable list.
