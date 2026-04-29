# Element Exists

`UiPath.MobileAutomation.Activities.ElementExists`

Element Exists

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Element Exists |
| `WaitTimeout` | Wait Timeout | InArgument | `int` | | `30000` | Maximum time to wait for the element in milliseconds |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Exists` | Exists | `bool` | True if element exists, False otherwise |

## XAML Example

```xml
<ma:ElementExists DisplayName="Element Exists"
                  Selector="[&quot;&lt;mobile id='submit_button' /&gt;&quot;]"
                  WaitTimeout="[10000]"
                  Exists="[elementFound]" />
```

## Notes

- This activity checks whether a mobile UI element exists on the screen
- Returns True if the element is found within the timeout period, False otherwise
- Does not throw an exception if the element is not found
- Useful for conditional logic based on element presence
- The WaitTimeout parameter specifies maximum wait time in milliseconds
- Must be used within a Mobile Device Connection scope
