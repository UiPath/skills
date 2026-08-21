# Share Item

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.ShareItemConnections`

Shares a file or folder with the specified recipients via OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `Item` | Item | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The file or folder to share. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `RecipientType` | Recipient Type | `Property` | `GranteeType` | No | `PeopleInOrganization` | The type of recipient: `SpecificPeople`, `PeopleInOrganization`, `Anyone`. |
| `PermissionType` | Permission Type | `Property` | `GranteePermission` | No | `View` | The permission level: `View`, `Edit`. |
| `Recipients` | Recipients | `InArgument` | `IEnumerable<String>` | When SpecificPeople | | Email addresses of recipients. Required when RecipientType is `SpecificPeople`. |
| `Message` | Message | `InArgument` | `String` | No | | A message included in the sharing invitation email. |
| `SendInvitationEmail` | Send Invitation Email | `InArgument` | `Boolean` | No | `True` | Whether to send a sharing invitation email. |
| `SignInRequired` | Sign In Required | `InArgument` | `Boolean` | No | `False` | Whether the recipient must sign in to access the item. |
| `SharingLinkPassword` | Sharing Link Password | `InArgument` | `String` | No | | An optional password for the sharing link. |
| `ExpirationDate` | Expiration Date | `InArgument` | `DateTime` | No | | An optional expiration date for the sharing permission. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `AccessUrl` | Access URL | `OutArgument` | `String` | The web URL of the sharing link or drive item. |

> **Supported `ItemSelectionMode` values:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`. `Browse` is also available in Studio but not suitable for AI-generated XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umaf:ShareItemConnections
    ConnectionId="{x:Null}"
    AccessUrl="[shareUrl]"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    DisplayName="Share Item"
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/report.xlsx"
    PermissionType="View" RecipientType="PeopleInOrganization"
>
  <umaf:ShareItemConnections.DriveItemArgument>
    <umafm:DriveItemArgument
        ItemSelectionMode="ItemUrl"
        ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/report.xlsx"
        ParentFullPathHint="">
      <umafm:DriveItemArgument.ItemIdBackup>
        <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
            x:Name="__ReferenceID0" StoredValue="ItemUrl">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umafm:DriveItemArgument.ItemIdBackup>
    </umafm:DriveItemArgument>
  </umaf:ShareItemConnections.DriveItemArgument>
  <umaf:ShareItemConnections.Recipients>
    <InArgument x:TypeArguments="scg:IEnumerable(x:String)">[recipientEmails]</InArgument>
  </umaf:ShareItemConnections.Recipients>
</umaf:ShareItemConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
