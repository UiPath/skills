# Custom Input

`UiPath.Core.Activities.CustomInput`

Displays a custom HTML or web-based input form and returns the submitted result as text.

**Package:** `UiPath.System.Activities`
**Category:** System > Dialog

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `URI` | URI | `InArgument` | `string` | Yes | - | Absolute URI or local file path to the custom input page. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `Width` | Width | `InArgument` | `int` | `800` when omitted or <= 0 | Dialog width in pixels. |
| `Height` | Height | `InArgument` | `int` | `600` when omitted or <= 0 | Dialog height in pixels. |
| `TopMost` | TopMost | `InArgument` | `bool` | `true` | Keeps the custom input window above other windows. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `string` | The text returned by the custom input page. |

## XAML Example

```xml
<ui:CustomInput
    DisplayName="Custom Input"
    URI="C:\forms\approval.html"
    Width="900"
    Height="650"
    Result="[formResult]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- Relative file paths are converted to full local paths before the form is opened.
- The activity reads the custom input process standard output and stores it in `Result`.
