# XAML Outlook Mail Activities (UiPath.Mail.Activities)

Classic Outlook mail activity patterns for `UiPath.Mail.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed namespace and attribute patterns from real workflows only. **Not for `UiPath.MicrosoftOffice365.Activities`** — see `msoffice365-outlook-activities.md` for O365.

## Package

`UiPath.Mail.Activities`

## Two Distinct Styles

| Style | Namespace prefix | Scope required | Activities |
|-------|-----------------|---------------|------------|
| **Classic** (`ui:`) | `xmlns:ui="http://schemas.uipath.com/workflow/activities"` | No — standalone | `GetOutlookMailMessages`, `MoveOutlookMessage`, `SaveMailAttachments`, `SendOutlookMail` |
| **Modern** (`umab:`) | `xmlns:umab="clr-namespace:UiPath.Mail.Activities.Business;assembly=UiPath.Mail.Activities"` | Yes — `OutlookApplicationCard` | `ForEachEmailX` |

## Key Email Type

`System.Net.Mail.MailMessage` — output of `GetOutlookMailMessages`; iterator item in `ForEach` / `ForEachEmailX`.

```xml
<!-- Variable holding a list of messages -->
<Variable x:TypeArguments="scg:List(snm:MailMessage)" Name="Emails" />

<!-- ForEach type argument -->
<ui:ForEach x:TypeArguments="snm:MailMessage" Values="[Emails]">
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="snm:MailMessage">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="snm:MailMessage" Name="currentEmail" />
      </ActivityAction.Argument>
      ...
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>
```

## IS Connection Pattern (Classic activities)

When using Integration Service connection, add `UseISConnection="True"` and the `ConnectionDetailsBackupSlot` child to `GetOutlookMailMessages` and `SendOutlookMail`. Use `uipcli is connections list --format json` to discover available connection GUIDs. If no Outlook connection exists, create one: `uipcli is connections create <outlook-connector-key>`.

```xml
<ui:GetOutlookMailMessages ... UseISConnection="True">
  <ui:GetOutlookMailMessages.ConnectionDetailsBackupSlot>
    <usau:BackupSlot x:TypeArguments="umae:ConnectionDetails" StoredValue="{x:Null}">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umae:ConnectionDetails, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </ui:GetOutlookMailMessages.ConnectionDetailsBackupSlot>
</ui:GetOutlookMailMessages>
```

Without IS connection, omit `UseISConnection` and the child element entirely.

## Classic Activities (ui:)

### GetOutlookMailMessages — Retrieve Emails

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

### MoveOutlookMessage — Move Email to Folder

Null attribute: `Account`.

```xml
<ui:MoveOutlookMessage
    Account="{x:Null}"
    DisplayName="Move email to Invoices folder"
    MailFolder="Invoices"
    MailMessage="[currentEmail]" />
```

- `MailMessage`: binds a `snm:MailMessage` variable (e.g., loop iterator)
- `MailFolder`: destination folder name

### SaveMailAttachments — Save Attachments to Disk

Null attributes: `Attachments`, `ResourceAttachments`.

```xml
<ui:SaveMailAttachments
    Attachments="{x:Null}"
    ResourceAttachments="{x:Null}"
    DisplayName="Download attachments to folder"
    ExcludeInlineAttachments="False"
    FolderPath="[DestinationFolderPath]"
    Message="[currentEmail]"
    OverwriteExisting="False" />
```

- `Message`: binds a `snm:MailMessage` variable
- `FolderPath`: destination directory path
- `ExcludeInlineAttachments`: `"True"` to skip embedded images

### SendOutlookMail — Send Email via Outlook

Null attributes: `Account`, `Bcc`, `Cc`, `ContinueOnError`, `MailMessage`, `ReplyTo`, `TimeoutMS`.

```xml
<ui:SendOutlookMail
    Account="{x:Null}"
    Bcc="{x:Null}"
    Cc="{x:Null}"
    ContinueOnError="{x:Null}"
    MailMessage="{x:Null}"
    ReplyTo="{x:Null}"
    TimeoutMS="{x:Null}"
    Body="[EmailBody]"
    DisplayName="Send Outlook email"
    Importance="Normal"
    IsBodyHtml="False"
    IsDraft="False"
    Sensitivity="Normal"
    Subject="[EmailSubject]"
    To="[recipientAddress]"
    UseISConnection="True">
  <ui:SendOutlookMail.ConnectionDetailsBackupSlot>
    <usau:BackupSlot x:TypeArguments="umae:ConnectionDetails" StoredValue="{x:Null}">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umae:ConnectionDetails, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </ui:SendOutlookMail.ConnectionDetailsBackupSlot>
  <ui:SendOutlookMail.Files>
    <scg:List x:TypeArguments="InArgument(x:String)" Capacity="0" />
  </ui:SendOutlookMail.Files>
</ui:SendOutlookMail>
```

- `To`: string recipient address
- `Files`: child element — empty list when no attachments; populate with `InArgument(x:String)` items for attachments
- `Importance`: `"Normal"`, `"High"`, or `"Low"`
- `Sensitivity`: `"Normal"`, `"Personal"`, `"Private"`, or `"CompanyConfidential"`

## Modern Activities (umab:) — Scope Required

### OutlookApplicationCard — Scope Container

All `umab:` activities must be nested inside `OutlookApplicationCard`. The scope handle type is `um:IMailQuickHandle`.

```xml
<umab:OutlookApplicationCard
    Account="user@example.com"
    AccountMismatchBehavior="UseDefaultEmailAccount"
    DisplayName="Open the Outlook desktop application">
  <umab:OutlookApplicationCard.Body>
    <ActivityAction x:TypeArguments="um:IMailQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="um:IMailQuickHandle" Name="Outlook" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested umab: activities here -->
      </Sequence>
    </ActivityAction>
  </umab:OutlookApplicationCard.Body>
</umab:OutlookApplicationCard>
```

The delegate argument name is `"Outlook"` by convention. Folder references use `Outlook.Folder("FolderName")`.

### ForEachEmailX — Iterate Emails in Folder

Requires **two** delegate arguments — `Argument1` (`snm:MailMessage`) and `Argument2` (`x:Int32` index):

```xml
<umab:ForEachEmailX
    DisplayName="For Each Email in Inbox"
    IncludeSubfolders="False"
    Mails="[Outlook.Folder(&quot;Inbox&quot;)]"
    NumberOfEmailsLimit="10"
    RetrieveAttachments="False"
    UnreadOnly="False"
    WithAttachmentsOnly="False">
  <umab:ForEachEmailX.Body>
    <ActivityAction x:TypeArguments="snm:MailMessage, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="snm:MailMessage" Name="CurrentMail" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do">
        <!-- Access email: CurrentMail.Subject, CurrentMail.SenderEmailAddress(), etc. -->
      </Sequence>
    </ActivityAction>
  </umab:ForEachEmailX.Body>
  <!-- Optional filter child -->
  <umab:ForEachEmailX.MailFilter>
    <umabf:MailFilterArgument LogicalOperator="And">
      <umabf:MailFilterArgument.Filters>
        <scg:List x:TypeArguments="umabf:SingleMailFilterArgument" Capacity="1">
          <umabf:SingleMailFilterArgument
              DateEqualsFilter="{x:Null}"
              Value="{x:Null}"
              Criteria="Date"
              DateFilter="Today"
              Operator="NewerThan" />
        </scg:List>
      </umabf:MailFilterArgument.Filters>
    </umabf:MailFilterArgument>
  </umab:ForEachEmailX.MailFilter>
</umab:ForEachEmailX>
```

- `Mails`: folder reference using delegate handle (e.g., `Outlook.Folder("Inbox")`)
- `NumberOfEmailsLimit`: `"0"` = no limit
- `MailFilter="{x:Null}"` when no filter is needed (omit the child element entirely)
- Without filter: set `MailFilter="{x:Null}"` as an attribute directly on `ForEachEmailX`

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Classic prefix | `ui:` — `xmlns:ui="http://schemas.uipath.com/workflow/activities"` |
| Modern prefix | `umab:` — `xmlns:umab="clr-namespace:UiPath.Mail.Activities.Business;assembly=UiPath.Mail.Activities"` |
| Email variable type | `scg:List(snm:MailMessage)` for lists; `snm:MailMessage` for single/iterator |
| `snm:` declaration | `xmlns:snm="clr-namespace:System.Net.Mail;assembly=System.Net.Mail"` |
| IS connection (classic) | `UseISConnection="True"` + `ConnectionDetailsBackupSlot` child with `usau:BackupSlot x:TypeArguments="umae:ConnectionDetails"` |
| Without IS connection | Omit `UseISConnection` and `ConnectionDetailsBackupSlot` entirely |
| Classic ForEach | `<ui:ForEach x:TypeArguments="snm:MailMessage">` with single `DelegateInArgument` |
| Modern scope handle | `um:IMailQuickHandle` — `xmlns:um="clr-namespace:UiPath.Mail;assembly=UiPath.Mail.Activities"` |
| Modern folder ref | `Outlook.Folder("Inbox")` — uses the `DelegateInArgument` name `"Outlook"` |
| `ForEachEmailX` | Two args: `Argument1` (`snm:MailMessage` `"CurrentMail"`) + `Argument2` (`x:Int32` `"CurrentIndex"`) |
| `SaveMailAttachments` | Uses `ui:` prefix even inside modern scope — it's a classic activity |
| Email properties | `CurrentMail.Subject`, `CurrentMail.SenderEmailAddress()`, `CurrentMail.Date()`, `CurrentMail.Priority.AsText()`, `CurrentMail.Attachments.Count` |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
