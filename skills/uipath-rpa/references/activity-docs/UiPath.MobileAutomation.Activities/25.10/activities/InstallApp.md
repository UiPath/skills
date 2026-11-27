# Install App

`UiPath.MobileAutomation.Activities.InstallApp`

Install App

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AppPath` | Install App | InArgument | `string` | Yes | | Install App |

## XAML Example

```xml
<ma:InstallApp DisplayName="Install App"
               AppPath="[&quot;C:\Apps\myapp.apk&quot;]" />
```

## Notes

- This activity installs a mobile application on the connected device
- For Android, provide the path to an APK file
- For iOS, provide the path to an IPA or APP file
- The app path can be a local file path or a URL
- The device must allow installation from external sources (Android) or be properly provisioned (iOS)
- If the app is already installed, the behavior depends on the platform and Appium settings
- Must be used within a Mobile Device Connection scope
