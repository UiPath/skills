# Reply To Email

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.ReplyToEmailConnections`

Replies to an email message using Microsoft Office 365. Supports reply-all, additional recipients, attachments, custom subject, importance, and delivery/read receipts.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Email` | Email | Input | [`InArgument<Office365Message>`](types/Office365Message.md) | Yes | | The email to reply to. |
| `Body` | Body | Input | `InArgument<string>` | No | | The body of the reply email (HTML). |
| `NewSubject` | New Subject | Input | `InArgument<string>` | No | | The new subject of the email. If left blank, the original subject is used. |
| `PreferredTimezone` | Preferred Timezone | Input | `InArgument<string>` | No | `UTC` | Preferred timezone for the whole thread. |
| `AttachmentInputMode` | Attachment Input Mode | Input | `AttachmentInputMode` | No | `Existing` | How to define the attachments. |
| `Attachments` | Attachments | Input | `InArgument<IEnumerable<IResource>>` | No | | The attachments to be sent with the reply email. |
| `ArgumentAttachments` | Attachments (Builder) | Input | `IEnumerable<InArgument<IResource>>` | No | | Individual attachment arguments. |
| `AttachmentPaths` | Attachment Paths | Input | `InArgument<IEnumerable<string>>` | No | | The file paths of the attachments. |
| `ArgumentAttachmentPaths` | Attachment Paths (Builder) | Input | `IEnumerable<InArgument<string>>` | No | | The list of file paths of the attachments. |
| `To` | To | Recipients | `InArgument<IEnumerable<string>>` | No | | Additional primary recipients of the email. |
| `Cc` | CC | Recipients | `InArgument<IEnumerable<string>>` | No | | Additional secondary recipients of the email. |
| `Bcc` | BCC | Recipients | `InArgument<IEnumerable<string>>` | No | | Additional hidden recipients of the email. |
| `Importance` | Importance | Input | `InArgument<Importance>` | No | `Normal` | The importance of the mail. |
| `SaveAsDraft` | Save As Draft | Options | `InArgument<bool>` | No | `True` | Specifies whether the email should be saved as draft instead of being sent. |
| `ReplyToAll` | Reply To All | Options | `InArgument<bool>` | No | `False` | Specifies whether to send the reply to all the recipients. |
| `IsDeliveryReceiptRequested` | Delivery Receipt | Options | `InArgument<bool>` | No | `False` | Specifies whether a delivery receipt was requested. |
| `IsReadReceiptRequested` | Read Receipt | Options | `InArgument<bool>` | No | `False` | Specifies whether a read receipt was requested. |
| `MailboxArg` | Reply As | | [`MailboxArgument`](components/MailboxArgument.md) | No | | The email address of a user or a shared mailbox to reply from. See [MailboxArgument](components/MailboxArgument.md) for input modes. |

## Output Model

This activity does not return an output object.

## Enum Reference

| Enum | Values |
|---|---|
| `AttachmentInputMode` | `Existing`, `Builder`, `FilePaths`, `FilePathsBuilder` |
| `Importance` | `Low`, `Normal`, `High` |

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
<umam:ReplyToEmailConnections
    ConnectionId="{x:Null}"
    Body="[replyBody]" ReplyToAll="False" SaveAsDraft="False"
    DisplayName="Reply To Email">
  <umam:ReplyToEmailConnections.AttachmentsBackup>
    <usau:BackupSlot x:TypeArguments="umame:AttachmentInputMode" StoredValue="Builder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umame:AttachmentInputMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umam:ReplyToEmailConnections.AttachmentsBackup>
  <umam:ReplyToEmailConnections.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:ReplyToEmailConnections.MailboxArg>
</umam:ReplyToEmailConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Email` property is required.
- The reply body is always treated as HTML.
- When `SaveAsDraft` is `True` (default), the reply is saved to Drafts instead of being sent.
