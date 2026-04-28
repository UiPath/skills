# Get Log Types

`UiPath.MobileAutomation.Activities.GetLogTypes`

Get all available log types for a session

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Logging & Debugging

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `LogTypes` | Get Log Types | `string[]` | Get all available log types for a session |

## XAML Example

```xml
<ma:GetLogTypes DisplayName="Get Log Types" LogTypes="[logTypesArray]" />
```

## Notes

- This activity retrieves all available log types that can be used with the Get Logs activity
- Must be used within a Mobile Device Connection scope
- The output is an array of strings containing the available log type names
