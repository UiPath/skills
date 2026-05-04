# Set Bookmark Content

`UiPath.Word.Activities.DocumentSetBookmarkContent`

Sets the text content of a named bookmark in a Word document.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |
| `BookmarkName` | Bookmark name | InArgument | `string` | Yes | | The name of the bookmark to update |
| `BookmarkText` | Bookmark text | InArgument | `string` | Yes | | The text to set in the bookmark |

## Valid Configurations

This activity supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

## XAML Example

```xml
<ui:DocumentSetBookmarkContent
    DisplayName="Set Bookmark Content"
    FilePath="[documentPath]"
    BookmarkName="[&quot;CustomerName&quot;]"
    BookmarkText="[customerName]" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
- The bookmark must already exist in the document
