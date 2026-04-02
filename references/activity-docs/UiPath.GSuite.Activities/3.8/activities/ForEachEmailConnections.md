# ForEachEmailConnections

Iterates over multiple emails. Uses a **three-argument** body delegate.

Key attributes:
- `Folder` — same Browse pattern as above
- `MaxResults` — integer cap on emails processed
- `ImportantOnly`, `UnreadOnly`, `WithAttachmentsOnly` — filter flags
- Body delegate arguments:
  - `Argument1`: `UiPath.GSuite.Models.GmailMessage` named `"CurrentEmail"`
  - `Argument2`: `x:Int32` named `"CurrentEmailIndex"` (index within current batch)
  - Outer scope also provides `CurrentIndex` / `Length` counters
