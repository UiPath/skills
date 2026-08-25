# Log Message

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`UiPath.Core.Activities.LogMessage`

Writes the specified diagnostic message at the specified level. These messages are also sent to Orchestrator and displayed in the Logs page.

**Package:** `UiPath.System.Activities`
**Category:** Logging

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Level | Level | InArgument | `LogLevel` | Yes | `LogLevel.Info` | The severity level of the log message. Configurable as a project setting. |
| Message | Message | InArgument | `object` | No | — | The text of the message to log. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## Enum Reference

### LogLevel

| Value | Description |
|-------|-------------|
| `Trace` | Finest-grained informational events |
| `Info` | Informational messages (default) |
| `Warn` | Potentially harmful situations |
| `Error` | Error events that might still allow the application to continue |
| `Fatal` | Severe error events that will presumably abort execution |

## XAML Example

```xml
<ui:LogMessage
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:ui="http://schemas.uipath.com/workflow/activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Level="Info"
    DisplayName="Log Message">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <VisualBasicValue x:TypeArguments="x:Object" ExpressionText="$&quot;Processing item {itemId}&quot;" />
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>
```

## Notes

- `Level` is a project-level setting; the default (`Info`) can be changed project-wide in Studio project settings.
- Messages logged here are visible both in the Studio Output panel and in the Orchestrator Logs page when running attended or unattended.
- The expanded property-element form matches the common activity card and converts cleanly for C# XAML projects by replacing `VisualBasicValue` with `CSharpValue`.
