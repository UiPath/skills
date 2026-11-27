# Swipe

`UiPath.MobileAutomation.Activities.Swipe`

Swipe

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | | | Target element selector (optional - swipes screen if not specified) |
| `Direction` | Swipe | InArgument | `SwipeDirectionEnum` | Yes | | Swipe direction |

## Enum Reference

**`SwipeDirectionEnum`**: `Up`, `Down`, `Left`, `Right`

## XAML Example

```xml
<ma:Swipe DisplayName="Swipe"
          Direction="Up"
          Selector="[&quot;&lt;mobile class='android.widget.ScrollView' /&gt;&quot;]" />
```

## Notes

- This activity performs a swipe gesture on the screen or on a specific element
- Available directions: Up, Down, Left, Right
- If Selector is provided, the swipe is performed on that specific element
- If Selector is not provided, the swipe is performed on the entire screen
- Useful for scrolling lists, switching between screens, or revealing hidden UI elements
- Must be used within a Mobile Device Connection scope
