# PowerPoint — Portable (OpenXml) API

Cross-platform PowerPoint API using `powerpoint.UsePresentationDocument(...)` returning `IPresentationDocumentHandle`. Works without PowerPoint installed. For general info see [powerpoint.md](powerpoint.md).

---

## Opening Presentations

### `UsePresentationDocument(string path)`

Opens a PowerPoint document using OpenXml. The returned handle is `IDisposable` and should be disposed when done.

```csharp
using var doc = powerpoint.UsePresentationDocument(@"C:\Reports\report.pptx");
```

**Note:** The portable API does not support creating new files — the file must already exist.

---

## Slide Management

### AddNewSlide

Inserts a new slide. Returns the 1-based index at which the slide was inserted (or `null` if the layout was not found).

```csharp
int? AddNewSlide(this IPresentationDocumentHandle presentation, string layout,
    InsertPositionType addAs = InsertPositionType.End,
    string slideMaster = "(default)");

int? AddNewSlide(this IPresentationDocumentHandle presentation, int? insertPosition,
    string layout, InsertPositionType addAs = InsertPositionType.End,
    string slideMaster = "(default)");
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `layout` | `string` | — | Name of the layout (e.g., `"Title Slide"`, `"Blank"`) |
| `insertPosition` | `int?` | — | 1-based position (when `addAs` is `SpecifiedIndex`) |
| `addAs` | `InsertPositionType` | `End` | `Beginning`, `End`, or `SpecifiedIndex` |
| `slideMaster` | `string` | `"(default)"` | Slide master containing the layout |

### DeleteSlide

Deletes a slide at the specified 1-based index.

```csharp
void DeleteSlide(this IPresentationDocumentHandle presentation, int slideNumber);
```

---

## Text Operations

### AddTextToSlide

Inserts text into a named shape/placeholder.

```csharp
void AddTextToSlide(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentPlaceholder, string textToAdd, bool clearExisting = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `slideNumber` | `int` | — | 1-based slide index |
| `contentPlaceholder` | `string` | — | Name of the shape/placeholder |
| `textToAdd` | `string` | — | Text to insert |
| `clearExisting` | `bool` | `false` | Clear existing text before adding |

**Note:** Default for `clearExisting` is `false` in the portable API (vs `true` in the Windows API).

### ReplaceTextInPresentation

Replaces text across the entire presentation. Returns the number of replacements made.

```csharp
int ReplaceTextInPresentation(this IPresentationDocumentHandle presentation,
    string findWhat, string replaceWith, bool matchCase = false,
    bool wholeWordsOnly = false, bool replaceAll = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `findWhat` | `string` | — | Text to search for |
| `replaceWith` | `string` | — | Replacement text |
| `matchCase` | `bool` | `false` | Match specific capitalization |
| `wholeWordsOnly` | `bool` | `false` | Replace entire words only |
| `replaceAll` | `bool` | `true` | Replace all occurrences; if `false`, only the first |

---

## DataTable Operations

### AddDataTableToSlide

Inserts a DataTable into a named shape/placeholder.

```csharp
// With row/column offset
void AddDataTableToSlide(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentPlaceholder, DataTable tableToAdd, bool excludeHeaders,
    TableAppendMode behaviour, int startRow, int startColumn);

// Without row/column offset
void AddDataTableToSlide(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentPlaceholder, DataTable tableToAdd, bool excludeHeaders,
    TableAppendMode behaviour);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentPlaceholder` | `string` | Name of the shape/placeholder |
| `tableToAdd` | `DataTable` | DataTable to insert |
| `excludeHeaders` | `bool` | Skip the header row of the source |
| `behaviour` | `TableAppendMode` | `CreateNewTable`, `AppendToTable`, or `OverwriteExistingData` |
| `startRow` | `int` | Row offset for overwrite (0 = header, 1 = first data row) |
| `startColumn` | `int` | Column offset for overwrite (1 = first column) |

---

## Media

### AddImageOrVideoToSlide

Replaces a shape/placeholder with an image or video.

```csharp
// Simple — use shape position and size
void AddImageOrVideoToSlide(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentPlaceholder, string imageOrVideoFile);

// With positioning
void AddImageOrVideoToSlide(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentPlaceholder, string imageOrVideoFile,
    float? left, float? top, float? width, float? height, string newShapeName);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentPlaceholder` | `string` | Name of the shape to replace |
| `imageOrVideoFile` | `string` | Absolute path to the image or video file |
| `left` | `float?` | Horizontal position in points |
| `top` | `float?` | Vertical position in points |
| `width` | `float?` | Width in points |
| `height` | `float?` | Height in points |
| `newShapeName` | `string` | New name for the inserted shape |

---

## Formatting

### FormatSlideContent

Applies formatting modifications to a named shape.

```csharp
void FormatSlideContent(this IPresentationDocumentHandle presentation, int slideNumber,
    string contentToModify, List<ISlideContentModicationModel> modifications);
```

| Parameter | Type | Description |
|---|---|---|
| `slideNumber` | `int` | 1-based slide index |
| `contentToModify` | `string` | Name of the shape to modify |
| `modifications` | `List<ISlideContentModicationModel>` | List of modification descriptors |

#### Available Modification Models (Portable)

| Model | Constructor | Description |
|---|---|---|
| `ShapeFontSizeModificationModel` | `new ShapeFontSizeModificationModel(int fontSize)` | Changes font size |
| `ShapeZOrderModificationModel` | `new ShapeZOrderModificationModel(ZOrderChangeType changeType)` | Brings to front or sends to back |
| `ShapeChangeNameModel` | `new ShapeChangeNameModel(string newShapeName)` | Renames the shape |

**Note:** These are different types than the Windows API modification models (`ISlideContentModicationModel` vs `IFormatSlideModicationModel`).

---

## Portable vs Windows API Comparison

| Feature | Windows API | Portable API |
|---|---|---|
| Create new files | Yes (`CreateIfNotExist`) | No |
| Save/SaveAs/PDF export | Yes | No (auto-saves on dispose) |
| Macros | Yes | No |
| Copy/paste slides | Yes | No |
| Paste from clipboard | Yes | No |
| Add files as icons | Yes | No |
| Sensitivity labels | Yes | No |
| Get text/table from shapes | Yes (via `SlideOperations`) | No |
| Cross-platform | No (Windows only) | Yes |
| Requires PowerPoint | Yes | No |
