# Word — Coded Workflow API

`UiPath.Word.Activities`

Provides coded workflow operations for creating, reading, and manipulating Word documents (.docx, .docm). Supports two runtime modes: a cross-platform (portable) API and a Windows-only API with additional features like sensitivity labels, content controls, and Save As.

**Service accessor:** `word` (type `IWordService`)
**Required package:** `"UiPath.Word.Activities": "*"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```
System
System.Collections.Generic
System.Data
UiPath.Word
UiPath.Word.Activities
UiPath.Word.Activities.API
UiPath.Word.Activities.API.Models
```

## Service Overview

The `word` service provides a handle-based API for Word document operations. You open a document via the service, receive a disposable handle, then call extension methods on the handle to read, write, and manipulate content.

The API has two runtime variants:

| Variant | Method | Handle Type | Availability |
|---------|--------|-------------|-------------|
| Portable (cross-platform) | `UseDocument` | `IWordDocumentHandle` | All platforms |
| Windows (COM/Interop) | `UseWordDocument` | `IWordDocument` | Windows only |

Both handles are `IDisposable` — always use them inside a `using` statement.

---

## Opening a Document (Portable)

### `IWordDocumentHandle UseDocument(string documentPath, bool createNew = true)`

Opens or creates a Word document using the cross-platform engine.

**Parameters:**
- `documentPath` (`string`) — Path of the Word document
- `createNew` (`bool`) — If the document does not exist, determines whether a new document is created (default: `true`)

**Returns:** `IWordDocumentHandle` — Disposable handle to the Word document. Use with `using` statement.

### `IWordDocumentHandle UseDocument(DocumentOptions options)`

Opens or creates a Word document with detailed options. When `CreateNew` is true, validates the file extension (.docx or .docm), handles conflict behavior, and creates the parent directory if needed.

**Parameters:**
- `options` (`DocumentOptions`) — Options controlling how the document is opened or created

**Returns:** `IWordDocumentHandle` — Disposable handle to the Word document. Use with `using` statement.

---

## Opening a Document (Windows)

### `IWordDocument UseWordDocument(string path)`

Opens or creates a Word file using COM/Interop (Windows only).

**Parameters:**
- `path` (`string`) — The path of the Word file

**Returns:** `IWordDocument` — Disposable handle for performing operations on the Word file. Use with `using` statement.

### `IWordDocument UseWordDocument(WordUseOptions options)`

Opens or creates a Word file with detailed options (Windows only).

**Parameters:**
- `options` (`WordUseOptions`) — Options controlling how the document is opened or created

**Returns:** `IWordDocument` — Disposable handle for performing operations on the Word file. Use with `using` statement.

---

## Handle Types

### `IWordDocumentHandle` (Portable)

Disposable handle to a Word document opened via the portable (cross-platform) engine. Operations are available as extension methods in the `UiPath.Word.Activities.API.WordOperations` class and are called directly on the handle.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Extension Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `AppendText(string text, bool newLine = true)` | `void` | Appends text to the document. If `newLine` is true, appends on a new line. |
| `AppendText(string text)` | `void` | Appends text to the document on a new line. |
| `ReadText()` | `string` | Reads all text from the document. |
| `ReplaceText(string search, string replace)` | `bool` | Searches and replaces text. Returns true if the searched text was found. |
| `AddPicture(string imagePath)` | `bool` | Adds a picture at the end of the document. |
| `AddPicture(string imagePath, Position position)` | `bool` | Adds a picture at the start or end of the document. |
| `AddPicture(string imagePath, string bookmark, Position position)` | `bool` | Adds a picture relative to a bookmark. |
| `AddPicture(string imagePath, string textToSearchFor, Occurrence occurrence, int? occurrenceIndex, Position position)` | `bool` | Adds a picture relative to a text occurrence. |
| `InsertDataTable(DataTable dataTable)` | `bool` | Inserts a DataTable at the end of the document. |
| `InsertDataTable(DataTable dataTable, Position position)` | `bool` | Inserts a DataTable at the start or end of the document. |
| `InsertDataTable(DataTable dataTable, string bookmark, Position position)` | `bool` | Inserts a DataTable relative to a bookmark. |
| `InsertDataTable(DataTable dataTable, string textToSearchFor, Occurrence occurrence, int? occurrenceIndex, Position position)` | `bool` | Inserts a DataTable relative to a text occurrence. |
| `InsertHyperlink(string textToDisplay, string address)` | `bool` | Inserts a hyperlink at the end of the document. |
| `InsertHyperlink(string textToDisplay, string address, Position position)` | `bool` | Inserts a hyperlink at the start or end of the document. |
| `InsertHyperlink(string textToDisplay, string address, Position position, string textToSearchFor)` | `bool` | Inserts a hyperlink relative to a text. |
| `InsertHyperlink(string textToDisplay, string address, InsertHyperlinkRelativeToType insertRelativeTo, Position position, string textToSearchFor)` | `bool` | Inserts a hyperlink with full control over positioning. |
| `SetBookmarkContent(string bookmarkName, string bookmarkText)` | `bool` | Sets the text content of a bookmark. |
| `EnableTrackChanges()` | `void` | Enables revision tracking on the document. Tracking applies to all users. |
| `DisableTrackChanges()` | `void` | Disables revision tracking on the document. |
| `AddComment(string commentText, string anchorText, int? occurrenceIndex = null, string author = null)` | `void` | Adds a comment anchored to a text match in the document. |
| `AddComment(string commentText, string bookmark, string author = null)` | `void` | Adds a comment anchored to a bookmark in the document. |

### `IWordDocument` (Windows)

Disposable handle to a Word document opened via COM/Interop (Windows only). Operations are available as extension methods in the `UiPath.Word.Activities.API.WordOperations` class.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

> **Return type note:** Several methods that return `bool` in the portable API return `void` in the Windows API (e.g., `AddPicture`, `InsertDataTable`/`InsertDataTableInDocument`, `SetBookmarkContent`). Do not assume return types are the same across the two handle types.

#### Extension Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `AppendText(string text, bool addNewLineBeforeText = true)` | `void` | Appends text at the end of the document. |
| `ReadText()` | `string` | Reads all text from the document. |
| `ReplaceTextInDocument(string searchFor, string replaceWith, bool replaceAll = true)` | `bool` | Replaces first/all occurrences of text. Both `searchFor` and `replaceWith` max 255 chars. |
| `AddPicture(string pictureToInsert)` | `void` | Adds a picture at the end of the document. |
| `AddPicture(string pictureToInsert, Position positionWhereToInsert)` | `void` | Adds a picture at the start or end of the document. |
| `AddPicture(string pictureToInsert, string bookmarkToSearchFor, Position positionWhereToInsert)` | `void` | Adds a picture relative to a bookmark. |
| `AddPicture(string pictureToInsert, string textToSearchFor, Occurrence textOccurrence, int? occurenceIndex, Position positionWhereToInsert)` | `void` | Adds a picture relative to a text occurrence. |
| `AddHyperlinkToDocument(string textToDisplay, string address)` | `bool` | Adds a hyperlink at the end of the document. |
| `AddHyperlinkToDocument(string textToDisplay, string address, Position positionWhereToInsert)` | `bool` | Adds a hyperlink at the start or end of the document. |
| `AddHyperlinkToDocument(string textToDisplay, string address, Position positionWhereToInsert, string textToSearchFor)` | `bool` | Adds a hyperlink relative to a text. |
| `AddHyperlinkToDocument(string textToDisplay, string address, InsertHyperlinkRelativeToType insertRelativeTo, Position positionWhereToInsert, string textToSearchFor)` | `bool` | Adds a hyperlink with full control over positioning. |
| `InsertDataTableInDocument(DataTable tableToInsert)` | `void` | Inserts a DataTable at the end of the document. |
| `InsertDataTableInDocument(DataTable tableToInsert, Position positionWhereToInsert)` | `void` | Inserts a DataTable at the start or end of the document. |
| `InsertDataTableInDocument(DataTable tableToInsert, string bookmarkToSearchFor, Position positionWhereToInsert)` | `void` | Inserts a DataTable relative to a bookmark. |
| `InsertDataTableInDocument(DataTable tableToInsert, string textToSearchFor, Occurrence textOccurrence, int? occurenceIndex, Position positionWhereToInsert)` | `void` | Inserts a DataTable relative to a text occurrence. |
| `SetBookmarkContent(string bookmarkName, string bookmarkText)` | `void` | Sets the text in a document bookmark. |
| `SetContentControlProperty(MatchPropertyBy matchBy, string matchTo, string value, bool replaceAll = false)` | `bool` | Sets the value of a content control matched by text, title, or tag. |
| `ReplacePicture(string findPicturesWithAltText, string replaceWithPicture)` | `void` | Replaces pictures by alt text. |
| `PasteChartPictureIntoDocument(PasteRelativeToType pasteRelativeTo, Position positionWhereToPaste, string textToSearchFor, PasteOptionType pasteOption)` | `bool` | Pastes a chart/image from clipboard into the document. |
| `SaveDocumentAs(WordSaveAsType saveAsType, string saveAsFile, bool replaceExisting = true)` | `void` | Saves the document as a different format. |
| `SaveAsPDF(string filePathToSaveAs, bool replaceExisting = true)` | `void` | Exports the document to PDF. |
| `AddSensitivityLabel(IWordLabelObject label)` | `void` | Adds a sensitivity label to the document. |
| `GetSensitivityLabel()` | `IWordLabelObject` | Retrieves the sensitivity label from the document. |
| `EnableTrackChanges(TrackingScope scope = TrackingScope.TrackForEveryone)` | `void` | Enables revision tracking on the document. When scope is `TrackForEveryone`, enforces tracking for all users. |
| `DisableTrackChanges()` | `void` | Disables revision tracking on the document. |
| `AddComment(string commentText, string anchorText, int? occurrenceIndex = null, string author = null)` | `void` | Adds a comment anchored to a text match in the document via COM Interop. |
| `AddComment(string commentText, string bookmark, string author = null)` | `void` | Adds a comment anchored to a bookmark in the document via COM Interop. |
| `AddCommentAtRevision(string commentText, string revisionText, int? occurrenceIndex = null, string author = null)` | `void` | Adds a comment anchored to a tracked change (revision) in the document. Windows only. |

---

## Options & Configuration Classes

### `DocumentOptions`

Options for opening or creating a Word document (portable API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Path` | `string` | — | Path of the Word document. |
| `CreateNew` | `bool` | `true` | If the document does not exist, creates a new one. Validates file extension (.docx or .docm) and creates parent directory if needed. |
| `ConflictBehavior` | `ConflictBehavior` | `Skip` | Behavior when a file already exists and `CreateNew` is true. |

### `WordUseOptions`

Options for opening or creating a Word document (Windows API).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Path` | `string` | — | Path of the Word file. |
| `CreateIfNotExist` | `bool` | `true` | If true, the file is created when it does not exist. |
| `ReadOnly` | `bool` | `false` | If true, the document is opened as read-only. |
| `AutoSave` | `bool` | `true` | If true, saves changes after document operations. |
| `SensitivityOperation` | `WordLabelOperation` | `None` | Sensitivity label operation to execute when opening/creating the file. |
| `SensitivityLabel` | `IWordLabelObject` | — | Sensitivity label object to apply. Used only when `SensitivityOperation` is `Add`. |

### `IWordLabelObject`

Represents a sensitivity label to apply to a document.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `LabelId` | `string` | — | Sensitivity label ID. |
| `Justification` | `string` | — | Justification for changing the label. |

---

## Enum Reference

**`ConflictBehavior`**: `Replace`, `Fail`, `Skip`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

> **Note:** Valid `Position` values depend on the operation mode. For operations relative to the whole **Document**, only `Start` and `End` are supported. For operations relative to **Text** or a **Bookmark**, `Before`, `After`, and `Replace` are supported. Using unsupported combinations will result in validation failures or the operation returning `false`.

**`Occurrence`**: `All`, `First`, `Last`, `Specific`

**`InsertHyperlinkRelativeToType`**: `Document`, `Text`

**`PasteRelativeToType`**: `Document`, `Text`

**`PasteOptionType`**: `EmbedData`, `LinkData`, `Picture`

**`MatchPropertyBy`**: `Text`, `Title`, `Tag`

**`WordSaveAsType`**: `XmlDocument`, `MacroEnabledDocument`, `OldDocument`, `WebPage`, `FilteredWebPage`, `RichText`, `PlainText`

**`WordLabelOperation`**: `None`, `Add`, `Clear`

**`TrackingScope`**: `TrackForEveryone`, `TrackForMe`

> **Note:** `TrackForEveryone` protects the document to enforce tracking for all users. `TrackForMe` enables tracking for the current user only without protection. Windows only.

**`CommentAnchorType`**: `Text`, `Bookmark`, `Revision`

> **Note:** `Text` anchors the comment to a text match. `Bookmark` anchors to a named bookmark. `Revision` anchors to a tracked change and is only available via `AddCommentAtRevision` on the Windows API — not available on the cross-platform API.

---

## Common Patterns

### Read text from an existing document (portable)

```csharp
[Workflow]
public void Execute()
{
    var docPath = Path.Combine("Reports", "quarterly.docx");
    using var doc = word.UseDocument(docPath, createNew: false);
    var content = doc.ReadText();
    Log(content);
}
```

### Create a new document and append text (portable)

```csharp
[Workflow]
public void Execute()
{
    using var doc = word.UseDocument(new DocumentOptions
    {
        Path = Path.Combine("Output", "report.docx"),
        CreateNew = true,
        ConflictBehavior = ConflictBehavior.Replace
    });

    doc.AppendText("Quarterly Report", newLine: false);
    doc.AppendText("This report covers Q1 2025 performance metrics.");
    doc.AppendText("Revenue increased by 15% compared to Q4 2024.");
}
```

### Replace text and insert a picture (portable)

```csharp
[Workflow]
public void Execute()
{
    var templatePath = Path.Combine("Templates", "invoice.docx");
    using var doc = word.UseDocument(templatePath, createNew: false);

    doc.ReplaceText("{{CustomerName}}", "Acme Corp");
    doc.ReplaceText("{{Date}}", DateTime.Now.ToString("yyyy-MM-dd"));
    doc.AddPicture(Path.Combine("Assets", "logo.png"), "LogoBookmark", Position.Replace);
}
```

### Fill bookmarks and export to PDF (Windows)

```csharp
[Workflow]
public void Execute()
{
    using var doc = word.UseWordDocument(new WordUseOptions
    {
        Path = "C:\\Templates\\contract.docx",
        CreateIfNotExist = false,
        AutoSave = true
    });

    doc.SetBookmarkContent("ClientName", "Acme Corp");
    doc.SetBookmarkContent("ContractDate", DateTime.Now.ToString("MMMM dd, yyyy"));
    doc.SetBookmarkContent("Amount", "$50,000");
    doc.SaveAsPDF("C:\\Output\\contract_signed.pdf");
}
```

### Insert a DataTable from data (portable)

```csharp
[Workflow]
public void Execute()
{
    var table = new DataTable("Sales");
    table.Columns.Add("Product", typeof(string));
    table.Columns.Add("Revenue", typeof(string));
    table.Rows.Add("Widget A", "$12,000");
    table.Rows.Add("Widget B", "$8,500");

    using var doc = word.UseDocument(Path.Combine("Reports", "sales.docx"));
    doc.AppendText("Sales Summary", newLine: false);
    doc.InsertDataTable(table, Position.End);
}
```

---

## Track Changes

### Enable Track Changes (Portable)

### `void EnableTrackChanges(this IWordDocumentHandle wordDocument)`

Enables revision tracking on the document by adding the `trackRevisions` element to `word/settings.xml`. Tracking applies to all users (the cross-platform path does not support per-user scope).

**Parameters:** None

**Returns:** `void`

---

### Enable Track Changes (Windows)

### `void EnableTrackChanges(this IWordDocument wordDocument, TrackingScope scope = TrackingScope.TrackForEveryone)`

Enables revision tracking on the document. When scope is `TrackForEveryone`, the document is protected to enforce tracking for all users.

**Parameters:**
- `scope` (`TrackingScope`) — Tracking scope. Default: `TrackForEveryone`

**Returns:** `void`

---

### Enable Track Changes with Password (Windows)

### `void EnableTrackChanges(this IWordDocument wordDocument, TrackingScope scope, string password)`

Enables revision tracking with password protection. The password prevents users from disabling track changes without providing the correct password.

**Parameters:**
- `scope` (`TrackingScope`) — Tracking scope
- `password` (`string`) — Password to enforce track changes protection

**Returns:** `void`

---

### Disable Track Changes (Portable)

### `void DisableTrackChanges(this IWordDocumentHandle wordDocument)`

Disables revision tracking by removing the `trackRevisions` element from `word/settings.xml`.

**Parameters:** None

**Returns:** `void`

---

### Disable Track Changes (Windows)

### `void DisableTrackChanges(this IWordDocument wordDocument)`

Disables revision tracking. If the document was protected via `TrackForEveryone`, it is unprotected first.

**Parameters:** None

**Returns:** `void`

---

### Disable Track Changes with Password (Windows)

### `void DisableTrackChanges(this IWordDocument wordDocument, string password)`

Disables revision tracking, removing password protection if it was set.

**Parameters:**
- `password` (`string`) — Password to remove track changes protection

**Returns:** `void`

---

### Examples

```csharp
[Workflow]
public void Execute()
{
    // Portable: enable and disable track changes
    using var doc = word.UseDocument("C:\\Documents\\report.docx", createNew: false);
    doc.EnableTrackChanges();
    doc.AppendText("This text will be tracked as an insertion.");
    doc.DisableTrackChanges();
}
```

```csharp
[Workflow]
public void Execute()
{
    // Windows: enable track changes with scope control
    using var doc = word.UseWordDocument("C:\\Documents\\report.docx");
    doc.EnableTrackChanges(TrackingScope.TrackForEveryone);
    doc.AppendText("This text will be tracked as an insertion.");
    doc.DisableTrackChanges();
}
```

```csharp
[Workflow]
public void Execute()
{
    // Windows: enable track changes with password protection
    using var doc = word.UseWordDocument("C:\\Documents\\report.docx");
    doc.EnableTrackChanges(TrackingScope.TrackForEveryone, "secretPass");
    doc.AppendText("Track changes cannot be disabled without the password.");
    doc.DisableTrackChanges("secretPass");
}
```

---

## Comments

### Add Comment at Text (Portable)

### `void AddComment(this IWordDocumentHandle wordDocument, string commentText, string anchorText, int? occurrenceIndex = null, string author = null)`

Adds a comment anchored to a text match in the document.

**Parameters:**
- `commentText` (`string`) — The comment body text
- `anchorText` (`string`) — The text in the document to anchor the comment to
- `occurrenceIndex` (`int?`) — Which occurrence of the anchor text to target (1-based). Default: first occurrence when `null`
- `author` (`string`) — Comment author name. Default: current system user when `null` or empty

**Returns:** `void`

---

### Add Comment at Bookmark (Portable)

### `void AddComment(this IWordDocumentHandle wordDocument, string commentText, string bookmark, string author = null)`

Adds a comment anchored to a bookmark in the document.

**Parameters:**
- `commentText` (`string`) — The comment body text
- `bookmark` (`string`) — The bookmark name to anchor the comment to
- `author` (`string`) — Comment author name. Default: current system user when `null` or empty

**Returns:** `void`

---

### Add Comment at Text (Windows)

### `void AddComment(this IWordDocument wordDocument, string commentText, string anchorText, int? occurrenceIndex = null, string author = null)`

Adds a comment anchored to a text match in the document via COM Interop.

**Parameters:**
- `commentText` (`string`) — The comment body text
- `anchorText` (`string`) — The text in the document to anchor the comment to
- `occurrenceIndex` (`int?`) — Which occurrence of the anchor text to target (1-based). Default: first occurrence when `null`
- `author` (`string`) — Comment author name. Default: current user when `null`

**Returns:** `void`

---

### Add Comment at Bookmark (Windows)

### `void AddComment(this IWordDocument wordDocument, string commentText, string bookmark, string author = null)`

Adds a comment anchored to a bookmark in the document via COM Interop.

**Parameters:**
- `commentText` (`string`) — The comment body text
- `bookmark` (`string`) — The bookmark name to anchor the comment to
- `author` (`string`) — Comment author name. Default: current user when `null`

**Returns:** `void`

---

### Add Comment at Revision (Windows only)

### `void AddCommentAtRevision(this IWordDocument wordDocument, string commentText, string revisionText, int? occurrenceIndex = null, string author = null)`

Adds a comment anchored to a tracked change (revision) in the document. Windows only — not available on the cross-platform API.

**Parameters:**
- `commentText` (`string`) — The comment body text
- `revisionText` (`string`) — The text content of the tracked change to anchor the comment to
- `occurrenceIndex` (`int?`) — Which matching revision to anchor to (1-based). Default: first match when `null`
- `author` (`string`) — Comment author name. Default: current user when `null`

**Returns:** `void`

---

### Examples

```csharp
[Workflow]
public void Execute()
{
    // Portable: add a comment anchored to text
    using var doc = word.UseDocument("C:\\Documents\\report.docx", createNew: false);
    doc.AddComment(
        "Please review this paragraph.",
        "quarterly results",
        occurrenceIndex: 1,
        author: "ReviewBot");
}
```

```csharp
[Workflow]
public void Execute()
{
    // Portable: add a comment at a bookmark
    using var doc = word.UseDocument("C:\\Documents\\report.docx", createNew: false);
    doc.AddComment(
        "This section needs updating.",
        "SummaryBookmark",
        author: "ReviewBot");
}
```

```csharp
[Workflow]
public void Execute()
{
    // Windows: add a comment at a tracked change (revision)
    using var doc = word.UseWordDocument("C:\\Documents\\report.docx");
    doc.EnableTrackChanges(TrackingScope.TrackForEveryone);
    doc.AppendText("New content to review.");
    doc.AddCommentAtRevision(
        "Please verify this addition.",
        "New content to review.",
        author: "ReviewBot");
}
```
