# Set Selected Item

`UiPath.MobileAutomation.Activities.SetSelectedItem`

Set Selected Item

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |
| `Item` | Set Selected Item | InArgument | `string` | Yes | | Set Selected Item |

## XAML Example

```xml
<ma:SetSelectedItem DisplayName="Set Selected Item"
                    Selector="[&quot;&lt;mobile class='android.widget.Spinner' /&gt;&quot;]"
                    Item="[&quot;Option 2&quot;]" />
```

## Notes

- This activity selects an item from a selection element (dropdown, spinner, picker, etc.)
- The Item parameter specifies the text of the item to select
- Works with dropdowns, spinners, pickers, and other selection controls
- The element must support selection operations
- If the item is not found in the list, an exception is thrown
- Must be used within a Mobile Device Connection scope
