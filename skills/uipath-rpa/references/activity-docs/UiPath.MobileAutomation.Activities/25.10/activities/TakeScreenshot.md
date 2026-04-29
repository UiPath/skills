# Take Screenshot

`UiPath.MobileAutomation.Activities.TakeScreenshot`

Take a screenshot from a mobile device

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ScreenshotFilePath` | Take Screenshot | InArgument | `string` | Yes | | Take a screenshot from a mobile device |

## XAML Example

```xml
<ma:TakeScreenshot DisplayName="Take Screenshot"
                   ScreenshotFilePath="[&quot;C:\Screenshots\device_screen.png&quot;]" />
```

## Notes

- This activity captures a screenshot of the current mobile device screen
- The screenshot is saved to the specified file path
- Supports common image formats (typically PNG)
- Useful for documentation, debugging, or validation purposes
- Must be used within a Mobile Device Connection scope
