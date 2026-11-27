# Type Text

`UiPath.MobileAutomation.Activities.TypeText`

Type Text

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |
| `Text` | Type Text | InArgument | `string` | Yes | | Type Text |
| `ClearText` | Clear Text | Property | `bool` | | `true` | Clear existing text before typing |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ClearText` | Clear Text | `bool` | `true` | Clear existing text before typing |

## XAML Example

```xml
<ma:TypeText DisplayName="Type Text"
             Selector="[&quot;&lt;mobile id='email_input' /&gt;&quot;]"
             Text="[&quot;user@example.com&quot;]"
             ClearText="True" />
```

## Notes

- This activity types text into a mobile input field
- When ClearText is True, existing text is cleared before typing
- When ClearText is False, new text is appended to existing text
- The target element must be an editable field (text input, text area, etc.)
- Must be used within a Mobile Device Connection scope
