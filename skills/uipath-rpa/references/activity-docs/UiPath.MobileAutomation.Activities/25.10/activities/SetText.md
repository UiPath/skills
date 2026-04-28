# Set Text

`UiPath.MobileAutomation.Activities.SetText`

Set Text

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Interaction

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Target` | Target | InArgument | `TargetElement` | Yes | | The target element to set text in |
| `Text` | Set Text | InArgument | `string` | Yes | | Set Text |
| `ClearBeforeTyping` | Clear Before Typing | Property | `bool` | | `true` | Clear the field before entering text |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ClearBeforeTyping` | Clear Before Typing | `bool` | `true` | Clear the field before entering text |

## XAML Example

```xml
<ma:SetText DisplayName="Set Text"
            Text="[&quot;example@email.com&quot;]"
            ClearBeforeTyping="True">
  <ma:SetText.Target>
    <ma:TargetElement Selector="&lt;mobile id='email_input' /&gt;" />
  </ma:SetText.Target>
</ma:SetText>
```

## Notes

- This activity enters text into a mobile input field
- When ClearBeforeTyping is True, the existing text is cleared before entering new text
- When ClearBeforeTyping is False, the new text is appended to existing text
- The target element must be an editable field (text input, text area, etc.)
- Must be used within a Mobile Device Connection scope
