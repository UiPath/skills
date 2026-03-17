# ForEachFileFolderConnections

Iterates items inside a Drive folder.

Key attributes:
- `Item` — folder selector (Browse mode)
- `MaxResults` — cap on items iterated
- `WhatToReturn` — `"Files"`, `"Folders"`, or `"FilesAndFolders"`
- Body delegate argument: `CurrentItem` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`
