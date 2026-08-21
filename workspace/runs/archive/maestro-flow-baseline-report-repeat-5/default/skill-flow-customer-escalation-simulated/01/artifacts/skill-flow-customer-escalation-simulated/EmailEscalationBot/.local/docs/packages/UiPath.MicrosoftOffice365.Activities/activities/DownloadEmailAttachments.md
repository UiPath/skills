# Download Email Attachments

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.DownloadEmailAttachments`

Downloads the attachments from an email to a local folder.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Email` | Email | Input | [`InArgument<Office365Message>`](types/Office365Message.md) | Yes | | The email to get the attachments from. |
| `ExcludeInlineAttachments` | Exclude Inline Attachments | Options | `InArgument<bool>` | No | `False` | Indicates whether to exclude inline attachments embedded in the email body. |
| `FilterByFileNames` | Filter By File Names | Options | `InArgument<string>` | No | | Download only attachments whose name matches the specified pattern. Separate multiple patterns with a vertical bar. |
| `DestinationPath` | Destination Path | Options | `InArgument<string>` | No | | The path where to save the downloaded attachments. |
| `ConflictResolution` | Conflict Resolution | Options | `InArgument<ConflictBehavior>` | No | `Fail` | The conflict resolution behavior when a file with the same name exists. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `NewResult` | Attachments | Output | `OutArgument<O365AttachmentLocalItem[]>` | The downloaded attachment files. |

## Output Model

The `NewResult` property returns an array of `O365AttachmentLocalItem` representing the downloaded files.

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
<umam:DownloadEmailAttachments
    ConnectionId="{x:Null}"
    DestinationPath="C:\Downloads"
    DisplayName="Download Email Attachments" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Email` property is required.
- Supports both simple filename filtering and advanced condition-based filtering.
- If `DestinationPath` is provided, the files are saved to disk.
