# Get Session Identifier

`UiPath.MobileAutomation.Activities.GetSessionIdentifier`

Get Session Identifier

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Mobile Device

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SessionId` | Get Session Identifier | `string` | Get Session Identifier |

## XAML Example

```xml
<ma:GetSessionIdentifier DisplayName="Get Session Identifier"
                         SessionId="[sessionIdentifier]" />
```

## Notes

- This activity retrieves the unique session identifier for the current Appium session
- The session ID can be used for advanced scenarios like sharing sessions or debugging
- Returns a string containing the session identifier
- Must be used within a Mobile Device Connection scope
