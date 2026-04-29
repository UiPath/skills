# Manage Other App

`UiPath.MobileAutomation.Activities.ManageOtherApp`

Manage other app using commands

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `App` | App | InArgument | `string` | Yes | | App representing the ios bundle id or android package name |
| `Command` | Manage Other App | InArgument | `ManageOtherAppCommandEnum` | Yes | `Activate` | Manage other app using commands |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Result | `bool` | Result of the command |

## Enum Reference

**`ManageOtherAppCommandEnum`**: `Activate`, `Terminate`, `Install`, `Remove`, `GetState`

## XAML Example

```xml
<ma:ManageOtherApp DisplayName="Manage Other App"
                   App="[&quot;com.example.otherapp&quot;]"
                   Command="Activate"
                   Result="[commandResult]" />
```

## Notes

- This activity manages applications other than the one currently configured in the Mobile Device Connection
- For Android, use the package name (e.g., "com.android.settings")
- For iOS, use the bundle ID (e.g., "com.apple.mobilesafari")
- Available commands:
  - **Activate**: Bring the application to the foreground
  - **Terminate**: Force stop the application
  - **Install**: Install the application on the device
  - **Remove**: Uninstall the application from the device
  - **GetState**: Get the current state of the application
- The Result output indicates whether the command was successful
