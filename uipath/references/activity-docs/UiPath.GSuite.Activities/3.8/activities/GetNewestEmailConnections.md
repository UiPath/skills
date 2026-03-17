# GetNewestEmailConnections

Retrieves the most recent email matching the criteria.

Key attributes:
- `Folder` — folder selection; use `BrowserFolderId` + `BrowserFolder` for Browse mode (e.g., `BrowserFolderId="INBOX"`)
- `UnreadOnly` — `"True"` / `"False"`
- `WithAttachmentsOnly` — `"True"` / `"False"`
- `MarkAsRead` — `"True"` / `"False"`
- `ImportantOnly` — `"True"` / `"False"`
- `StarredOnly` — `"True"` / `"False"`
- Output: `Result` as `UiPath.GSuite.Models.GmailMessage`
