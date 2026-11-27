# Get Attribute

`UiPath.MobileAutomation.Activities.GetAttribute`

Get Attribute

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |
| `AttributeName` | Attribute Name | InArgument | `string` | Yes | | Get Attribute |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Value` | Value | `string` | Value of the specified attribute |

## XAML Example

```xml
<ma:GetAttribute DisplayName="Get Attribute"
                 Selector="[&quot;&lt;mobile id='username_field' /&gt;&quot;]"
                 AttributeName="[&quot;text&quot;]"
                 Value="[attributeValue]" />
```

## Notes

- This activity retrieves the value of a specified attribute from a mobile UI element
- Common attributes include: `text`, `name`, `value`, `enabled`, `displayed`, `selected`, `resource-id`, `content-desc`
- The available attributes depend on the platform (Android/iOS) and element type
- Returns the attribute value as a string
- If the attribute doesn't exist, the behavior depends on the Appium version
- Must be used within a Mobile Device Connection scope
