# Set Outlook Desktop Mail Categories

`UiPath.Mail.Outlook.Activities.SetOutlookMailCategories`

Associates categories with a mail message.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The message to associate with the specified categories. |
| Categories | Categories | InArgument | string[] | No | | The categories to add to this message. If empty, it clears all categories. |

## XAML Example

```xml
<olm:SetOutlookMailCategories
    MailMessage="[mailMessage]"
    Categories="[new String() {&quot;Red Category&quot;, &quot;Blue Category&quot;}]" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- Passing an empty or null `Categories` array clears all existing categories from the message
- Category names must match categories defined in Outlook; unrecognized names are ignored
- Related activities: GetOutlookMailMessages, MarkOutlookMailAsRead
