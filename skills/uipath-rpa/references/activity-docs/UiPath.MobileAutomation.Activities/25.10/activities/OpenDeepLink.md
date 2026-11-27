# Open DeepLink

`UiPath.MobileAutomation.Activities.OpenDeepLink`

Go to a deeplink inside an application

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `App` | App | InArgument | `string` | | | App representing the ios bundle id or android package name |
| `Url` | Open DeepLink | InArgument | `string` | Yes | | Go to a deeplink inside an application |

## XAML Example

```xml
<ma:OpenDeepLink DisplayName="Open DeepLink"
                 Url="[&quot;myapp://products/1234&quot;]"
                 App="[&quot;com.example.myapp&quot;]" />
```

## Notes

- This activity opens a deep link URL within a mobile application
- Deep links allow direct navigation to specific content or features within an app
- The App parameter is optional; if not specified, the system will attempt to determine which app should handle the deep link
- For Android, use the package name for the App parameter
- For iOS, use the bundle ID for the App parameter
- The URL format depends on how the target application has configured its deep linking scheme
