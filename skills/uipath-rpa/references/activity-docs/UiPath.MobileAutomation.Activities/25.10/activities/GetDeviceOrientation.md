# Get Device Orientation

`UiPath.MobileAutomation.Activities.GetDeviceOrientation`

Get the current device orientation

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Orientation` | Get Device Orientation | `ScreenOrientation` | Get the current device orientation |

## Enum Reference

**`ScreenOrientation`**: `Portrait`, `Landscape`

## XAML Example

```xml
<ma:GetDeviceOrientation DisplayName="Get Device Orientation"
                         Orientation="[deviceOrientation]" />
```

## Notes

- This activity retrieves the current orientation of the mobile device screen
- Returns either Portrait or Landscape orientation
- Useful for implementing orientation-specific automation logic
- Must be used within a Mobile Device Connection scope
