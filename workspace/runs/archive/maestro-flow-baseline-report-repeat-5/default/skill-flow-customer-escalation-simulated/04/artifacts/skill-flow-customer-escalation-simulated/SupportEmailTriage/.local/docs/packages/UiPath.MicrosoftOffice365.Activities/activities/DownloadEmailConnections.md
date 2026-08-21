# Download Email

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.DownloadEmailConnections`

Downloads an email in EML file format to a local folder.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Email` | Email | Input | [`InArgument<Office365Message>`](types/Office365Message.md) | Yes | | The email to download. |
| `DestinationPath` | Destination Path | Options | `InArgument<string>` | No | | The path where to save the downloaded mail. |
| `CreateMissingFolders` | Create Missing Folders | | `InArgument<bool>` | No | `False` | Indicates whether to create missing folders in the destination path. |
| `ConflictResolution` | Conflict Resolution | Options | `InArgument<ConflictBehavior>` | No | `Fail` | The conflict resolution behavior when a file with the same name exists. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `NewResult` | Downloaded File | Output | `OutArgument<O365MailLocalItem>` | The downloaded EML file. |

## Output Model

The `NewResult` property returns an `O365MailLocalItem` representing the downloaded EML file.

## Enum Reference

| Enum | Values |
|---|---|
| `ConflictBehavior` | `Fail`, `Replace`, `Rename` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:DownloadEmailConnections
    ConnectionId="{x:Null}"
    DestinationPath="C:\Downloads"
    DisplayName="Download Email" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Email` property is required.
- If `DestinationPath` is provided, the file is saved to disk.
