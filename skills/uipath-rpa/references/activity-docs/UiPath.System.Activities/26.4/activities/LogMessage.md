# Log Message

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
<ui:LogMessage Level="Info" Message="Processing started" />
```

## Notes

- `Level` is a project-level setting; the default (`Info`) can be changed project-wide in Studio project settings.
- Messages logged here are visible both in the Studio Output panel and in the Orchestrator Logs page when running attended or unattended.
