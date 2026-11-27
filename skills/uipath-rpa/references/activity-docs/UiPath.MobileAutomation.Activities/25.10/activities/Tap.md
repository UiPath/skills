# Tap

`UiPath.MobileAutomation.Activities.Tap`

Tap

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Selector` | Selector | InArgument | `string` | Yes | | Target element selector |
| `TapCount` | Tap | InArgument | `int` | | `1` | Number of taps to perform |

## XAML Example

```xml
<ma:Tap DisplayName="Tap"
        Selector="[&quot;&lt;mobile id='submit_button' /&gt;&quot;]"
        TapCount="[1]" />
```

## Notes

- This activity performs a tap (click/touch) action on a mobile UI element
- TapCount specifies the number of consecutive taps (default: 1)
- Use TapCount=2 for double-tap gestures
- The element must be visible and interactive
- Must be used within a Mobile Device Connection scope
