# GetFileListConnections

Key attributes:
- `Item` / `ManualEntryLocation` — folder to list contents of
- `LocationInputMode` — `"EnterId"` or `"Browse"`
- `MaxResults` — integer cap on results
- `StarredOnly` — `"True"` / `"False"`
- `WhatToReturn` — `"Files"`, `"Folders"`, or `"FilesAndFolders"`
- `Filter` — child block for name/type filtering conditions
- Output: `Result` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem[]`
