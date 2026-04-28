# UiPath Presentations Activities

`UiPath.Presentations.Activities`

Activities for automating PowerPoint presentations — creating, editing, and formatting slides, inserting text, data tables, media, and managing files.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### PowerPoint (Cross-Platform)

These activities use the OpenXML SDK and do **not** require Desktop PowerPoint to be installed. They work on both Windows and Linux.

| Activity | Description |
|----------|-------------|
| [Create New PowerPoint Document](activities/PptDocumentCreateNew.md) | Creates a new PowerPoint document, optionally from a template |
| [Add Text to Slide](activities/PptDocumentAddTextToSlide.md) | Inserts text into a slide placeholder |
| [Add New Slide](activities/PptDocumentInsertSlide.md) | Inserts a new slide at a specified position |
| [Delete Slide](activities/PptDocumentDeleteSlide.md) | Deletes a slide from a presentation |
| [Replace Text in Presentation](activities/PptDocumentFindAndReplaceTextInPresentation.md) | Finds and replaces text across all slides |
| [Add Data Table to Slide](activities/PptDocumentReplaceShapeWithDataTable.md) | Inserts a DataTable into a slide placeholder |
| [Add Image/Video to Slide](activities/PptDocumentReplaceShapeWithMedia.md) | Replaces a placeholder with an image or video |
| [Format Slide Content](activities/PptDocumentFormatSlideContent.md) | Modifies Z-order, font size, or shape name |

### PowerPoint.Windows

These activities use the PowerPoint Interop (COM) API and require Desktop PowerPoint to be installed. **Windows only.**

#### Scope

| Activity | Description |
|----------|-------------|
| [Use PowerPoint Presentation](activities/PowerPointApplicationScope.md) | Opens or creates a PowerPoint file as a scope for child activities |

#### Slide Operations

| Activity | Description |
|----------|-------------|
| [Add New Slide](activities/InsertSlide.md) | Inserts a new slide at a specified position |
| [Delete Slide](activities/DeleteSlide.md) | Deletes a slide from a presentation |
| [Copy Paste Slide](activities/CopyPasteSlide.md) | Copies or moves a slide between presentations |

#### Content

| Activity | Description |
|----------|-------------|
| [Add Text to Slide](activities/InsertTextInPresentation.md) | Inserts text into a slide placeholder |
| [Replace Text in Presentation](activities/FindAndReplaceTextInPresentation.md) | Finds and replaces text across all slides |
| [Add Data Table to Slide](activities/ReplaceShapeWithDataTable.md) | Inserts a DataTable into a slide placeholder |
| [Add Image/Video to Slide](activities/ReplaceShapeWithMedia.md) | Replaces a placeholder with an image or video |
| [Paste Item into Slide](activities/PasteIntoSlide.md) | Pastes clipboard content into a slide |
| [Add File to Slide](activities/InsertFile.md) | Inserts a file as an icon on a slide |
| [Format Slide Content](activities/FormatSlideContent.md) | Modifies Z-index, font size, or shape name |

#### File Operations

| Activity | Description |
|----------|-------------|
| [Save Presentation as PDF](activities/SavePresentationAsPdf.md) | Exports a presentation to PDF |
| [Save PowerPoint File As](activities/SavePresentationFileAs.md) | Saves a presentation in a different format |

#### Sensitivity Labels

| Activity | Description |
|----------|-------------|
| [Add Sensitivity Label](activities/AddSensitivityLabel.md) | Adds a sensitivity label to a presentation |
| [Get Sensitivity Label](activities/GetSensitivityLabel.md) | Retrieves the sensitivity label from a presentation |

#### Macros

| Activity | Description |
|----------|-------------|
| [Run Presentation Macro](activities/RunMacro.md) | Runs a VBA macro in a macro-enabled presentation |
