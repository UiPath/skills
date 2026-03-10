# XAML Outlook Mail Activities

Office 365 Outlook mail activity patterns for `UiPath.MicrosoftOffice365.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed namespace and attribute patterns from real workflows only.

## Package

`UiPath.MicrosoftOffice365.Activities`

## Key Email Type

`umm:Office365Message` — output of `GetNewestEmail` and `NewEmailReceived`; input to `DownloadEmailAttachments`.

```xml
<Variable x:TypeArguments="umm:Office365Message" Name="email" />
```

## Connection Pattern

All activities authenticate via:
```xml
ConnectionId="<guid>" UseConnectionService="True" AuthScopesInvalid="False"
```

Use `uipcli is connections list --format json` to obtain the connection GUID. If no O365 connection exists, create one: `uipcli is connections create <o365-connector-key>`. Verify it's active: `uipcli is connections ping <connection-id>`.

## Activities

### SendMailConnections — Send Email

Null attributes: `ArgumentAttachmentPaths`, `AttachmentList`, `Bcc`, `Cc`, `ConnectionAccountName`, `ContinueOnError`

```xml
<umam:SendMailConnections
    ArgumentAttachmentPaths="{x:Null}"
    AttachmentList="{x:Null}"
    Bcc="{x:Null}"
    Cc="{x:Null}"
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    AttachmentInputMode="Existing"
    AuthScopesInvalid="False"
    Body="[emailBody]"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Send Email"
    InputType="HTML"
    Subject="[emailSubject]"
    UseConnectionService="True"
    UseSharedMailbox="False">
  <!-- Recipients: IEnumerable<string> -->
  <umam:SendMailConnections.To>
    <InArgument x:TypeArguments="scg:IEnumerable(x:String)">
      <CSharpValue x:TypeArguments="scg:IEnumerable(x:String)">new string[]{"user@example.com"}</CSharpValue>
    </InArgument>
  </umam:SendMailConnections.To>
  <!-- BackupSlot children required for enum properties -->
  <umam:SendMailConnections.MailboxArg>
    <umamm:MailboxArgument SharedMailbox="{x:Null}" UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:SendMailConnections.MailboxArg>
</umam:SendMailConnections>
```

Additional BackupSlot children (get full structure from `uipcli rpa get-default-activity-xaml`):
- `AttachmentsArg` — type `umame:AttachmentInputMode`
- `InputTypeArg` — type `umame:BodyInputType`

### GetNewestEmail — Retrieve Single Email

Null attributes: `ConnectionAccountName`, `ContinueOnError`

```xml
<umam:GetNewestEmail
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    AuthScopesInvalid="False"
    BodyAsHtml="False"
    BrowserFolder="Inbox"
    BrowserFolderId="Inbox"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Get Newest Email"
    FilterSelectionMode="ConditionBuilder"
    Importance="Any"
    MarkAsRead="False"
    Result="[email]"
    SelectionMode="Browse"
    UnreadOnly="False"
    UseConnectionService="True"
    UseSharedMailbox="False"
    WithAttachmentsOnly="False">
  <!-- Optional filter -->
  <umam:GetNewestEmail.Filter>
    <umamf:MailFilterCollection LogicalOperator="And">
      <umamf:MailFilterCollection.Filters>
        <umamf:MailFilterElement
            DateValue="{x:Null}"
            Criteria="Subject"
            StringOperator="Contains"
            InStringValue="[keyword]" />
      </umamf:MailFilterCollection.Filters>
    </umamf:MailFilterCollection>
  </umam:GetNewestEmail.Filter>
</umam:GetNewestEmail>
```

Output type: `umm:Office365Message`

### DownloadEmailAttachments — Extract Attachments

Null attributes: `ConnectionAccountName`, `ContinueOnError`, `Filter`, `FilterByFileNames`, `NewResult`

```xml
<umam:DownloadEmailAttachments
    ConnectionAccountName="{x:Null}"
    ContinueOnError="{x:Null}"
    Filter="{x:Null}"
    FilterByFileNames="{x:Null}"
    NewResult="{x:Null}"
    AuthScopesInvalid="False"
    ConnectionId="00000000-0000-0000-0000-000000000000"
    DisplayName="Download Email Attachments"
    Email="[email]"
    ExcludeInlineAttachments="True"
    Result="[attachmentPaths]"
    SearchMode="UseSimple"
    UseConnectionService="True" />
```

- `Email`: binds a `umm:Office365Message` variable
- `Result`: `IEnumerable<string>` — saved attachment file paths
- `SearchMode`: `"UseSimple"` is the standard value

### NewEmailReceived — Trigger on Incoming Email

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

#### FilterExpression Examples

| Filter | Expression |
|--------|-----------|
| Inbox only | `(parentFolderId=='INBOX')` |
| Has attachments | `(hasAttachments==\`true\`)` |
| Inbox + attachments | `(parentFolderId=='INBOX')&amp;&amp;(hasAttachments==\`true\`)` |
| Unread only | `(isRead==\`false\`)` |

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Connection | `ConnectionId="<guid>" UseConnectionService="True" AuthScopesInvalid="False"` |
| `umm:` assembly | `assembly=UiPath.MicrosoftOffice365` — NOT `...Activities` |
| Trigger prefix | `umamt:NewEmailReceived` — requires `xmlns:umamt=...Mail.Triggers...` |
| Filter prefix | `umamf:MailFilterCollection` / `umamf:MailFilterElement` — requires `xmlns:umamf=...Mail.Filters...` |
| Email variable type | `umm:Office365Message` — used for `Result` in `GetNewestEmail`/`NewEmailReceived`; `Email` in `DownloadEmailAttachments` |
| Recipients | `<CSharpValue x:TypeArguments="scg:IEnumerable(x:String)">new string[]{"a@b.com"}</CSharpValue>` |
| FilterExpression booleans | Backtick-quoted: `` `true` ``, `` `false` `` |
| FilterExpression AND | `&amp;&amp;` (XML-escaped `&&`) |
| BackupSlot (SendMail) | `MailboxArg` child required; `AttachmentsArg` and `InputTypeArg` also needed — use `uipcli rpa get-default-activity-xaml` for full structure |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
