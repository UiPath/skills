# Word Activities Presentation Rules

- **Activities** — use the display name (e.g., "Save Document as PDF", "Word Application Scope", "Replace Text"), not the fully qualified class name (e.g., `UiPath.Word.Activities.WordExportToPdf`)
- **Documents** — refer to documents by their filename (e.g., "document 'Doc1.docx'") or full path when ambiguous; not by the variable holding the document reference
- **Word instances** — refer to the external Word process as "Microsoft Word (`WINWORD.EXE`)" so the user knows which process to check for or close
- **HRESULTs** — quote the exact code and symbol together (e.g., "`0x8001010E RPC_E_WRONG_THREAD`"), and name the IID's interface (`{0002096B-...}` = `Microsoft.Office.Interop.Word._Document`) so the user can correlate it with the stack trace
- **Office versions** — refer to Office by its installed product name and bitness (e.g., "Microsoft 365 Apps for Enterprise (64-bit)", "Office 2019 (32-bit)"), not by internal version numbers like `16.0` unless they are the only identifier available
- **Run surface** — name the surface in the user's terms (e.g., "Studio Run/Debug (foreground)", "unattended robot (Session 0)"), not internal runtime flags like `isAttended`
