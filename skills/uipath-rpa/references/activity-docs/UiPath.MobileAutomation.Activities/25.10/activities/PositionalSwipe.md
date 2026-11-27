# Positional Swipe

`UiPath.MobileAutomation.Activities.PositionalSwipe`

Positional Swipe

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `StartX` | Start X | InArgument | `int` | Yes | | X coordinate of the starting point |
| `StartY` | Start Y | InArgument | `int` | Yes | | Y coordinate of the starting point |
| `EndX` | End X | InArgument | `int` | Yes | | X coordinate of the ending point |
| `EndY` | End Y | InArgument | `int` | Yes | | Y coordinate of the ending point |
| `Duration` | Positional Swipe | InArgument | `int` | | `500` | Duration of the swipe in milliseconds |

## XAML Example

```xml
<ma:PositionalSwipe DisplayName="Positional Swipe"
                    StartX="[100]"
                    StartY="[500]"
                    EndX="[100]"
                    EndY="[100]"
                    Duration="[300]" />
```

## Notes

- This activity performs a swipe gesture between two specific coordinates on the screen
- The swipe moves from (StartX, StartY) to (EndX, EndY)
- Duration controls the speed of the swipe in milliseconds (default: 500ms)
- Uses absolute screen coordinates
- Useful for custom swipe gestures or when element-based swipes are not suitable
- Must be used within a Mobile Device Connection scope
