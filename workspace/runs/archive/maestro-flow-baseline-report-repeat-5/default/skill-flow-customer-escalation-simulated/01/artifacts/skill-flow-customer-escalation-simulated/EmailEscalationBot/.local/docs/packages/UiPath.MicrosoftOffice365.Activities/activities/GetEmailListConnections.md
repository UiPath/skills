# Get Email List

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.GetEmailListConnections`

Gets the list of emails within a mail folder. Supports filtering by read status, attachments, importance, and includes options for subfolder inclusion and marking retrieved emails as read.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `MailFolderArgument` | Mail Folder | | [`MailFolderArgument`](components/MailFolderArgument.md) | No | | Specifies the mail folder to target. See [MailFolderArgument](components/MailFolderArgument.md) for input modes. |
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use. See [MailboxArgument](components/MailboxArgument.md) for input modes. |
| `IncludeSubfolders` | Include Subfolders | Input | `InArgument<bool>` | No | `False` | Include subfolders or not. |
| `MaxResults` | Max Results | Options | `InArgument<int>` | No | `100` | The maximum number of emails to retrieve. Values less than or equal to zero return all results. |
| `UnreadOnly` | Unread Only | Options | `InArgument<bool>` | No | `False` | Retrieve only unread emails. |
| `WithAttachmentsOnly` | With Attachments Only | Options | `InArgument<bool>` | No | `False` | Retrieve only emails with attachments. |
| `MarkAsRead` | Mark As Read | Options | `InArgument<bool>` | No | `False` | Indicates whether to mark retrieved emails as read after fetching them. |
| `Importance` | Importance | Options | `InArgument<ImportanceFilter>` | No | `Any` | Filter by email importance. |
| `Filter` | Filter | | [`MailFilterCollection`](filtering/MailFilterCollection.md) | | | Condition-based filter. See [MailFilterCollection](filtering/MailFilterCollection.md). |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `EmailList` | Email List | Output | `OutArgument<List<`[`Office365Message`](types/Office365Message.md)`>>` | The processed email list. |

## Output Model

See [`Office365Message`](types/Office365Message.md) for the email object structure.

## Enum Reference

| Enum | Values |
|---|---|
| `ImportanceFilter` | `Any`, `Low`, `Normal`, `High` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umamm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umam:GetEmailListConnections
    ConnectionId="{x:Null}"
    MarkAsRead="False" MaxResults="50" EmailList="[emails]" UnreadOnly="True"
    DisplayName="Get Email List">
  <umam:GetEmailListConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umame:FilterMode" StoredValue="ConditionBuilder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umame:FilterMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umam:GetEmailListConnections.FilterSelectionBackup>
  <umam:GetEmailListConnections.MailFolderArgument>
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
  </umam:GetEmailListConnections.MailFolderArgument>
  <umam:GetEmailListConnections.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:GetEmailListConnections.MailboxArg>
</umam:GetEmailListConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Default MaxResults is 100. Set to 0 or a negative value to retrieve all emails.
- The activity supports server-side filtering via condition builder, free text, or OData query.
