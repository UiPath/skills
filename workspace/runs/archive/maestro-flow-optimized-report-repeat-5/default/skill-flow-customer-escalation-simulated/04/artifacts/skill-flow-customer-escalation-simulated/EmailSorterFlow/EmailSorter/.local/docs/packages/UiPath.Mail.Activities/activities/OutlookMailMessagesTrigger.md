# Outlook Desktop Mail Messages Trigger

`UiPath.Mail.Activities.Outlook.OutlookMailMessagesTrigger`

Sets up a trigger to watch for incoming/outgoing mail messages that match a certain criteria.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailFolder | Mail folder | InArgument | string | Yes | "Inbox" | The mail folder to monitor for incoming/outgoing mail messages. |
| Account | Account | InArgument | string | No | | The account used to access the mail messages. |
| From | From | InArgument | string | No | | Filter to only trigger on emails received from the specified email address(es), separated by semicolons. |
| To | To | InArgument | string | No | | Filter to only trigger on emails sent to the specified email address(es), separated by semicolons. |
| Cc | Cc | InArgument | string | No | | Filter to only trigger on emails where the specified email address(es) appear in the CC field, separated by semicolons. |
| SubjectFilter | Subject | InArgument | string | No | | A regex pattern to match against the email subject. Only emails whose subject matches the pattern will trigger the event. |
| BodyFilter | Body | InArgument | string | No | | A regex pattern to match against the email body. Only emails whose body matches the pattern will trigger the event. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| MarkAsRead | Mark as read | bool | | Specifies whether to mark as read the mail message that fires the trigger. |
| WhenOutlookIsClosed | When Outlook is closed | WhenOutlookIsClosedEnum | | Specifies how the activity behaves when Outlook application is closed. |
| Importance | Importance | Importance | `Importance.Any` | Filter to only trigger on emails with the specified importance level. Set to Any to match all importance levels. |

## XAML Example

```xml
<olm:OutlookMailMessagesTrigger
    MailFolder="Inbox"
    MarkAsRead="False">
  <olm:OutlookMailMessagesTrigger.From>
    <InArgument x:TypeArguments="x:String">sender@example.com</InArgument>
  </olm:OutlookMailMessagesTrigger.From>
</olm:OutlookMailMessagesTrigger>
```

## Notes

- Windows only -- requires Outlook COM interop
- This is a trigger activity that monitors Outlook for new messages
- The `SubjectFilter` and `BodyFilter` properties accept regex patterns for flexible matching
- Filter properties (`From`, `To`, `Cc`, `SubjectFilter`, `BodyFilter`, `Importance`) are combined with AND logic
- The `WhenOutlookIsClosed` property controls behavior when the Outlook application is not running
- Related activities: GetOutlookMailMessages
