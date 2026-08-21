# Wait For Email Received

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.WaitForEmailReceived`

Suspends workflow execution and waits until a new email is received in the specified mail folder. This is a persistent (long-running) activity.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `MailFolderArgument` | Mail Folder | | [`MailFolderArgument`](components/MailFolderArgument.md) | No | | Specifies the mail folder to monitor for new emails. See [MailFolderArgument](components/MailFolderArgument.md) for input modes. |
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use. See [MailboxArgument](components/MailboxArgument.md) for input modes. |
| `MarkAsRead` | Mark As Read | Options | `InArgument<bool>` | No | `False` | Indicates whether to mark the retrieved email as read. |
| `WithAttachmentsOnly` | With Attachments Only | | `InArgument<bool>` | No | `False` | Retrieve only emails with attachments. |
| `IncludeAttachments` | Include Attachments | | `InArgument<bool>` | No | `False` | Indicates if the email should contain the attachments. |

## Output Model

The activity returns an [`Office365Message`](types/Office365Message.md) as its result.

See [`Office365Message`](types/Office365Message.md) for the email object structure.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umo="clr-namespace:UiPath.MicrosoftOffice365.Activities;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umamm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umo:WaitForEmailReceived
    MarkAsRead="True" WithAttachmentsOnly="False" IncludeAttachments="False"
    DisplayName="Wait For Email Received">
  <umo:WaitForEmailReceived.MailFolderArgument>
    <umamm:MailFolderArgument SelectionMode="EnterPath">
      <umamm:MailFolderArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:ItemSelectionMode" StoredValue="EnterPath">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:ItemSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailFolderArgument.Backup>
      <umamm:MailFolderArgument.ManualEntryFolder>
        <InArgument x:TypeArguments="x:String">["Inbox"]</InArgument>
      </umamm:MailFolderArgument.ManualEntryFolder>
    </umamm:MailFolderArgument>
  </umo:WaitForEmailReceived.MailFolderArgument>
  <umo:WaitForEmailReceived.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umo:WaitForEmailReceived.MailboxArg>
</umo:WaitForEmailReceived>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- This is a persistent activity that suspends workflow execution until the trigger fires.
- Supports filtering via the `Filter` property (condition builder with variables).
- In debug mode, retrieves the most recent matching email instead of waiting.
