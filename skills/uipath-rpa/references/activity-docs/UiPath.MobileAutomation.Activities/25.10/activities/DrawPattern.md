# ActivityNameDrawPattern

`UiPath.MobileAutomation.Activities.DrawPattern`

Create finger paths using input points that will be executed on the screen device.

**Package:** `UiPath.MobileAutomation.Activities`
**Category:** UI Automation

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `PointX` | Point X | InArgument | `double` | | | X coordinate for the touch point |
| `PointY` | Point Y | InArgument | `double` | | | Y coordinate for the touch point |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `CoordinatesType` | CoordinatesType | `CoordinatesTypeEnum` | | Whether the dimensions should be described in device independent or physical (real) device pixels |
| `PointOperations` | Point Operations | `List<PointOperation>` | | List of point operations defining the pattern |

## Enum Reference

**`CoordinatesTypeEnum`**: `DeviceIndependent`, `Physical`

## XAML Example

```xml
<ma:DrawPattern DisplayName="Draw Pattern"
                CoordinatesType="DeviceIndependent">
  <ma:DrawPattern.PointOperations>
    <!-- Define point operations for the pattern -->
  </ma:DrawPattern.PointOperations>
</ma:DrawPattern>
```

## Notes

- This activity creates complex finger paths using multiple input points
- Device independent pixels are recommended for multi-device automation as they are more reliable
- Physical pixels represent the true resolution of the screen and differ per device
- Useful for creating custom gestures, drawing patterns (like unlock patterns), or complex touch sequences
- Must be used within a Mobile Device Connection scope
