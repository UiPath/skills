# Set Device GeoLocation

`UiPath.MobileAutomation.Activities.SetDeviceGeoLocation`

Set Device GeoLocation

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Latitude` | Latitude | InArgument | `double` | Yes | | Latitude coordinate |
| `Longitude` | Longitude | InArgument | `double` | Yes | | Longitude coordinate |
| `Altitude` | Set Device GeoLocation | InArgument | `double` | | `0` | Altitude in meters |

## XAML Example

```xml
<ma:SetDeviceGeoLocation DisplayName="Set Device GeoLocation"
                         Latitude="[37.7749]"
                         Longitude="[-122.4194]"
                         Altitude="[10.0]" />
```

## Notes

- This activity sets the GPS location of the mobile device
- Latitude and Longitude are required, Altitude is optional (default: 0)
- Useful for testing location-based features without physical movement
- The device must support GPS simulation or location mocking
- Some apps may require location services to be enabled
- Must be used within a Mobile Device Connection scope
