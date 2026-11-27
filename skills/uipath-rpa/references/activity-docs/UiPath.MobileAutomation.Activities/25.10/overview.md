# UiPath Mobile Automation Activities

This package provides activities for automating mobile applications on Android and iOS devices using the Appium framework.

**Package ID:** `UiPath.MobileAutomation.Activities`

## Activity Categories

### Mobile Device

Core mobile device management and connection activities.

- **[MobileDeviceConnection](activities/MobileDeviceConnection.md)** - Establishes and maintains a connection to an Appium server. Container scope for all mobile automation activities.
- **[ExecuteCommand](activities/ExecuteCommand.md)** - Executes a custom Appium command on the mobile device.
- **[GetDeviceOrientation](activities/GetDeviceOrientation.md)** - Gets the current orientation of the mobile device (portrait/landscape).
- **[SetDeviceOrientation](activities/SetDeviceOrientation.md)** - Sets the orientation of the mobile device.
- **[SetDeviceGeoLocation](activities/SetDeviceGeoLocation.md)** - Sets the geolocation of the mobile device for testing location-based features.
- **[GetSystemTime](activities/GetSystemTime.md)** - Gets the system time from the mobile device.
- **[TakeScreenshot](activities/TakeScreenshot.md)** - Captures a screenshot of the entire mobile device screen.
- **[TakeScreenshotPart](activities/TakeScreenshotPart.md)** - Captures a screenshot of a specific element or region on the mobile device.
- **[GetSessionIdentifier](activities/GetSessionIdentifier.md)** - Gets the unique session identifier for the current Appium session.
- **[Tap](activities/Tap.md)** - Performs a tap gesture on the mobile device screen at specified coordinates.

### Mobile Application

Activities for managing mobile applications and navigation.

- **[ManageCurrentApp](activities/ManageCurrentApp.md)** - Manages the currently active application (background, activate, terminate, etc.).
- **[ManageOtherApp](activities/ManageOtherApp.md)** - Manages other installed applications by bundle/package ID.
- **[InstallApp](activities/InstallApp.md)** - Installs a mobile application from a local file path.
- **[OpenDeepLink](activities/OpenDeepLink.md)** - Opens a deep link URL within a mobile application.
- **[OpenUrl](activities/OpenUrl.md)** - Opens a URL in the mobile browser or application.

### UI Automation

Activities for interacting with mobile UI elements.

- **[ElementExists](activities/ElementExists.md)** - Checks if a UI element exists on the mobile screen.
- **[GetAttribute](activities/GetAttribute.md)** - Gets an attribute value from a mobile UI element.
- **[GetText](activities/GetText.md)** - Gets the text content from a mobile UI element.
- **[SetText](activities/SetText.md)** - Sets text in a mobile input field.
- **[TypeText](activities/TypeText.md)** - Types text into the currently focused mobile input field.
- **[GetSelectedItem](activities/GetSelectedItem.md)** - Gets the currently selected item from a mobile picker/dropdown.
- **[SetSelectedItem](activities/SetSelectedItem.md)** - Selects an item in a mobile picker/dropdown.
- **[Swipe](activities/Swipe.md)** - Performs a swipe gesture on a mobile element in a specified direction.
- **[PositionalSwipe](activities/PositionalSwipe.md)** - Performs a swipe gesture between specific coordinates on the mobile screen.
- **[DrawPattern](activities/DrawPattern.md)** - Draws a pattern lock gesture on Android devices.

### Hardware Interaction

Activities for interacting with mobile device hardware.

- **[PressHardwareButton](activities/PressHardwareButton.md)** - Presses a hardware button (Home, Back, Volume Up/Down, Power, etc.) on the mobile device.

### Logging & Debugging

Activities for debugging and diagnostics.

- **[GetLogTypes](activities/GetLogTypes.md)** - Gets all available log types for the current Appium session.
- **[GetLogs](activities/GetLogs.md)** - Retrieves logs of a specific type from the mobile device/Appium server.
- **[GetPageSource](activities/GetPageSource.md)** - Gets the XML page source of the current mobile screen for debugging UI hierarchy.

## Prerequisites

- **Appium Server** - An Appium server must be running and accessible. See [http://appium.io](http://appium.io) for installation instructions.
- **Mobile Device or Emulator** - A physical device (connected via USB/network) or emulator/simulator.
- **Platform-specific drivers**:
  - **Android**: UIAutomator2 driver (default)
  - **iOS**: XCUITest driver (requires macOS and Xcode)

## Common Workflow Pattern

All mobile automation workflows follow this pattern:

1. **Use MobileDeviceConnection scope** - All mobile activities must be inside this container
2. **Configure Appium capabilities** - Set platformName, deviceName, app path, etc.
3. **Perform mobile actions** - Use UI automation, device interaction, and app management activities
4. **Handle connection lifecycle** - The scope manages connection open/close automatically

## Example Workflow Structure

```xml
<ma:MobileDeviceConnection DisplayName="Mobile Device Connection"
                          AppiumUrl="http://127.0.0.1:4723/wd/hub"
                          OutputConnection="[mobileDevice]">
  <ma:MobileDeviceConnection.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="platformName">Android</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="deviceName">Android Emulator</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="app">C:\apps\myapp.apk</InArgument>
    </scg:Dictionary>
  </ma:MobileDeviceConnection.Arguments>

  <ma:MobileDeviceConnection.Body>
    <!-- Your mobile automation activities here -->
    <ma:Tap Target="{maui:Target}" />
    <ma:SetText Target="{maui:Target}" Text="Hello Mobile" />
    <ma:GetText Target="{maui:Target}" Result="[textValue]" />
  </ma:MobileDeviceConnection.Body>
</ma:MobileDeviceConnection>
```

## Platform Support

Most activities work on both **Android** and **iOS**, but some features may be platform-specific:

- **DrawPattern** - Android only (pattern lock)
- **PressHardwareButton** - Some buttons are platform-specific (e.g., Android Back button)
- Appium capabilities and element selectors differ between platforms

## Notes

- **Namespace prefix**: Mobile Automation activities use the `ma:` XML namespace prefix in XAML
- **Appium version compatibility**: This package is compatible with Appium 1.x and 2.x servers
- **Target resolution**: Mobile UI elements are typically targeted using descriptors generated by the UiPath Mobile Device Manager
- **Computer Vision support**: Activities support CV-based targeting as an alternative to native element selectors
- **Resource keys**: Some activity display names in the generated docs show resource keys (e.g., "ActivityNameXxx") instead of friendly names. Refer to UiPath Studio's activity panel for correct display names.

## Additional Resources

- [Appium Documentation](http://appium.io/docs)
- [Appium Desired Capabilities](http://appium.io/docs/en/writing-running-appium/caps)
- UiPath Mobile Automation Guide (check UiPath documentation portal)
