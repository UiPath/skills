# PowerPoint — Windows (Interop) API

Full-featured PowerPoint API using `powerpoint.UsePowerPointPresentation(...)` returning `IPresentation`. Windows-only, requires PowerPoint installed. For general info see [powerpoint.md](powerpoint.md).

---

## Opening/Creating Presentations

### `UsePowerPointPresentation(UseOptions options)`

Opens or creates a PowerPoint file with full configuration.

```csharp
IPresentation presentation = powerpoint.UsePowerPointPresentation(new UseOptions
{
    Path = @"C:\Reports\report.pptx",
    CreateIfNotExist = true,
    AutoSave = true,
    ReadOnly = false,
    Password = null,
    EditPassword = null,
    SensitivityOperation = PptLabelOperation.None,
    SensitivityLabel = null
});
```

#### UseOptions Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `Path` | `string` | — | Path of the PowerPoint file (required) |
| `Password` | `string` | `null` | Password to open protected file |
| `EditPassword` | `string` | `null` | Edit password for the file |
| `CreateIfNotExist` | `bool` | `true` | Create the file if it does not exist |
| `ReadOnly` | `bool` | `false` | Open in read-only mode |
| `AutoSave` | `bool` | `true` | Save changes automatically when disposed |
| `SensitivityOperation` | `PptLabelOperation` | `None` | Sensitivity label operation (`None`, `Add`, `Clear`) |
| `SensitivityLabel` | `PptLabelObject` | `null` | Label object (used only when `SensitivityOperation` is `Add`) |

### `UsePowerPointPresentation(string path)`

Opens or creates a file with defaults (auto-save on, create if not exists).

```csharp
IPresentation presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\report.pptx");
```

### `UsePowerPointPresentation(string path, bool saveChanges, bool createIfNotExist)`

Opens or creates a file with explicit save and create settings.

```csharp
IPresentation presentation = powerpoint.UsePowerPointPresentation(
    @"C:\Reports\report.pptx", saveChanges: true, createIfNotExist: true);
```

---

## IPresentation Properties

| Property | Type | Description |
|---|---|---|
| `NumberOfSlides` | `int` | Current number of slides |
| `Location` | `string` | File path or URI of the presentation |
| `Hwnd` | `int` | Window handle of the presentation |
| `Pid` | `int` | PID of the PowerPoint process |
| `SlideOperations` | `ISlideOperations` | Low-level slide operations (used internally by extension methods) |
| `SlideContentOperations` | `ISlideContentOperations` | Low-level content formatting operations |

---

## Slide Management

### AddNewSlide

Inserts a new slide. Returns the 1-based index at which the slide was inserted.

```csharp
int AddNewSlide(this IPresentation presentation, string layout,
    InsertPositionType addAs = InsertPositionType.End,
    string slideMaster = "(default)");

int AddNewSlide(this IPresentation presentation, string layout, int insertPosition,
    InsertPositionType addAs = InsertPositionType.End,
    string slideMaster = "(default)");
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `layout` | `string` | — | Name of the layout (e.g., `"Title Slide"`, `"Title and Content"`, `"Blank"`) |
| `insertPosition` | `int` | — | 1-based position for the new slide (when `addAs` is `SpecifiedIndex`) |
| `addAs` | `InsertPositionType` | `End` | `Beginning`, `End`, or `SpecifiedIndex` |
| `slideMaster` | `string` | `"(default)"` | Slide master containing the layout |

### DeleteSlide

Deletes a slide at the specified 1-based index.

```csharp
void DeleteSlide(this IPresentation presentation, int slideNumber);
```

### CopyPasteSlide

Copies (or moves) a slide from one presentation to another.

```csharp
void CopyPasteSlide(this IPresentation sourcePresentation, IPresentation destinationPresentation,
    int slideToCopy, int whereToInsert, bool move = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `slideToCopy` | `int` | — | 1-based index of the slide to copy |
| `whereToInsert` | `int` | — | 1-based index in destination for the copied slide |
| `move` | `bool` | `false` | If `true`, removes the slide from the source after copying |

---

## Text Operations

### AddTextToSlide

Inserts text into a named shape/placeholder on a slide.

```csharp
void AddTextToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, string textToAdd, bool clearExistingText = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `slideNumber` | `int` | — | 1-based slide index |
| `contentPlaceholder` | `string` | — | Name of the shape/placeholder |
| `textToAdd` | `string` | — | Text to insert |
| `clearExistingText` | `bool` | `true` | Clear existing text before adding |

### ReplaceTextInPresentation

Replaces text across the entire presentation. Returns the number of replacements made.

```csharp
int ReplaceTextInPresentation(this IPresentation presentation, string findWhat,
    string replaceWith, bool matchCase = false, bool wholeWordsOnly = false,
    bool replaceAll = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `findWhat` | `string` | — | Text to search for |
| `replaceWith` | `string` | — | Replacement text |
| `matchCase` | `bool` | `false` | Match specific capitalization |
| `wholeWordsOnly` | `bool` | `false` | Replace entire words only (disabled for non-alphanumeric characters) |
| `replaceAll` | `bool` | `true` | Replace all occurrences; if `false`, only the first |

---

## DataTable Operations

### AddDataTableToSlide

Inserts a DataTable into a named shape/placeholder on a slide.

```csharp
// Basic — create new table
void AddDataTableToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, DataTable tableToAdd,
    TableAppendMode behaviour = TableAppendMode.CreateNewTable);

// With headers control
void AddDataTableToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, DataTable tableToAdd,
    TableAppendMode behaviour = TableAppendMode.CreateNewTable,
    bool excludeSourceHeaders = false);

// Full — with row/column offset for overwrite mode
void AddDataTableToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, DataTable tableToAdd,
    bool excludeSourceHeaders, TableAppendMode behaviour,
    int overwriteStartingInRow, int overwriteStartingInColumn);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `slideNumber` | `int` | — | 1-based slide index |
| `contentPlaceholder` | `string` | — | Name of the shape/placeholder |
| `tableToAdd` | `DataTable` | — | DataTable to insert |
| `behaviour` | `TableAppendMode` | `CreateNewTable` | `CreateNewTable`, `AppendToTable`, or `OverwriteExistingData` |
| `excludeSourceHeaders` | `bool` | `false` | Skip the first row (headers) of the source |
| `overwriteStartingInRow` | `int` | — | Row offset for overwrite (0 = header row, 1 = first data row) |
| `overwriteStartingInColumn` | `int` | — | Column offset for overwrite (1 = first column) |

---

## Media & Files

### AddImageOrVideoToSlide

Replaces a shape/placeholder with an image or video.

```csharp
// Simple — use shape position and size
void AddImageOrVideoToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, string imageOrVideoPath);

// With positioning — specify exact position and size in points
void AddImageOrVideoToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, string imageOrVideoPath,
    float? left, float? top, float? width, float? height, string newShapeName);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentPlaceholder` | `string` | Name of the shape to replace |
| `imageOrVideoPath` | `string` | Absolute path to the image or video file |
| `left` | `float?` | Horizontal position in points |
| `top` | `float?` | Vertical position in points |
| `width` | `float?` | Width in points |
| `height` | `float?` | Height in points |
| `newShapeName` | `string` | New name for the inserted shape |

### AddFileToSlide

Inserts a file into a slide, displayed as an icon.

```csharp
// Simple — insert at default position
void AddFileToSlide(this IPresentation presentation, int slideNumber, string fileToAdd);

// With placeholder and label
void AddFileToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, string fileToAdd, string iconLabel);

// With new shape name
void AddFileToSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, string fileToAdd, string iconLabel, string newShapeName);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentPlaceholder` | `string` | Name of the shape where to insert |
| `fileToAdd` | `string` | Absolute path to the file |
| `iconLabel` | `string` | Caption for the icon (defaults to file name) |
| `newShapeName` | `string` | New name for the shape |

---

## Clipboard

### PasteItemIntoSlide

Pastes clipboard content into a slide placeholder.

```csharp
// Simple
void PasteItemIntoSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder);

// With positioning
void PasteItemIntoSlide(this IPresentation presentation, int slideNumber,
    string contentPlaceholder, float? left, float? top, float? width, float? height,
    string newShapeName);
```

---

## Save & Export

### SavePresentationAs

Saves the presentation as a new file in the specified format.

```csharp
void SavePresentationAs(this IPresentation presentation, string filePath,
    PresentationSaveAsType presentationSaveAsType = PresentationSaveAsType.XmlPresentation,
    bool replaceExisting = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filePath` | `string` | — | Destination file path |
| `presentationSaveAsType` | `PresentationSaveAsType` | `XmlPresentation` | `XmlPresentation` (.pptx), `MacroEnabledPresentation` (.pptm), `OldPresentation` (.ppt) |
| `replaceExisting` | `bool` | `true` | Replace if file already exists |

### SavePresentationAsPDF

Exports the presentation to PDF.

```csharp
void SavePresentationAsPDF(this IPresentation presentation, string pathToDestinationPDF,
    bool replaceExisting = true);
```

---

## Macros

### RunPresentationMacro

Runs a macro in a macro-enabled presentation. Returns the macro's return value (if any).

```csharp
object RunPresentationMacro(this IPresentation presentation, string macroName,
    IList<object> macroArguments);
```

| Parameter | Type | Description |
|---|---|---|
| `macroName` | `string` | Name of the macro to run |
| `macroArguments` | `IList<object>` | Input arguments for the macro |

---

## Formatting

### FormatSlideContent

Applies formatting modifications to a named shape on a slide.

```csharp
void FormatSlideContent(this IPresentation presentation, int slideNumber,
    string contentToModify, List<IFormatSlideModicationModel> modifications);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentToModify` | `string` | Name of the shape to modify |
| `modifications` | `List<IFormatSlideModicationModel>` | List of modification descriptors |

#### Available Modification Models

| Model | Constructor | Description |
|---|---|---|
| `FontSizeModificationModel` | `new FontSizeModificationModel(int fontSize)` | Changes font size |
| `ZIndexModificationModel` | `new ZIndexModificationModel(ZIndexChangeType changeType)` | Brings to front or sends to back |
| `ChangeShapeNameModel` | `new ChangeShapeNameModel(string newShapeName)` | Renames the shape |

---

## Sensitivity Labels

### AddSensitivityLabel

Adds or updates a sensitivity label on the presentation.

```csharp
void AddSensitivityLabel(this IPresentation presentation, IPptLabelObject label);
```

### GetSensitivityLabel

Retrieves the sensitivity label from the presentation.

```csharp
IPptLabelObject GetSensitivityLabel(this IPresentation presentation);
```

#### PptLabelObject Properties

| Property | Type | Description |
|---|---|---|
| `LabelId` | `string` | The sensitivity label ID |
| `Justification` | `string` | Justification for the label |

---

## IPresentation Direct Methods

These methods are available directly on the `IPresentation` object (not as extension methods):

```csharp
presentation.ClosePresentation();           // Close and dispose
presentation.BringToFront();                // Bring window to front
presentation.ValidateSlideIndex(int index); // Throws if index out of bounds
presentation.SaveAsPdf(string filePath);    // Direct PDF export
presentation.SaveAs(PresentationSaveAsType type, string filePath, bool replaceExisting);
object result = presentation.RunMacro(string macroName, IList<object> parameters);
```

---

## ISlideOperations Direct Methods

Available via `presentation.SlideOperations`. These are the low-level methods used internally by the extension methods above. Additional methods not exposed through extension methods:

| Method | Return | Description |
|---|---|---|
| `GetText(int slideIndex, string shapeName)` | `string` | Gets text from a shape |
| `GetTable(int slideIndex, string shapeName)` | `DataTable` | Gets table data from a shape |
| `GetLayout(int slideIndex)` | `string` | Gets the layout name of a slide |
| `GetShapeCount(int slideIndex)` | `int` | Gets number of shapes on a slide |
| `GetFontSize(int slideIndex, string shapeName)` | `float` | Gets font size of a shape |
| `GetZIndex(int slideIndex, string shapeName)` | `int` | Gets z-index of a shape |
| `GetCurrentSlideNumber()` | `int` | Gets the current slide number |
| `CopySlides(int insertIndex, string sourceFile, int firstSlide, int lastSlide)` | `void` | Copies slides from another file |
| `DuplicateSlides(int startSlide, int endSlide, int count)` | `void` | Duplicates a range of slides |
| `ExportToPdf(string fileName, int slideStartNo, int slideEndNo)` | `void` | Exports a range of slides to PDF (0-0 = all) |
| `ReplaceInSlide(int slideNumber, Dictionary<string, string> values)` | `int` | Batch replace text pairs in a single slide |
| `ReplaceImages(int slideNumber, Dictionary<string, string> images)` | `int` | Replace placeholders with base64 images |
| `InsertEmptySlide(int insertPosition)` | `void` | Insert a slide without specifying a layout |

---

## ISlideContentOperations Direct Methods

Available via `presentation.SlideContentOperations`:

| Method | Description |
|---|---|
| `ChangeFontSize(int slideNumber, string contentPlaceholder, int fontSize)` | Change font size of a shape |
| `BringToFront(int slideNumber, string contentPlaceholder)` | Bring shape to front |
| `SendToBack(int slideNumber, string contentPlaceholder)` | Send shape to back |
| `ChangeShapeName(int slideNumber, string contentPlaceholder, string newShapeName)` | Rename a shape |
