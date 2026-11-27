# ActivityNameMobileDeviceConnection

`UiPath.MobileAutomation.Activities.MobileDeviceConnection`

ActivityDescriptionMobileDeviceConnection

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AppiumUrl` | Appium Url | InArgument | `string` | | | The URL of the Appium server |
| `Arguments` | Capabilities | Property | `Dictionary<string, Argument>` | | `new Dictionary<string, Argument>()` | The requested capabilities for the connection. See http://appium.io/docs/en/writing-running-appium/caps for a list of Appium capabilities. |
| `CollectPageSource` | Collect Page Source | InArgument | `Collect` | | | Specify if a page source is retrieved after executing each activity. Supported values are None and AfterActivity |
| `CollectScreenshot` | Collect Screenshot | InArgument | `Collect` | | | Specify if a screenshot is retrieved after executing each activity. Supported values are None and AfterActivity |
| `ContinueOnError` | ContinueOnError | InArgument | `bool` | | | Specifies to continue executing the remaining activities even if the current activity failed. Only boolean values (True, False) are supported. |
| `HttpHeaders` | Http Headers | Property | `Dictionary<string, Argument>` | | `new Dictionary<string, Argument>()` | Http headers added to the requests. |
| `InputConnection` | InputConnection | InArgument | `MobileDevice` | | | Input mobile device connection |
| `LoggingEnabled` | Logging Enabled | InArgument | `bool` | | | Enables or disables the logging during execution. Only boolean values (True, False) are supported. |
| `LoggingFolderPath` | Logging Folder Path | InArgument | `string` | | | A valid folder path where the logging outputs are stored. |
| `MirroringEnabled` | Mirroring Enabled | InArgument | `bool` | | `Constants.DefaultMirroringEnabled` | |

### Input/Output Connections

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `InputConnection` | InputConnection | InArgument | `MobileDevice` | | | Input mobile device connection |
| `OutputConnection` | OutputConnection | OutArgument | `MobileDevice` | | | Output mobile device connection |

### Options

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Close` | Close | `MobileConnectionCloseMode?` | `null` | Close connection. Null value is treated like Always |

## Enum Reference

**`Collect`**: `None`, `AfterActivity`

**`MobileConnectionCloseMode`**: `Always`, `Never`, `IfNotInputConnection`

## XAML Example

```xml
<ma:MobileDeviceConnection DisplayName="Mobile Device Connection"
                          AppiumUrl="[&quot;http://127.0.0.1:4723/wd/hub&quot;]"
                          OutputConnection="[mobileDevice]"
                          Close="Always">
  <ma:MobileDeviceConnection.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="platformName">Android</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="deviceName">Android Emulator</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="app">C:\apps\myapp.apk</InArgument>
    </scg:Dictionary>
  </ma:MobileDeviceConnection.Arguments>
  <ma:MobileDeviceConnection.Body>
    <!-- Mobile automation activities go here -->
  </ma:MobileDeviceConnection.Body>
</ma:MobileDeviceConnection>
```

## Project Settings

This activity reads default values from project-level settings (configurable in UiPath Studio under Project Settings). When a property's value is not explicitly set, the project setting is used as the default.

| Property | Setting Key | Default | Description |
|----------|-----------|---------|-------------|
| `CvApiKey` | `UiPath.Sdk.Activities.CvScope.ApiKey` | `Constants.CvDefaultApiKey` | Computer Vision API key |
| `CvServer` | `UiPath.Sdk.Activities.CvScope.Server` | `Constants.CvDefaultServer` | Computer Vision server URL |
| `CvUseLocalServer` | `UiPath.Sdk.Activities.CvScope.UseLocalServer` | `Constants.CvDefaultUseLocalServer` | Use local Computer Vision server |
| `MirroringEnabled` | `UiPath.Sdk.Activities.Generic.MirroringEnabled` | `Constants.DefaultMirroringEnabled` | Enable device mirroring |

## Notes

- This is a container activity that establishes and maintains a connection to an Appium server
- All mobile automation activities must be placed inside this scope
- The Capabilities (Arguments) property is used to configure the device and application settings according to Appium specifications
- Common capabilities include: `platformName`, `deviceName`, `app`, `appPackage`, `appActivity`, `bundleId`, `udid`, etc.
- The Close property controls when the connection is terminated:
  - **Always**: Close connection when scope exits
  - **Never**: Keep connection open after scope exits
  - **IfNotInputConnection**: Close only if this scope created the connection (not passed via InputConnection)
- InputConnection/OutputConnection allow chaining multiple connection scopes or reusing existing connections
- Logging capabilities allow capturing screenshots and page sources for debugging
