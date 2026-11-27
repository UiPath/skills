# Take Screenshot Part

`UiPath.MobileAutomation.Activities.TakeScreenshotPart`

Take Screenshot Part

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |
| `ScreenshotFilePath` | Take Screenshot Part | InArgument | `string` | Yes | | Take Screenshot Part |

## XAML Example

```xml
<ma:TakeScreenshotPart DisplayName="Take Screenshot Part"
                       Selector="[&quot;&lt;mobile id='product_image' /&gt;&quot;]"
                       ScreenshotFilePath="[&quot;C:\Screenshots\element.png&quot;]" />
```

## Notes

- This activity captures a screenshot of a specific mobile UI element
- The screenshot is cropped to only include the target element
- The screenshot is saved to the specified file path
- Supports common image formats (typically PNG)
- Useful for capturing specific UI components for documentation or validation
- Must be used within a Mobile Device Connection scope
