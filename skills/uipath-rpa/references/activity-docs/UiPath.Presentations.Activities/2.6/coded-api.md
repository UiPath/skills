# Presentations — Coded Workflow API

`UiPath.Presentations.Activities`

Provides PowerPoint presentation operations for coded workflows using both OpenXml (cross-platform) and COM Interop (Windows-only) engines.

**Service accessor:** `powerpoint` (type `IPresentationsService`)
**Required package:** `"UiPath.Presentations.Activities": "*"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```
System
System.Collections.Generic
System.Data
UiPath.Presentations
UiPath.Presentations.Activities
UiPath.Presentations.Activities.API
UiPath.Presentations.Activities.API.Models
```

## Service Overview

The `powerpoint` service provides:

- **Handle-based API** — Call `UsePresentationDocument(...)` or `UsePowerPointPresentation(...)` to open/create a PowerPoint file and receive a disposable handle
- **OpenXml engine (cross-platform)** — `UsePresentationDocument` returns `IPresentationDocumentHandle` with extension methods for slide operations
- **COM Interop engine (Windows-only)** — `UsePowerPointPresentation` returns `IPresentation` with extension methods for richer operations including macros, Save As, PDF export, and sensitivity labels

---

## Opening / Creating Presentations (Cross-Platform — OpenXml)

These methods use the OpenXml engine and work on all platforms.

### `IPresentationDocumentHandle UsePresentationDocument(string path)`

Opens a PowerPoint document using OpenXml. If the document does not exist, a new one is created.

**Parameters:**
- `path` (`string`) — Path of the document

**Returns:** `IPresentationDocumentHandle` — Disposable handle to the presentation. Use with `using` statement.

```csharp
using var ppt = powerpoint.UsePresentationDocument("report.pptx");
```

### `IPresentationDocumentHandle UsePresentationDocument(string path, bool createNew)`

Opens a PowerPoint document using OpenXml. Controls whether a new file is created if it does not exist.

**Parameters:**
- `path` (`string`) — Path of the document
- `createNew` (`bool`) — If the document does not exist, determines if a new document is created. The single-parameter overload `UsePresentationDocument(path)` always creates if missing; use this overload with `false` to open existing files only

**Returns:** `IPresentationDocumentHandle` — Disposable handle to the presentation.

```csharp
// Open existing only — throws if file does not exist
using var ppt = powerpoint.UsePresentationDocument("existing.pptx", createNew: false);
```

### `IPresentationDocumentHandle UsePresentationDocument(PresentationCreateOptions options)`

Creates a new PowerPoint document using OpenXml with full control over creation options, including template usage, metadata preservation, and conflict resolution.

**Parameters:**
- `options` (`PresentationCreateOptions`) — Options for creating the presentation

**Returns:** `IPresentationDocumentHandle` — Disposable handle to the presentation.

```csharp
using var ppt = powerpoint.UsePresentationDocument(new PresentationCreateOptions
{
    Path = "report.pptx",
    TemplatePath = "template.potx",
    PreserveTemplateMetadata = false,
    ConflictResolution = ConflictBehavior.Replace,
    CreateNew = true
});
```

---

## Opening / Creating Presentations (Windows-Only — COM Interop)

These methods use the PowerPoint COM Interop engine. **Windows only.**

### `IPresentation UsePowerPointPresentation(string path)`

Opens or creates a PowerPoint file.

**Parameters:**
- `path` (`string`) — The path of the PowerPoint file

**Returns:** `IPresentation` — Disposable handle for presentation operations.

```csharp
using var ppt = powerpoint.UsePowerPointPresentation("report.pptx");
```

### `IPresentation UsePowerPointPresentation(string path, bool saveChanges, bool createIfNotExist)`

Opens or creates a PowerPoint file with save and creation control.

**Parameters:**
- `path` (`string`) — The path of the PowerPoint file
- `saveChanges` (`bool`) — `true` to save changes after operations
- `createIfNotExist` (`bool`) — `true` to create the file if it does not exist

**Returns:** `IPresentation` — Disposable handle for presentation operations.

```csharp
using var ppt = powerpoint.UsePowerPointPresentation("report.pptx",
    saveChanges: true, createIfNotExist: false);
```

### `IPresentation UsePowerPointPresentation(UseOptions options)`

Opens or creates a PowerPoint file with full options control.

**Parameters:**
- `options` (`UseOptions`) — Options for opening or creating the file

**Returns:** `IPresentation` — Disposable handle for presentation operations.

```csharp
using var ppt = powerpoint.UsePowerPointPresentation(new UseOptions
{
    Path = "report.pptx",
    Password = "secret",
    AutoSave = true,
    CreateIfNotExist = true,
    ReadOnly = false
});
```

---

## Handle Types

### `IPresentationDocumentHandle` (Cross-Platform)

Handle to a PowerPoint presentation opened via OpenXml. All operations are provided as extension methods.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Extension Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `AddTextToSlide(int slideNumber, string contentPlaceholder, string textToAdd, bool clearExisting = false)` | `void` | Inserts text into a placeholder on a slide |
| `DeleteSlide(int slideNumber)` | `void` | Deletes a slide at the specified position |
| `AddNewSlide(string layout, InsertPositionType addAs = InsertPositionType.End, string slideMaster = "(default)")` | `int?` | Inserts a new slide and returns the position |
| `AddNewSlide(int insertPosition, string layout, InsertPositionType addAs = InsertPositionType.End, string slideMaster = "(default)")` | `int?` | Inserts a new slide at a specific position. **Note:** Although the underlying signature is `int?`, passing `null` will throw — always provide a positive integer |
| `AddDataTableToSlide(int slideNumber, string contentPlaceholder, DataTable tableToAdd, bool excludeHeaders, TableAppendMode behaviour, int startRow, int startColumn)` | `void` | Inserts a DataTable with row/column offsets |
| `AddDataTableToSlide(int slideNumber, string contentPlaceholder, DataTable tableToAdd, bool excludeHeaders, TableAppendMode behaviour)` | `void` | Inserts a DataTable into a placeholder |
| `ReplaceTextInPresentation(string findWhat, string replaceWith, bool matchCase = false, bool wholeWordsOnly = false, bool replaceAll = true)` | `int` | Replaces text occurrences; returns replacement count |
| `AddImageOrVideoToSlide(int slideNumber, string contentPlaceholder, string imageOrVideoFile)` | `void` | Replaces a placeholder with an image or video |
| `AddImageOrVideoToSlide(int slideNumber, string contentPlaceholder, string imageOrVideoFile, float? left, float? top, float? width, float? height, string newShapeName)` | `void` | Replaces a placeholder with media, with size/position control |
| `FormatSlideContent(int slideNumber, string contentToModify, List<ISlideContentModicationModel> modifications)` | `void` | Applies formatting modifications to slide content |

### `IPresentation` (Windows-Only)

Handle to a PowerPoint presentation opened via COM Interop. **Windows only.**

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` explicitly.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `NumberOfSlides` | `int` | The number of slides currently in the presentation |
| `Location` | `string` | The file path or URI of the presentation |
| `Hwnd` | `int` | Window handle for the presentation |
| `Pid` | `int` | PID of the PowerPoint process hosting the presentation |
| `SlideOperations` | `ISlideOperations` | Low-level slide operations. Prefer the extension methods below for coded workflows |
| `SlideContentOperations` | `ISlideContentOperations` | Low-level content operations. Prefer the extension methods below for coded workflows |

#### Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `BringToFront()` | `void` | Brings the presentation window to front and activates it |

> Additional public methods are also available on `IPresentation` but are not listed here. Use the extension methods below for `SaveAsPdf`, `SaveAs`, and `RunMacro` in coded workflows; call `ClosePresentation` and `ValidateSlideIndex` directly on `IPresentation` as needed (disposing the handle also closes the presentation).

#### Extension Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `AddTextToSlide(int slideNumber, string contentPlaceholder, string textToAdd, bool clearExistingText = true)` | `void` | Inserts text into a placeholder on a slide |
| `DeleteSlide(int slideNumber)` | `void` | Deletes a slide at the specified position |
| `AddNewSlide(string layout, InsertPositionType addAs = InsertPositionType.End, string slideMaster = "(default)")` | `int` | Inserts a new slide; returns computed insert position. **Note:** The current implementation does not pass the computed position to the underlying insert call — the slide may not be inserted at the position indicated by `addAs` |
| `AddNewSlide(string layout, int insertPosition, InsertPositionType addAs = InsertPositionType.End, string slideMaster = "(default)")` | `int` | Inserts a new slide at a specific position. **Note:** Parameter order is `(layout, insertPosition)` here vs `(insertPosition, layout)` in OpenXml |
| `CopyPasteSlide(IPresentation destinationPresentation, int slideToCopy, int whereToInsert, bool move = false)` | `void` | Copies/moves a slide to another presentation |
| `AddDataTableToSlide(int slideNumber, string contentPlaceholder, DataTable tableToAdd, TableAppendMode behaivour = TableAppendMode.CreateNewTable)` | `void` | Inserts a DataTable into a placeholder |
| `AddDataTableToSlide(int slideNumber, string contentPlaceholder, DataTable tableToAdd, TableAppendMode behaivour = TableAppendMode.CreateNewTable, bool excludeSourceHeaders = false)` | `void` | Inserts a DataTable with header exclusion option |
| `AddDataTableToSlide(int slideNumber, string contentPlaceholder, DataTable tableToAdd, bool excludeSourceHeaders, TableAppendMode behaivour, int overwriteStartingInRow, int overwriteStartingInColumn)` | `void` | Inserts a DataTable with row/column offsets |
| `ReplaceTextInPresentation(string findWhat, string replaceWith, bool matchCase = false, bool wholeWordsOnly = false, bool replaceAll = true)` | `int` | Replaces text occurrences; returns replacement count |
| `AddImageOrVideoToSlide(int slideNumber, string contentPlaceholder, string imageOrVideoPath)` | `void` | Replaces a placeholder with an image or video |
| `AddImageOrVideoToSlide(int slideNumber, string contentPlaceholder, string imageOrVideoPath, float? left, float? top, float? width, float? height, string newShapeName)` | `void` | Replaces a placeholder with media, with size/position control |
| `PasteItemIntoSlide(int slideNumber, string contentPlaceholder)` | `void` | Pastes clipboard content into a slide placeholder |
| `PasteItemIntoSlide(int slideNumber, string contentPlaceholder, float? left, float? top, float? width, float? height, string newShapeName)` | `void` | Pastes clipboard content with size/position control |
| `AddFileToSlide(int slideNumber, string fileToAdd)` | `void` | Inserts a file as an icon on a slide |
| `AddFileToSlide(int slideNumber, string contentPlaceholder, string fileToAdd, string iconLabel)` | `void` | Inserts a file into a placeholder with an icon label |
| `AddFileToSlide(int slideNumber, string contentPlaceholder, string fileToAdd, string iconLabel, string newShapeName)` | `void` | Inserts a file with icon label and custom shape name |
| `SavePresentationAs(string filePath, PresentationSaveAsType presentationSaveAsType = PresentationSaveAsType.XmlPresentation, bool replaceExisting = true)` | `void` | Saves presentation as a new file in specified format |
| `SavePresentationAsPDF(string pathToDestinationPDF, bool replaceExisting = true)` | `void` | Exports presentation to PDF |
| `RunPresentationMacro(string macroName, IList<object> macroArguments)` | `object` | Runs a macro and returns the result |
| `FormatSlideContent(int slideNumber, string contentToModify, List<IFormatSlideModicationModel> modifications)` | `void` | Applies formatting modifications to slide content |
| `AddSensitivityLabel(IPptLabelObject label)` | `void` | Applies a sensitivity label to the presentation |
| `GetSensitivityLabel()` | `IPptLabelObject` | Retrieves the sensitivity label from the presentation |

> **Note:** The COM `AddDataTableToSlide` parameter name `behaivour` is a known misspelling in the API. The OpenXml equivalent uses the correct spelling `behaviour`. Use the exact spelling shown above when calling COM methods.

---

## Options & Configuration Classes

### `PresentationCreateOptions`

Options for creating a new PowerPoint presentation (OpenXml engine).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Path` | `string` | `null` | Path of the PowerPoint file to create |
| `TemplatePath` | `string` | `null` | Path to a template file (.potx, .potm, .pptx, .pptm) to use as the base. When null/empty, an embedded default template is used |
| `PreserveTemplateMetadata` | `bool` | `true` | When true, keeps the original template's author and timestamp metadata. When false, replaces with current user and updates timestamps. Only relevant when TemplatePath is set |
| `ConflictResolution` | `ConflictBehavior` | `Skip` | How to handle the case when the file already exists |
| `CreateNew` | `bool` | `true` | If the document at Path does not exist, determines if a new document is created |

### `UseOptions`

Options for opening or creating PowerPoint files (Windows COM Interop engine).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Path` | `string` | `null` | Path of the PowerPoint file |
| `Password` | `string` | `null` | Password for the PowerPoint file |
| `EditPassword` | `string` | `null` | Edit password for the PowerPoint file |
| `CreateIfNotExist` | `bool` | `true` | If true, creates the file if it does not exist |
| `ReadOnly` | `bool` | `false` | If true, opens the presentation as read-only |
| `AutoSave` | `bool` | `true` | If true, saves changes after presentation operations |
| `SensitivityOperation` | `PptLabelOperation` | `None` | Sensitivity label operation to execute when opening/creating the file |
| `SensitivityLabel` | `PptLabelObject` | `null` | Sensitivity label object to apply. Only used if SensitivityOperation is `Add` |

### `IPptLabelObject` / `PptLabelObject`

Represents a sensitivity label to apply to a presentation (Windows-only).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `LabelId` | `string` | `null` | Sensitivity label ID |
| `Justification` | `string` | `null` | Justification for changing the label |

---

## Enum Reference

**`ConflictBehavior`**: `Replace`, `Fail`, `Skip`
- `Replace` — Deletes the existing file and creates a new one
- `Fail` — Throws an exception if the file already exists
- `Skip` — Keeps the existing file and opens it as-is (default)

**`InsertPositionType`**: `SpecifiedIndex`, `Beginning`, `End`
- `SpecifiedIndex` — Insert at a specific slide index
- `Beginning` — Insert at the start of the presentation
- `End` — Insert at the end of the presentation (default)

**`TableAppendMode`**: `CreateNewTable`, `AppendToTable`, `OverwriteExistingData`
- `CreateNewTable` — Completely replaces the target shape with a new table
- `AppendToTable` — Appends data to an existing table
- `OverwriteExistingData` — Overwrites specific cells in an existing table

**`PresentationSaveAsType`** (Windows-only): `XmlPresentation`, `MacroEnabledPresentation`, `OldPresentation`
- `XmlPresentation` — PowerPoint .pptx format (default)
- `MacroEnabledPresentation` — PowerPoint .pptm format
- `OldPresentation` — Legacy .ppt format

**`PptLabelOperation`** (Windows-only): `None`, `Add`, `Clear`
- `None` — No sensitivity label operation
- `Add` — Add or update the sensitivity label
- `Clear` — Remove the sensitivity label

**`ZOrderChangeType`** (OpenXml): `BringToFront`, `SendToBack` — Used with `ShapeZOrderModificationModel` in `FormatSlideContent` modifications

**`ZIndexChangeType`** (Windows): `BringToFront`, `SendToBack` — Used with `ZIndexModificationModel` in `FormatSlideContent` modifications

---

## Modification Models

> **Coded workflows limitation.** The built-in modification model types have `internal` constructors and cannot be instantiated directly from coded workflows. However, the `FormatSlideContent` extension method can still be used by providing custom implementations of the public interfaces described below.

### `ISlideContentModicationModel` (Cross-Platform)

Interface for slide content modifications used with `FormatSlideContent` (OpenXml engine). Built-in implementations (not directly constructible from coded workflows):

| Class | Constructor Parameters | Description |
|-------|----------------------|-------------|
| `ShapeZOrderModificationModel` | `ZOrderChangeType zOrderChange` | Changes a shape's Z-order (bring to front or send to back) |
| `ShapeFontSizeModificationModel` | `int fontSize` | Changes the font size of text in a shape |
| `ShapeChangeNameModel` | `string newName` | Renames a shape |

### `IFormatSlideModicationModel` (Windows-Only)

Interface for slide content modifications used with `FormatSlideContent` (COM Interop engine). Built-in implementations (not directly constructible from coded workflows):

| Class | Constructor Parameters | Description |
|-------|----------------------|-------------|
| `ZIndexModificationModel` | `ZIndexChangeType zIndexChange` | Changes a shape's Z-index (bring to front or send to back) |
| `FontSizeModificationModel` | `int fontSize` | Changes the font size of text in a shape |
| `ChangeShapeNameModel` | `string newName` | Renames a shape |

---

## Common Patterns

### Open a presentation and add text to a slide (cross-platform)

> **Engine difference:** `AddTextToSlide` defaults to `clearExisting: false` (OpenXml) vs `clearExistingText: true` (COM). When switching engines, explicitly pass this parameter to avoid unexpected append/replace behavior.

```csharp
[Workflow]
public void Execute()
{
    using var ppt = powerpoint.UsePresentationDocument("report.pptx");
    ppt.AddTextToSlide(1, "Title 1", "Quarterly Report", clearExisting: true);
    ppt.AddTextToSlide(1, "Content Placeholder 1", "Revenue grew 15% this quarter.");
}
```

### Create a presentation from a template and insert a data table (cross-platform)

```csharp
[Workflow]
public void Execute()
{
    using var ppt = powerpoint.UsePresentationDocument(new PresentationCreateOptions
    {
        Path = "sales-report.pptx",
        TemplatePath = "corporate-template.potx",
        PreserveTemplateMetadata = false,
        ConflictResolution = ConflictBehavior.Replace
    });

    // Add a title slide
    ppt.AddNewSlide("Title Slide");
    ppt.AddTextToSlide(1, "Title 1", "Sales Report");

    // Add a content slide with a data table
    ppt.AddNewSlide("Title and Content");
    var salesData = new DataTable("SalesData");
    salesData.Columns.Add("Region", typeof(string));
    salesData.Columns.Add("Quarter", typeof(string));
    salesData.Columns.Add("Sales", typeof(double));
    salesData.Rows.Add("North", "Q1", 120000.0);
    salesData.Rows.Add("North", "Q2", 135000.0);
    salesData.Rows.Add("South", "Q1", 98000.0);
    salesData.Rows.Add("South", "Q2", 112500.0);
    ppt.AddDataTableToSlide(2, "Content Placeholder 1", salesData,
        excludeHeaders: false, behaviour: TableAppendMode.CreateNewTable);
}
```

### Find and replace text across the entire presentation (cross-platform)

```csharp
[Workflow]
public void Execute()
{
    using var ppt = powerpoint.UsePresentationDocument("template.pptx");
    int replaced = ppt.ReplaceTextInPresentation(
        findWhat: "{{CompanyName}}",
        replaceWith: "Acme Corp",
        matchCase: false,
        replaceAll: true);
    Log($"Replaced {replaced} occurrences.");
}
```

### Insert images and save as PDF (Windows-only)

```csharp
[Workflow]
public void Execute()
{
    using var ppt = powerpoint.UsePowerPointPresentation("deck.pptx");
    ppt.AddImageOrVideoToSlide(1, "Picture Placeholder 1", @"C:\images\chart.png");
    ppt.AddTextToSlide(1, "Title 1", "Monthly Metrics");
    ppt.SavePresentationAsPDF(@"C:\output\deck.pdf", replaceExisting: true);
}
```

### Copy slides between presentations and run a macro (Windows-only)

```csharp
[Workflow]
public void Execute()
{
    using var source = powerpoint.UsePowerPointPresentation("source.pptx");
    using var dest = powerpoint.UsePowerPointPresentation("destination.pptm",
        saveChanges: true, createIfNotExist: true);

    // Copy slide 2 from source to position 1 in destination
    source.CopyPasteSlide(dest, slideToCopy: 2, whereToInsert: 1);

    // Run a macro in the destination presentation
    var result = dest.RunPresentationMacro("FormatAllSlides", new List<object> { "Arial", 12 });
    Log($"Macro returned: {result}");
}
```
