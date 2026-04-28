# For Each

`UiPath.Core.Activities.ForEach`1`

Performs an activity or a series of activities on each element of an enumeration.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Values` | Values | `InArgument` | `IEnumerable<T>` | No | — | The collection to iterate over. The element type `T` is inferred from the collection and determines the type of the iterator variable. |
| `MaxIterations` | Max Iterations | `InArgument` | `int` | No | — | Maximum number of iterations. A value of `0` means unlimited. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TypeOfValues` | Type Of Values | `Type` | — | The element type `T` of the collection. Shown as a type-picker widget when supported by the designer. Changing this value morphs the activity to the selected generic type. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CurrentIndex` | Current Index | `OutArgument` | `int` | The zero-based index of the current iteration. |

## XAML Example

```xml
<ui:ForEach x:TypeArguments="x:String"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="For Each">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="scg:IEnumerable(x:String)">
      <VisualBasicValue x:TypeArguments="scg:IEnumerable(x:String)" ExpressionText="myList" />
    </InArgument>
  </ui:ForEach.Values>
  <ActivityAction x:TypeArguments="x:String">
    <ActivityAction.Argument>
      <DelegateInArgument x:TypeArguments="x:String" Name="item" />
    </ActivityAction.Argument>
    <Sequence DisplayName="Body">
      <!-- child activities reference the iterator variable "item" -->
    </Sequence>
  </ActivityAction>
</ui:ForEach>
```

## Notes

- **For Each** is a container/scope activity. Child activities are placed inside the `ActivityAction` body and can reference the iterator variable (e.g. `item`).
- The activity is generic (`ForEach<T>`); the type argument `T` is inferred from the `Values` collection or set explicitly via the `TypeOfValues` type picker.
- The iterator variable name is auto-suggested based on the element type (e.g. `stringItem` for `String`) and can be renamed. If the suggested name was not changed manually, it is automatically updated when the type changes.
- `TypeOfValues` is only visible when the designer supports the `TypePicker` widget; in other environments the type is set implicitly.
- Use a `Break` activity inside the body to exit the loop early; use `Continue` to skip to the next element.
