# Word Activities Presentation Rules

- **Activities** — use the display name (e.g., "Word Application Scope", "Use Word File", "Kill Process"), not the fully qualified class name (e.g., `UiPath.Word.Activities.WordApplicationScope`)
- **Documents** — refer to documents by their filename (e.g., "document 'Contract.docx'") or full path when ambiguous; not by the variable holding the document reference
- **Office versions** — refer to Office by its installed product name and bitness (e.g., "Microsoft 365 Apps for Enterprise (64-bit)", "Office 2019 (32-bit)"), not by internal version numbers like `16.0` unless they are the only identifier available
- **Word settings** — refer to Trust Center settings by the exact UI label path the user navigates (e.g., `File > Options > Trust Center > Trust Center Settings > Trusted Locations`), so the user can find the toggle without guessing
- **Processes** — refer to the Word process as `WINWORD.EXE` (the executable name the user sees in Task Manager), not "Word process" alone
