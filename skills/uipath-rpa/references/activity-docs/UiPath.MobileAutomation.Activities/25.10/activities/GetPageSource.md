# Get Page Source

`UiPath.MobileAutomation.Activities.GetPageSource`

Gets page source

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** Logging & Debugging

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `PageSourceFilePath` | Get Page Source | InArgument | `string` | Yes | | Gets page source |

## XAML Example

```xml
<ma:GetPageSource DisplayName="Get Page Source"
                  PageSourceFilePath="[&quot;C:\Logs\page_source.xml&quot;]" />
```

## Notes

- This activity captures the current page source (UI hierarchy) from the mobile device
- The page source is saved as XML to the specified file path
- Useful for debugging and understanding the UI structure of mobile applications
- Must be used within a Mobile Device Connection scope
