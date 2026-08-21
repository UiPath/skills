# For Each Email

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.ForEachEmailConnections`

Iterates over a collection of emails in a specified mail folder. Supports filtering by read status, attachments, importance, and includes options for subfolder inclusion and marking emails as read during iteration.

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
| `MaxResults` | Max Results | Options | `InArgument<int>` | No | `100` | The maximum number of emails to iterate over. Values less than or equal to zero return all results. |
| `UnreadOnly` | Unread Only | Options | `InArgument<bool>` | No | `False` | Retrieve only unread emails. |
| `WithAttachmentsOnly` | With Attachments Only | Options | `InArgument<bool>` | No | `False` | Retrieve only emails with attachments. |
| `MarkAsRead` | Mark As Read | Options | `InArgument<bool>` | No | `False` | Indicates whether to mark each email as read during iteration. |
| `Importance` | Importance | Options | `InArgument<ImportanceFilter>` | No | `Any` | Filter by email importance. |
| `Filter` | Filter | | [`MailFilterCollection`](filtering/MailFilterCollection.md) | | | Condition-based filter. See [MailFilterCollection](filtering/MailFilterCollection.md). |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Length` | Length | Output | `OutArgument<int>` | The number of emails processed. |

## Output Model

Each iteration provides a [`Office365Message`](types/Office365Message.md) as `CurrentEmail` and an `int` as `CurrentEmailIndex`.

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
    xmlns:umo365="clr-namespace:UiPath.MicrosoftOffice365.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umam:ForEachEmailConnections
    ConnectionId="{x:Null}"
    MarkAsRead="False" MaxResults="50" UnreadOnly="True"
    DisplayName="For Each Email">
  <umam:ForEachEmailConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umame:FilterMode" StoredValue="ConditionBuilder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umame:FilterMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umam:ForEachEmailConnections.FilterSelectionBackup>
  <umam:ForEachEmailConnections.MailFolderArgument>
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
  </umam:ForEachEmailConnections.MailFolderArgument>
  <umam:ForEachEmailConnections.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:ForEachEmailConnections.MailboxArg>
  <umam:ForEachEmailConnections.Body>
    <ActivityAction x:TypeArguments="umo365:Office365Message, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="umo365:Office365Message" Name="CurrentEmail" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentEmailIndex" />
      </ActivityAction.Argument2>
      <!-- Activities to execute for each email go here -->
    </ActivityAction>
  </umam:ForEachEmailConnections.Body>
</umam:ForEachEmailConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Body` property contains a sequence of activities executed for each email in the iteration.
- Current item variable name defaults to `CurrentEmail` and current index to `CurrentEmailIndex`.
