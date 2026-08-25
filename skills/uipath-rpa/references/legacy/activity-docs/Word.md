# UiPath Word Activities - Legacy Reference

## Overview
Word automation with COM Interop (requires Word) and Portable (Xceed.Words.NET, no Word needed). Package: `UiPath.Word.Activities`.

---

## Activities

### Windows/COM (require WordApplicationScope)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `WordApplicationScope` | FilePath, CreateNewFile, AutoSave, ReadOnly, Password, EditPassword | Container for all COM activities |
| `WordAppendText` | Text, NewLine (default true) | |
| `WordReadText` | Output: Text | Reads entire document |
| `WordReplaceText` | Search (max 255 chars), Replace (max 255 chars), ReplaceAll | |
| `WordAddImage` | ImagePath, Position (Start/End/Before/After/Replace), InsertRelativeTo | |
| `WordInsertDataTable` | DataTable | Default position: Start |
| `WordInsertHyperlink` | TextToDisplay, Address, TextToSearchFor | |
| `WordSetBookmarkContent` | BookmarkName, BookmarkText | Max 40 chars for name |
| `WordExportToPdf` | FilePath, ReplaceExisting | |
| `WordSaveAs` | FilePath, SaveAsFileType (docx/docm/doc/html/rtf/txt) | |
| `WordReplacePicture` | PicturePath, PictureAltText | Throws if alt text not found |
| `WordPasteFromClipboard` | Text, PasteOption (EmbedData/LinkData/Picture) | |
| `WordGetSensitivityLabel` | Output: SensitivityLabel | |
| `WordAddSensitivityLabel` | SensitivityLabel, Justification | |

### Portable (no Word required, Xceed-based)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `DocumentCreateNew` | FilePath, ConflictResolution (Replace/Fail/Skip) | .docx/.docm only |
| `DocumentReadText` | FilePath | |
| `DocumentAppendText` | FilePath, Text, NewLine | |
| `DocumentReplaceText` | FilePath, Search, Replace | |
| `DocumentAddImage` | FilePath, ImagePath, positional args | |
| `DocumentInsertDataTable` | FilePath, DataTable | |
| `DocumentInsertHyperlink` | FilePath, TextToDisplay, Address | |
| `DocumentSetBookmarkContent` | FilePath, BookmarkName, BookmarkText | |

---

## Critical Gotchas

### COM Object Management
1. **Must release COM objects** via `Marshal.ReleaseComObject()` - failing leaves Word processes
2. **RPC Server retry** - Error 0x8001010A retries up to 3 times with 100ms delay when Word is busy
3. **DisplayAlerts suppressed** during SaveAs/ExportPdf to prevent dialogs in unattended mode

### AutoSave
4. **AutoSave=true (default)** saves after EACH operation - performance impact
5. **Only saves if NOT ReadOnly** mode
6. **Portable (FileDocument)** only saves on close if content hash changed

### Text Limits
7. **Search text max 256 characters** (WordReplaceText validation: `text.Length > 256`)
8. **TextToSearch max 256 characters** (DocumentActivity validation)
9. **Bookmark name max 40 characters**

### Positional Insert Constraints
10. **InsertRelativeTo=Document**: Position can only be Start or End
11. **InsertRelativeTo=Bookmark**: Position can only be Start or End
12. **InsertRelativeTo=Text**: Supports Occurrence (All/First/Last/Specific)

### ReadOnly Mode
13. **Changes execute but don't persist** in ReadOnly mode - no error thrown

### SharePoint/URL Documents
14. **Cannot create new file at URL** (CreateNewFile must be false)
15. **SharePoint URLs auto-sanitized** via `.SanitizeWordSharePointUrl()`

### No Template Support
16. **Activities don't support .dotx templates** - must create blank then modify

### Dependencies
17. **Xceed.Words.NET** for portable (no COM)
18. **Microsoft.Office.Interop.Word** for Windows (COM, embedded interop types)
