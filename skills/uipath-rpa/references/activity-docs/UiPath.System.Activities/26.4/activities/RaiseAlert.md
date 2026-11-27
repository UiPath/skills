# Raise Alert

`UiPath.Core.Activities.RaiseAlert`

Helps you add custom alerts in Orchestrator, with a selected severity.

**Package:** `UiPath.System.Activities`
**Category:** Alerts

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Notification` | Notification | InArgument | `string` | Yes | — | The alert message text to display in Orchestrator. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Severity` | Severity | `AlertSeverity` | — | The severity level of the alert. Controls how it is displayed and filtered in Orchestrator. |

### Enum Reference

**AlertSeverity**

| Value | Description |
|-------|-------------|
| `Info` | Informational alert. Used for general operational messages. |
| `Warn` | Warning alert. Used for non-critical conditions that may require attention. |
| `Error` | Error alert. Used for conditions that indicate a processing failure. |
| `Fatal` | Fatal alert. Used for critical conditions that require immediate attention. |

## XAML Example

```xml
<ui:RaiseAlert
    Notification="&quot;Invoice processing completed with warnings.&quot;"
    Severity="Warn"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Alerts created by this activity appear in the **Alerts** section of Orchestrator and can trigger notification rules configured in Orchestrator.
- This activity does not stop or affect workflow execution — it only sends the alert to Orchestrator.
