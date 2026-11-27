# Get Text

`UiPath.MobileAutomation.Activities.GetText`

Get Text

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Get Text | `string` | Get Text |

## XAML Example

```xml
<ma:GetText DisplayName="Get Text"
            Selector="[&quot;&lt;mobile id='message_label' /&gt;&quot;]"
            Text="[elementText]" />
```

## Notes

- This activity retrieves the text content of a mobile UI element
- Returns the visible text of the element as a string
- For input fields, this typically returns the current value
- For labels and text views, returns the displayed text
- Must be used within a Mobile Device Connection scope
