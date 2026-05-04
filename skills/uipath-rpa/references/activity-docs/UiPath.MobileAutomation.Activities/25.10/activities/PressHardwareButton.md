# Press Hardware Button

`UiPath.MobileAutomation.Activities.PressHardwareButton`

Press Hardware Button

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Hardware Interaction

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Button` | Press Hardware Button | InArgument | `HardwareButton` | Yes | | Press Hardware Button |

## Enum Reference

**`HardwareButton`**: `Home`, `Back`, `Menu`, `VolumeUp`, `VolumeDown`, `Power`, `Camera`, `Search`

## XAML Example

```xml
<ma:PressHardwareButton DisplayName="Press Hardware Button"
                        Button="Back" />
```

## Notes

- This activity simulates pressing a hardware button on the mobile device
- Available buttons depend on the device platform:
  - **Android**: Home, Back, Menu, VolumeUp, VolumeDown, Power, Camera, Search
  - **iOS**: Home, VolumeUp, VolumeDown, Power (limited button support)
- Not all buttons may be available on all devices
- The Power button behavior may vary by device and platform
- Must be used within a Mobile Device Connection scope
