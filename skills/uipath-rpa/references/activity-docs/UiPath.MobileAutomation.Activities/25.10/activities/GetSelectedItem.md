# Get Selected Item

`UiPath.MobileAutomation.Activities.GetSelectedItem`

Get Selected Item

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
| `SelectedItem` | Get Selected Item | `string` | Get Selected Item |

## XAML Example

```xml
<ma:GetSelectedItem DisplayName="Get Selected Item"
                    Selector="[&quot;&lt;mobile class='android.widget.Spinner' /&gt;&quot;]"
                    SelectedItem="[selectedValue]" />
```

## Notes

- This activity retrieves the currently selected item from a selection element (dropdown, spinner, picker, etc.)
- Returns the text of the selected item as a string
- Useful for dropdowns, spinners, pickers, and other selection controls
- The element must support selection operations
- Must be used within a Mobile Device Connection scope
