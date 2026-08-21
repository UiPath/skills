# Report Status

`UiPath.Core.Activities.ReportStatus`

Displays a custom status in the UiPath Assistant for the process that is running.

**Package:** `UiPath.System.Activities`
**Category:** Logging

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| StatusMessage | Status Message | InArgument | `string` | Yes | — | The message to display as the current job status in UiPath Assistant. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:ReportStatus StatusMessage="Extracting invoice data..." />
```

## Notes

- Status messages appear in the UiPath Assistant job panel in real time while the robot is running.
- This activity sends the status to Orchestrator, which relays it to the connected Assistant instance.
- Has no effect when running outside of an Orchestrator-connected context.
