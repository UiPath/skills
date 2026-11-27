# Set Bookmark Content

`UiPath.Word.Activities.WordSetBookmarkContent`

Sets the text content of a named bookmark in the Word document.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `BookmarkName` | Bookmark name | InArgument | `string` | Yes | | The name of the bookmark to update |
| `BookmarkText` | Bookmark text | InArgument | `string` | Yes | | The text to set in the bookmark |

## XAML Example

```xml
<ui:WordSetBookmarkContent
    DisplayName="Set Bookmark Content"
    BookmarkName="[&quot;CustomerName&quot;]"
    BookmarkText="[customerName]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- The bookmark must already exist in the document
