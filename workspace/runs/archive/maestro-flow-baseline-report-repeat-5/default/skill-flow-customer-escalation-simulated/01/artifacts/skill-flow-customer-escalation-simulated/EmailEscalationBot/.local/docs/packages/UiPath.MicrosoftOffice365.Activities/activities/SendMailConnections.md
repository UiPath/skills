# Send Mail

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.SendMailConnections`

Sends an email message using Microsoft Office 365 via Integration Service. Supports HTML or plain-text body, attachments, importance settings, delivery/read receipts, and sensitivity labels. Can also save as draft instead of sending.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `To` | To | Recipients | `InArgument<IEnumerable<string>>` | Yes | | The main recipients of the email, separated by semicolon. |
| `Cc` | CC | Recipients | `InArgument<IEnumerable<string>>` | No | | The secondary recipients of the email, separated by semicolon. |
| `Bcc` | BCC | Recipients | `InArgument<IEnumerable<string>>` | No | | The hidden recipients of the email, separated by semicolon. |
| `Subject` | Subject | Email | `InArgument<string>` | No | | The subject of the email. |
| `Body` | Body | Email | `InArgument<string>` | No | | The body of the email in HTML format. Visible when InputType is HTML. |
| `TextBody` | Body | Email | `InArgument<string>` | No | | The body of the email in TEXT format. Visible when InputType is TEXT. |
| `InputType` | Input Type | Email | `BodyInputType` | No | `HTML` | Specifies whether the body is in HTML or TEXT format. |
| `Attachments` | Attachments | Email | `InArgument<IEnumerable<IResource>>` | No | | The attachments to be sent with the email. |
| `AttachmentInputMode` | Attachment Input Mode | Email | `AttachmentInputMode` | No | `Existing` | How to specify the attachments. |
| `AttachmentList` | Attachment List | Email | `IEnumerable<InArgument<IResource>>` | No | | The list of individual attachments to include. |
| `AttachmentPaths` | Attachment Paths | Email | `InArgument<IEnumerable<string>>` | No | | The full paths of the attachments to be sent with the email. |
| `ArgumentAttachmentPaths` | Attachment Paths (Builder) | Email | `IEnumerable<InArgument<string>>` | No | | The list of file paths of the attachments to be included. |
| `Importance` | Importance | Options | `InArgument<Importance>` | No | `Normal` | Email importance level. |
| `ReplyTo` | Reply To | Options | `InArgument<IEnumerable<string>>` | No | | The email addresses to use when replying. |
| `SaveAsDraft` | Save As Draft | Options | `InArgument<bool>` | No | `True` | Specifies whether the email should be saved as draft. |
| `IsDeliveryReceiptRequested` | Delivery Receipt | Options | `InArgument<bool>` | No | `False` | Specifies whether a delivery receipt was requested. |
| `IsReadReceiptRequested` | Read Receipt | Options | `InArgument<bool>` | No | `False` | Specifies whether a read receipt was requested. |
| `SensitivityLabelId` | Sensitivity Label ID | Options | `InArgument<string>` | No | | The sensitivity label ID for the email. |
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use, including optional shared mailbox configuration. See [MailboxArgument](components/MailboxArgument.md) for input modes. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Result` | Message ID | Output | `OutArgument<string>` | The message ID of the sent email or draft. |

## Output Model

The `Result` property returns a `string` containing the message ID of the sent email or saved draft.

## Enum Reference

| Enum | Values |
|---|---|
| `BodyInputType` | `HTML`, `TEXT` |
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
<umam:SendMailConnections
    Body="[emailBody]" ConnectionId="{x:Null}"
    Importance="Normal" InputType="HTML"
    SaveAsDraft="False"
    Subject="[subject]" To="[recipientEmail]"
    DisplayName="Send Mail">
  <umam:SendMailConnections.InputTypeBackup>
    <usau:BackupSlot x:TypeArguments="umame:BodyInputType" StoredValue="HTML">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umame:BodyInputType, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umam:SendMailConnections.InputTypeBackup>
  <umam:SendMailConnections.AttachmentsBackup>
    <usau:BackupSlot x:TypeArguments="umame:AttachmentInputMode" StoredValue="Builder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umame:AttachmentInputMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umam:SendMailConnections.AttachmentsBackup>
  <umam:SendMailConnections.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
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

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- When `SaveAsDraft` is `True` (default), the email is saved to the Drafts folder instead of being sent.
- Batching is used for performance when there are no attachments and no `Result` binding.
- The `To` property is required; the activity will fail validation without it.
