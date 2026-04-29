# Manage Current App

`UiPath.MobileAutomation.Activities.ManageCurrentApp`

Manage an app using a command

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Command` | Manage Current App | InArgument | `ManageCurrentAppCommandEnum` | Yes | `Launch` | Manage an app using a command |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Result | `bool` | Result of the command |

## Enum Reference

**`ManageCurrentAppCommandEnum`**: `Launch`, `Close`, `Reset`, `Activate`, `Terminate`, `GetState`

## XAML Example

```xml
<ma:ManageCurrentApp DisplayName="Manage Current App"
                     Command="Launch"
                     Result="[commandResult]" />
```

## Notes

- This activity manages the currently configured application in the Mobile Device Connection
- Available commands:
  - **Launch**: Start the application
  - **Close**: Close the application
  - **Reset**: Reset the application to its initial state
  - **Activate**: Bring the application to the foreground
  - **Terminate**: Force stop the application
  - **GetState**: Get the current state of the application
- The Result output indicates whether the command was successful
