# NewEmailReceived — Trigger on Incoming Email

Trigger activity (`umamt:` prefix). Null attributes: `ConnectionAccountName`, `ContinueOnError`, `Filter`, `JobData`, `UiPathEvent`, `UiPathEventConnector`, `UiPathEventObjectId`, `UiPathEventObjectType`

```xml
<umamt:NewEmailReceived
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    Filter="{x:Null}"
    JobData="{x:Null}"
    UiPathEvent="{x:Null}"
    UiPathEventConnector="{x:Null}"
    UiPathEventObjectId="{x:Null}"
    UiPathEventObjectType="{x:Null}"
    AuthScopesInvalid="False"
    BrowserFolderId="INBOX"
    BrowserFolderName="Inbox"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="New Email Received"
    FilterExpression="(parentFolderId=='INBOX')&amp;&amp;(hasAttachments==`true`)"
    IncludeAttachments="True"
    MarkAsRead="True"
    Result="[email]"
    UseConnectionService="True"
    WithAttachmentsOnly="True" />
```

- `BrowserFolderId`: `"INBOX"` (all-caps) — not `"Inbox"`
- `FilterExpression`: OData-style; `&amp;&amp;` is XML-escaped `&&`; booleans use backticks
- `Result`: `umm:Office365Message`

## FilterExpression Examples

| Filter | Expression |
|--------|-----------|
| Inbox only | `(parentFolderId=='INBOX')` |
| Has attachments | `(hasAttachments==\`true\`)` |
| Inbox + attachments | `(parentFolderId=='INBOX')&amp;&amp;(hasAttachments==\`true\`)` |
| Unread only | `(isRead==\`false\`)` |
