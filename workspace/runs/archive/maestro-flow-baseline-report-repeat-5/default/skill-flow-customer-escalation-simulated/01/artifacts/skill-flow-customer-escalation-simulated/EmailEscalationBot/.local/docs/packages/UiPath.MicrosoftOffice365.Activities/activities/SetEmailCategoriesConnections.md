# Set Email Categories

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.SetEmailCategoriesConnections`

Assigns and/or removes categories on an email.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Email` | Email | Input | [`InArgument<Office365Message>`](types/Office365Message.md) | Yes | | The email to associate with the specified categories. |
| `CategoriesToAssign` | Categories To Assign | Input | `InArgument<string[]>` | No | | The categories to add to the email. **XAML:** set as a flat attribute with a VB.NET array literal (e.g. `[New String(){"Work", "Important"}]`) — WF4 cannot express `String[]` as an `InArgument` type argument, and `List<string>` is not assignable to `string[]`. |
| `CategoriesToRemove` | Categories To Remove | Input | `CategoriesToRemove` | No | `None` | Indicates which categories to remove from the email. |
| `SpecificCategoriesToRemove` | Specific Categories To Remove | Options | `InArgument<string[]>` | No | | The specific categories to remove (when CategoriesToRemove is Specific). **XAML:** set as a flat attribute with a VB.NET array literal (e.g. `[New String(){"Work", "Important"}]`) — WF4 cannot express `String[]` as an `InArgument` type argument, and `List<string>` is not assignable to `string[]`. |
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use. See [MailboxArgument](components/MailboxArgument.md) for input modes. |

## Output Model

This activity does not return an output object.

## Enum Reference

| Enum | Values |
|---|---|
| `CategoriesToRemove` | `None`, `All`, `Specific` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umamm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365="clr-namespace:UiPath.MicrosoftOffice365.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umam:SetEmailCategoriesConnections
    ConnectionId="{x:Null}"
    CategoriesToRemove="None"
    CategoriesToAssign="[New String(){&quot;Category1&quot;, &quot;Category2&quot;}]"
    DisplayName="Set Email Categories">
  <umam:SetEmailCategoriesConnections.Email>
    <InArgument x:TypeArguments="umo365:Office365Message">[emailMessage]</InArgument>
  </umam:SetEmailCategoriesConnections.Email>
  <umam:SetEmailCategoriesConnections.MailboxArg>
    <umamm:MailboxArgument UseSharedMailbox="False">
      <umamm:MailboxArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode" StoredValue="NoMailbox">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umamm:MailboxArgument.Backup>
    </umamm:MailboxArgument>
  </umam:SetEmailCategoriesConnections.MailboxArg>
</umam:SetEmailCategoriesConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Email` property is required.
- If `CategoriesToRemove` is `None`, then `CategoriesToAssign` is required.
- If `CategoriesToRemove` is `Specific`, then `SpecificCategoriesToRemove` is required.
