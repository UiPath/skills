# Input Dialog

`UiPath.Core.Activities.InputDialog`

Displays a dialog box that prompts the user for text, password input, or a selection from predefined options.

**Package:** `UiPath.System.Activities`
**Category:** System > Dialog

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Title` | Title | `InArgument` | `string` | No | - | The dialog title. |
| `Label` | Label | `InArgument` | `string` | No | - | Prompt text shown in the dialog body. |
| `Options` | Options | `InArgument` | `string[]` | No | - | Fixed list of options to show as choices. Mutually exclusive with `OptionsString`. |
| `OptionsString` | Options String | `InArgument` | `string` | No | - | String that is split into option values by the dialog helper. Mutually exclusive with `Options`. |
| `IsPassword` | IsPassword | Property | `bool` | No | `false` | Masks typed input. Cannot be used together with `Options` or `OptionsString`. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TopMost` | TopMost | `InArgument` | `bool` | `false` | Keeps the input dialog above other windows. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | Inferred | The entered text or selected option, converted to the output argument type when possible. |

## Valid Configurations

| Mode | Properties |
|------|------------|
| Free text input | `Title`, `Label`, optional `Result` |
| Password input | `IsPassword = true`, optional `Title`, `Label`, `Result` |
| Option selection | Set exactly one of `Options` or `OptionsString`; do not set `IsPassword` |

## XAML Example

```xml
<ui:InputDialog
    DisplayName="Input Dialog"
    Title="Approval"
    Label="Choose a status"
    Options="[New String() { &quot;Approved&quot;, &quot;Rejected&quot; }]"
    Result="[status]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- The activity throws if the user cancels the dialog.
- `Options` and `OptionsString` cannot both be set.
