# Word Activities

`UiPath.Word.Activities`

Activities for creating, reading, and manipulating Microsoft Word documents. Includes cross-platform activities using Xceed DocX and Windows-only activities using Word COM Interop.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### Cross-Platform

These activities work on both Windows and Linux. They operate on document files directly via file path or resource reference, without requiring Microsoft Word to be installed.

| Activity | Description |
|----------|-------------|
| [Create New Document](activities/DocumentCreateNew.md) | Creates a new Word document at the specified path |
| [Read Text](activities/DocumentReadText.md) | Reads all text content from a Word document |
| [Append Text](activities/DocumentAppendText.md) | Writes text at the end of a Word document |
| [Replace Text](activities/DocumentReplaceText.md) | Replaces all occurrences of text within a document |
| [Set Bookmark Content](activities/DocumentSetBookmarkContent.md) | Sets the text in a document bookmark |
| [Add Hyperlink to Document](activities/DocumentInsertHyperlink.md) | Adds a hyperlink at a specified location in a document |
| [Add Picture](activities/DocumentAddImage.md) | Adds an image at a specified location in a document |
| [Insert DataTable in Document](activities/DocumentInsertDataTable.md) | Inserts a DataTable as a table in a document |
| [Add Comment](activities/AddComment.md) | Adds a comment anchored to text or a bookmark in a document |
| [Enable Track Changes](activities/EnableTrackChanges.md) | Enables revision tracking on a Word document *(not yet visible — `browsable: false`)* |
| [Disable Track Changes](activities/DisableTrackChanges.md) | Disables revision tracking on a Word document *(not yet visible — `browsable: false`)* |

### Windows Only

These activities require Microsoft Word to be installed and must be placed inside a **Word Application Scope**. They use Word COM Interop for full-fidelity document manipulation.

#### Scope

| Activity | Description |
|----------|-------------|
| [Word Application Scope](activities/WordApplicationScope.md) | Opens a Word document and provides a scope for other Word activities |

#### Text

| Activity | Description |
|----------|-------------|
| [Read Text](activities/WordReadText.md) | Reads all text from the document in the parent scope |
| [Append Text](activities/WordAppendText.md) | Appends text at the end of the document |
| [Replace Text](activities/WordReplaceText.md) | Replaces text occurrences within the document |

#### Bookmarks

| Activity | Description |
|----------|-------------|
| [Set Bookmark Content](activities/WordSetBookmarkContent.md) | Sets the text in a document bookmark |

#### Content Controls

| Activity | Description |
|----------|-------------|
| [Set Content Property](activities/WordSetContentProperty.md) | Sets the value of a content control by matching Text, Title, or Tag |

#### Images

| Activity | Description |
|----------|-------------|
| [Add Picture](activities/WordAddImage.md) | Adds a picture at a specified location in the document |
| [Replace Picture](activities/WordReplacePicture.md) | Replaces picture(s) by matching Alt Text |
| [Paste Chart/Picture into Document](activities/WordPasteFromClipboard.md) | Pastes clipboard content (chart/picture) into the document |

#### Tables

| Activity | Description |
|----------|-------------|
| [Insert DataTable in Document](activities/WordInsertDataTable.md) | Inserts a DataTable as a table in the document |

#### Hyperlinks

| Activity | Description |
|----------|-------------|
| [Add Hyperlink to Document](activities/WordInsertHyperlink.md) | Adds a hyperlink at a specified location in the document |

#### Save & Export

| Activity | Description |
|----------|-------------|
| [Save Document As](activities/WordSaveAs.md) | Saves the document as a different file or format |
| [Save Document as PDF](activities/WordExportToPdf.md) | Exports the document to PDF |

#### Sensitivity Labels

| Activity | Description |
|----------|-------------|
| [Add or Update Word Sensitivity Label](activities/WordAddSensitivityLabel.md) | Adds or updates a sensitivity label on the document |
| [Get Word Sensitivity Label](activities/WordGetSensitivityLabel.md) | Retrieves the sensitivity label from the document |

#### Track Changes

| Activity | Description |
|----------|-------------|
| [Enable Track Changes](activities/EnableTrackChanges.md) | Enables revision tracking with scope control (TrackForMe or TrackForEveryone) |
| [Disable Track Changes](activities/DisableTrackChanges.md) | Disables revision tracking, handling protected documents |

#### Comments

| Activity | Description |
|----------|-------------|
| [Add Comment](activities/AddComment.md) | Adds a comment anchored to text, a bookmark, or a tracked change |
