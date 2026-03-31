# XAML Outlook Mail Activities (UiPath.Mail.Activities)

Classic Outlook mail activity patterns for `UiPath.Mail.Activities`. Always get full XAML from `uip rpa get-default-activity-xaml --use-studio` — this file covers confirmed namespace and attribute patterns from real workflows only. **Not for `UiPath.MicrosoftOffice365.Activities`** — see `msoffice365-outlook-activities.md` for O365.

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

When using Integration Service connection, add `UseISConnection="True"` and the `ConnectionDetailsBackupSlot` child to `GetOutlookMailMessages` and `SendOutlookMail`. Use `uip is connections list --output json` to discover available connection GUIDs. If no Outlook connection exists, create one: `uip is connections create <outlook-connector-key>`.

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
| Full XAML | Always use `uip rpa get-default-activity-xaml --use-studio` for complete activity XAML |
