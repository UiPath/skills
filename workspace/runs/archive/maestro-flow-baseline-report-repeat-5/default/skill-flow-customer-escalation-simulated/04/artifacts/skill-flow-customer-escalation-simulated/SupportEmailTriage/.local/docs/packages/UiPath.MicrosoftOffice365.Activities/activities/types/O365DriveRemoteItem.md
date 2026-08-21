# O365DriveRemoteItem

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Files.Models`
**Implements:** `IRemoteResource`

Represents a remote file or folder in OneDrive or SharePoint. Returned as output by file/folder activities such as GetFileListConnections, GetFileFolderConnections, ForEachFileFolderConnections, CopyItemConnections, etc. Can be passed into [DriveItemArgument](../components/DriveItemArgument.md) in `UseExisting` mode.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `Name` | `String` | Name of the resource (without extension for files). |
| `FullName` | `String` | Full name of the resource including extension. |
| `Extension` | `String` | File extension (e.g., `.docx`). Empty for folders. |
| `ID` | `String` | Unique identifier of the drive item. |
| `Url` | `String` | Web URL of the resource. |
| `Uri` | `String` | Web URL of the resource (alias for `Url`; prefer `Url`). |
| `IsFolder` | `Boolean` | `true` if the resource is a folder. |
| `MimeType` | `String` | MIME type of the file, or the folder MIME type for folders. |
| `CreationDate` | `DateTime?` | Creation date and time. |
| `LastModifiedDate` | `DateTime?` | Last modified date and time. |
| `SizeInBytes` | `Int64` | Size of the file in bytes. |
| `CreatedBy` | `DriveItemIdentitySet` | Identity set of the user, device, or application that created the item. |
| `LastModifiedBy` | `DriveItemIdentitySet` | Identity set of the user, device, or application that last modified the item. |
| `CreatedByDisplayName` | `String` | Display name of the creator (user, application, or device). |
| `LastModifiedByDisplayName` | `String` | Display name of the last modifier. |
| `ParentUri` | `String` | URL of the parent folder. `null` for the root folder. |
| `Summary` | `String` | Summary text, if available. |
| `Metadata` | `Dictionary<String, String>` | Key-value metadata including URI, SharePoint drive name, site URL, and drive ID. |
| `LocalCopy` | `ILocalResource` | Provides access to a local downloaded copy of the file. |
| `IconUri` | `String` | Always `null`. |

## Related Types

### DriveItemIdentitySet

Represents the identity set (user, device, application) for created-by / modified-by.

| Property | Type | Description |
|----------|------|-------------|
| `User` | `DriveItemIdentity` | The user identity. |
| `Device` | `DriveItemIdentity` | The device identity. |
| `Application` | `DriveItemIdentity` | The application identity. |
| `Type` | `DriveItemIdentitySetType` | Flags indicating which identities are present (`Application`, `Device`, `User`). |

### DriveItemIdentity

| Property | Type | Description |
|----------|------|-------------|
| `DisplayName` | `String` | Display name of the identity. |
| `Id` | `String` | Unique identifier. |
| `EmailAddress` | `String` | Email address, if available. |

### DriveItemIdentitySetType (Flags Enum)

| Value | Int | Description |
|-------|-----|-------------|
| `Application` | 2 | Application identity is present. |
| `Device` | 4 | Device identity is present. |
| `User` | 8 | User identity is present. |

## Cross-References

- Used as output by OneDrive/SharePoint file activities
- Passed into [DriveItemArgument](../components/DriveItemArgument.md) via the `Item` property in `UseExisting` mode
- Filtered by [FileFilterArgument](../filtering/FileFilterArgument.md) and [FileFolderFilterArgument](../filtering/FileFolderFilterArgument.md)
