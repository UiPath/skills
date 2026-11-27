# Set Device Orientation

`UiPath.MobileAutomation.Activities.SetDeviceOrientation`

Set device orientation

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Orientation` | Set Device Orientation | InArgument | `ScreenOrientation` | Yes | | Set device orientation |

## Enum Reference

**`ScreenOrientation`**: `Portrait`, `Landscape`

## XAML Example

```xml
<ma:SetDeviceOrientation DisplayName="Set Device Orientation"
                         Orientation="Landscape" />
```

## Notes

- This activity changes the orientation of the mobile device screen
- Available orientations: Portrait or Landscape
- The device must support orientation changes for this activity to work
- Must be used within a Mobile Device Connection scope
