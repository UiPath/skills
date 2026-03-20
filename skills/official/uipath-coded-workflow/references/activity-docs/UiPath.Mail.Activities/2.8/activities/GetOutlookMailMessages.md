# GetOutlookMailMessages — Retrieve Emails

Null attributes: `Account`, `Filter`, `FilterByMessageIds`, `TimeoutMS`. Set `Messages` to a variable to capture output.

```xml
<ui:GetOutlookMailMessages
    Account="{x:Null}"
    Filter="{x:Null}"
    FilterByMessageIds="{x:Null}"
    TimeoutMS="{x:Null}"
    DisplayName="Get unread Outlook emails"
    GetAttachements="False"
    MailFolder="Inbox"
    MarkAsRead="False"
    Messages="[Emails]"
    OnlyUnreadMessages="True"
    OrderByDate="NewestFirst"
    Top="30" />
```

- `Messages`: `scg:List(snm:MailMessage)` output variable
- `MailFolder`: folder name string (e.g., `"Inbox"`)
- `GetAttachements`: `"False"` to skip downloading attachments (faster); `"True"` to include them
- `Top`: number of messages to retrieve
- `OrderByDate`: `"NewestFirst"` or `"OldestFirst"`
- `OnlyUnreadMessages`: `"True"` or `"False"`
