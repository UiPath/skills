# Get System time

`UiPath.MobileAutomation.Activities.GetSystemTime`

Get the system time from a mobile device

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SystemTime` | Get System time | `DateTime` | Get the system time from a mobile device |

## XAML Example

```xml
<ma:GetSystemTime DisplayName="Get System Time"
                  SystemTime="[deviceTime]" />
```

## Notes

- This activity retrieves the current system time from the mobile device
- Returns a DateTime object representing the device's system time
- Useful for time-based validations or logging
- The time zone will be based on the device's configured time zone
- Must be used within a Mobile Device Connection scope
