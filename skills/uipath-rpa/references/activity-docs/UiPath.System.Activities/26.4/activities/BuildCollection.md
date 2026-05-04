# Build Collection

`UiPath.Activities.System.Collections.BuildCollection`1``

Create a collection of items that have the same type as the first specified element.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FirstItem` | First Item | `InArgument` | `T` | Yes | — | The first element of the new collection. The type of this argument determines `T` for the entire activity. |
| `NextItems` | Next Items | `InArgument` | `List<InArgument<T>>` | No | — | Additional individual items to include in the collection. Mutually exclusive with `Items` — only one may be set at a time. Visible by default when `Items` is not bound. |
| `Items` | Items | `InArgument` | `ICollection<T>` | No | — | An existing collection whose elements are appended after `FirstItem`. Mutually exclusive with `NextItems` — only one may be set at a time. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `List<T>` | The newly built collection containing `FirstItem` followed by either all `NextItems` or all elements from `Items`. |

## Valid Configurations

The designer enforces that `NextItems` and `Items` cannot both be set simultaneously. A context menu on each property lets you switch modes:

| Mode | Visible properties |
|------|--------------------|
| Individual items mode (default) | `FirstItem`, `NextItems` |
| Collection mode | `FirstItem`, `Items` |

Use the **"Use Items"** menu action on `NextItems` to switch to collection mode, or **"Use Next Items"** on `Items` to switch back.

## XAML Example

```xml
<usc:BuildCollection x:TypeArguments="x:String"
    DisplayName="Build Collection"
    FirstItem="[&quot;alpha&quot;]"
    Result="[builtList]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

The activity always returns a new `List<T>` — the source collections or arguments are not modified. Setting both `NextItems` and `Items` is a validation error.
