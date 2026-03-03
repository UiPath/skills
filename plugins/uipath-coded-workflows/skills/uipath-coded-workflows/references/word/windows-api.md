# Word — Windows (Interop) API

Full-featured API using `word.UseWordDocument(...)` returning `IWordDocument`. Uses COM interop. For general info see [word.md](word.md).

---

## Opening Word Documents

### `word.UseWordDocument(string path)`

Opens a Word document with default options (create if not exists = true, auto-save = true).
Returns `IWordDocument` (disposable — use with `using`).

```csharp
using var doc = word.UseWordDocument("report.docx");
```

### `word.UseWordDocument(WordUseOptions options)`

Full control over how the document is opened.

```csharp
using var doc = word.UseWordDocument(new WordUseOptions
{
    Path = "report.docx",
    CreateIfNotExist = true,
    ReadOnly = false,
    AutoSave = true,
    SensitivityOperation = WordLabelOperation.None,
    SensitivityLabel = null
});
```

#### `WordUseOptions` Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `Path` | `string` | — | Path of the Word file |
| `CreateIfNotExist` | `bool` | `true` | Create the file if it does not exist |
| `ReadOnly` | `bool` | `false` | Open the document read-only |
| `AutoSave` | `bool` | `true` | Save changes when done |
| `SensitivityOperation` | `WordLabelOperation` | `None` | Sensitivity label operation (`None`, `Add`, `Clear`) |
| `SensitivityLabel` | `IWordLabelObject` | `null` | Sensitivity label to apply (used when `SensitivityOperation` is `Add`) |

---

## Text Operations

### AppendText

Writes text in the Word document at the current caret's position.

```csharp
void AppendText(this IWordDocument wordDocument, string text, bool addNewLineBeforeText = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `string` | — | Text to be written |
| `addNewLineBeforeText` | `bool` | `true` | Insert a line break after the existing text before appending |

```csharp
doc.AppendText("First paragraph.");
doc.AppendText("Second paragraph on a new line.", true);
doc.AppendText(" Appended inline.", false);
```

### ReadText

Reads all text from a Word document.

```csharp
string ReadText(this IWordDocument wordDocument);
```

Returns the full text content of the document.

```csharp
string content = doc.ReadText();
Log($"Document has {content.Length} characters.");
```

### ReplaceTextInDocument

Replaces occurrences of a text string within a Word document.

```csharp
bool ReplaceTextInDocument(this IWordDocument wordDocument, string searchFor, string replaceWith, bool replaceAll = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `searchFor` | `string` | — | Text to find (max 256 characters) |
| `replaceWith` | `string` | — | Replacement text (max 255 characters) |
| `replaceAll` | `bool` | `true` | If `true`, replace all occurrences; if `false`, only the first |

Returns `true` if the operation was successful.

```csharp
bool found = doc.ReplaceTextInDocument("{{CustomerName}}", "Acme Corp");
bool first = doc.ReplaceTextInDocument("old text", "new text", replaceAll: false);
```

---

## Bookmark Operations

### SetBookmarkContent

Sets the text content of a named bookmark in the document.

```csharp
void SetBookmarkContent(this IWordDocument wordDocument, string bookmarkName, string bookmarkText);
```

| Parameter | Type | Description |
|---|---|---|
| `bookmarkName` | `string` | Bookmark name as defined in the document |
| `bookmarkText` | `string` | Text to set inside the bookmark |

```csharp
doc.SetBookmarkContent("CompanyName", "Acme Corp");
doc.SetBookmarkContent("InvoiceDate", DateTime.Now.ToString("yyyy-MM-dd"));
```

---

## Hyperlink Operations

### AddHyperlinkToDocument

Adds a hyperlink to a Word document. Multiple overloads for different positioning strategies.

#### At end of document (default)

```csharp
bool AddHyperlinkToDocument(this IWordDocument wordDocument, string textToDisplay, string address);
```

```csharp
doc.AddHyperlinkToDocument("Visit UiPath", "https://uipath.com");
```

#### At start or end of document

```csharp
bool AddHyperlinkToDocument(this IWordDocument wordDocument, string textToDisplay, string address, Position positionWhereToInsert);
```

```csharp
doc.AddHyperlinkToDocument("Visit UiPath", "https://uipath.com", Position.Start);
```

#### Relative to a text

```csharp
bool AddHyperlinkToDocument(this IWordDocument wordDocument, string textToDisplay, string address, Position positionWhereToInsert, string textToSearchFor);
```

```csharp
doc.AddHyperlinkToDocument("Click here", "https://uipath.com", Position.After, "For more info");
```

#### Full control

```csharp
bool AddHyperlinkToDocument(this IWordDocument wordDocument, string textToDisplay, string address, InsertHyperlinkRelativeToType insertRelativeTo, Position positionWhereToInsert, string textToSearchFor);
```

| Parameter | Type | Description |
|---|---|---|
| `textToDisplay` | `string` | Display text for the hyperlink |
| `address` | `string` | URL/address of the hyperlink |
| `insertRelativeTo` | `InsertHyperlinkRelativeToType` | `Document` or `Text` |
| `positionWhereToInsert` | `Position` | Where to insert (`Start`, `End`, `Before`, `After`, `Replace`) |
| `textToSearchFor` | `string` | Text relative to which to insert (when `insertRelativeTo` is `Text`) |

Returns `true` if successful.

---

## Picture Operations

### AddPicture

Adds a picture to a Word document. Multiple overloads for different positioning strategies.

#### At end of document (default)

```csharp
void AddPicture(this IWordDocument wordDocument, string pictureToInsert);
```

```csharp
doc.AddPicture(@"C:\Images\logo.png");
```

#### At start or end of document

```csharp
void AddPicture(this IWordDocument wordDocument, string pictureToInsert, Position positionWhereToInsert);
```

```csharp
doc.AddPicture(@"C:\Images\header.png", Position.Start);
```

#### Relative to a bookmark

```csharp
void AddPicture(this IWordDocument wordDocument, string pictureToInsert, string bookmarkToSearchFor, Position positionWhereToInsert);
```

| Parameter | Type | Description |
|---|---|---|
| `bookmarkToSearchFor` | `string` | Bookmark name relative to which to insert |
| `positionWhereToInsert` | `Position` | `Before`, `After`, or `Replace` (replaces the bookmark with the image) |

```csharp
doc.AddPicture(@"C:\Images\signature.png", "SignatureBookmark", Position.Replace);
```

#### Relative to text

```csharp
void AddPicture(this IWordDocument wordDocument, string pictureToInsert, string textToSearchFor, Occurrence textOccurrence, int? occurenceIndex, Position positionWhereToInsert);
```

| Parameter | Type | Description |
|---|---|---|
| `textToSearchFor` | `string` | Text relative to which to insert the image |
| `textOccurrence` | `Occurrence` | `All`, `First`, `Last`, or `Specific` |
| `occurenceIndex` | `int?` | Index when `textOccurrence` is `Specific` |
| `positionWhereToInsert` | `Position` | `Before`, `After`, or `Replace` |

```csharp
doc.AddPicture(@"C:\Images\chart.png", "Insert chart here", Occurrence.First, null, Position.Replace);
```

### ReplacePicture

Replaces pictures in a Word document based on their Alt Text.

```csharp
void ReplacePicture(this IWordDocument wordDocument, string findPicturesWithAltText, string replaceWithPicture);
```

| Parameter | Type | Description |
|---|---|---|
| `findPicturesWithAltText` | `string` | Alt Text of the picture(s) to replace |
| `replaceWithPicture` | `string` | File path of the replacement image |

```csharp
doc.ReplacePicture("company_logo", @"C:\Images\new_logo.png");
```

---

## DataTable Operations

### InsertDataTableInDocument

Inserts a DataTable into a Word document. Multiple overloads for different positioning strategies.

#### At end of document (default)

```csharp
void InsertDataTableInDocument(this IWordDocument wordDocument, DataTable tableToInsert);
```

```csharp
doc.InsertDataTableInDocument(dataTable);
```

#### At start or end of document

```csharp
void InsertDataTableInDocument(this IWordDocument wordDocument, DataTable tableToInsert, Position positionWhereToInsert);
```

```csharp
doc.InsertDataTableInDocument(dataTable, Position.End);
```

#### Relative to a bookmark

```csharp
void InsertDataTableInDocument(this IWordDocument wordDocument, DataTable tableToInsert, string bookmarkToSearchFor, Position positionWhereToInsert);
```

```csharp
doc.InsertDataTableInDocument(dataTable, "TablePlaceholder", Position.Replace);
```

#### Relative to text

```csharp
void InsertDataTableInDocument(this IWordDocument wordDocument, DataTable tableToInsert, string textToSearchFor, Occurrence textOccurrence, int? occurenceIndex, Position positionWhereToInsert);
```

| Parameter | Type | Description |
|---|---|---|
| `tableToInsert` | `DataTable` | The DataTable to insert |
| `textToSearchFor` | `string` | Text relative to which to insert |
| `textOccurrence` | `Occurrence` | `All`, `First`, `Last`, or `Specific` |
| `occurenceIndex` | `int?` | Index when `textOccurrence` is `Specific` |
| `positionWhereToInsert` | `Position` | `Before`, `After`, or `Replace` |

```csharp
doc.InsertDataTableInDocument(dataTable, "Items", Occurrence.First, null, Position.After);
```

---

## Clipboard Operations

### PasteChartPictureIntoDocument

Pastes a chart or image from the clipboard into a Word document.

```csharp
bool PasteChartPictureIntoDocument(this IWordDocument wordDocument, PasteRelativeToType pasteRelativeTo, Position positionWhereToPaste, string textToSearchFor, PasteOptionType pasteOption);
```

| Parameter | Type | Description |
|---|---|---|
| `pasteRelativeTo` | `PasteRelativeToType` | `Document` or `Text` |
| `positionWhereToPaste` | `Position` | Position relative to target |
| `textToSearchFor` | `string` | Text relative to which to paste (when `pasteRelativeTo` is `Text`) |
| `pasteOption` | `PasteOptionType` | `EmbedData`, `LinkData`, or `Picture` |

Returns `true` if the paste was successful.

```csharp
// Paste at end of document as embedded data
doc.PasteChartPictureIntoDocument(PasteRelativeToType.Document, Position.End, null, PasteOptionType.EmbedData);

// Paste after specific text as picture
doc.PasteChartPictureIntoDocument(PasteRelativeToType.Text, Position.After, "Chart placeholder", PasteOptionType.Picture);
```

---

## Save and Export

### SaveDocumentAs

Saves a Word document in a different format.

```csharp
void SaveDocumentAs(this IWordDocument wordDocument, WordSaveAsType saveAsType, string saveAsFile, bool replaceExisting = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `saveAsType` | `WordSaveAsType` | — | Target format |
| `saveAsFile` | `string` | — | Full path for the new file |
| `replaceExisting` | `bool` | `true` | Replace existing file of the same name |

**`WordSaveAsType` values:**

| Value | Format |
|---|---|
| `XmlDocument` | .docx |
| `MacroEnabledDocument` | .docm |
| `OldDocument` | .doc |
| `WebPage` | .html |
| `FilteredWebPage` | .html (filtered) |
| `RichText` | .rtf |
| `PlainText` | .txt |

```csharp
doc.SaveDocumentAs(WordSaveAsType.XmlDocument, @"C:\Output\report_copy.docx");
doc.SaveDocumentAs(WordSaveAsType.RichText, @"C:\Output\report.rtf");
```

### SaveAsPDF

Exports a Word document to PDF.

```csharp
void SaveAsPDF(this IWordDocument wordDocument, string filePathToSaveAs, bool replaceExisting = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filePathToSaveAs` | `string` | — | PDF output file path |
| `replaceExisting` | `bool` | `true` | Replace existing file of the same name |

```csharp
doc.SaveAsPDF(@"C:\Output\report.pdf");
```

---

## Sensitivity Labels

### AddSensitivityLabel

Adds a sensitivity label to the document.

```csharp
void AddSensitivityLabel(this IWordDocument handle, IWordLabelObject label);
```

| Parameter | Type | Description |
|---|---|---|
| `label` | `IWordLabelObject` | Label object with at least `LabelId` set |

**`IWordLabelObject` properties:**

| Property | Type | Description |
|---|---|---|
| `LabelId` | `string` | Sensitivity label ID (required) |
| `Justification` | `string` | Justification for changing the label |

### GetSensitivityLabel

Retrieves the sensitivity label from a document.

```csharp
IWordLabelObject GetSensitivityLabel(this IWordDocument handle);
```

Returns an `IWordLabelObject` with the document's current sensitivity label.

```csharp
IWordLabelObject label = doc.GetSensitivityLabel();
if (label != null)
{
    Log($"Label ID: {label.LabelId}");
}
```
