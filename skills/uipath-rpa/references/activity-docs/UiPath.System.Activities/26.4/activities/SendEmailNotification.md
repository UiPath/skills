# Send Email Notification

`UiPath.Activities.System.Orchestrator.Mail.SendEmailNotification`

Sends an email notification via the Orchestrator API.

**Package:** `UiPath.System.Activities`
**Category:** Alerts

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Subject` | Subject | InArgument | `string` | Yes | — | The subject line of the email notification. |
| `Body` | Body | InArgument | `string` | No | — | The body content of the email. Supports rich text composition. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | No | — | The maximum time in milliseconds to wait for the activity to complete before throwing an error. Defaults to 30000 ms (30 seconds). |
| `ContinueOnError` | Continue on error | InArgument | `bool` | No | — | When true, execution continues even if the activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Recipients` | Recipients | `InArgument<IEnumerable<string>>` | — | The list of primary recipient email addresses (To). Required. |
| `Cc` | Cc | `InArgument<IEnumerable<string>>` | — | The list of carbon-copy recipient email addresses. Optional. |

## XAML Example

```xml
<ui:SendEmailNotification
    Subject="&quot;Process Completed&quot;"
    Body="&quot;The invoice processing run has finished successfully.&quot;"
    xmlns:ui="clr-namespace:UiPath.Activities.System.Orchestrator.Mail;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Email is delivered via the **Orchestrator Notification Service**. The Orchestrator instance must have email notifications configured (SMTP or SendGrid) for this activity to deliver messages.
- Unlike a direct SMTP send, this activity does not require credentials in the workflow — authentication is handled entirely by Orchestrator.
- `Recipients` is required and must contain at least one valid email address.
- This activity does not support coded workflows (`codedWorkflowSupport` is false).
