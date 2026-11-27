# UploadFilesConnections

Key attributes:
- `MultipleFilesToUpload` — `IEnumerable<string>` of local file paths
- `FilesInputMode` — `"MultipleByVariable"` when using a variable
- `Folder` — destination folder with `FolderInputMode` (`"Browse"` or `"UrlOrId"`)
- `ConflictResolution` — behavior on name conflict
- `Convert` — `"True"` to convert to Google Workspace format
- Output: `FirstResult` as `GDriveRemoteItem`, `AllResults` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem[]`
