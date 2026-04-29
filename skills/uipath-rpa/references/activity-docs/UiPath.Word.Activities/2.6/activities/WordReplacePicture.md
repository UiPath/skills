# Replace Picture

`UiPath.Word.Activities.WordReplacePicture`

Replaces picture(s) in the Word document based on their Alt Text.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `PictureAltText` | Find pictures with Alt Text | InArgument | `string` | Yes | | All pictures with this Alt Text will be replaced. Case insensitive |
| `PicturePath` | Replace with picture | InArgument | `string` | Yes | | The file path to the replacement image |

## XAML Example

```xml
<ui:WordReplacePicture
    DisplayName="Replace Picture"
    PictureAltText="[&quot;CompanyLogo&quot;]"
    PicturePath="[newLogoPath]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Matches are case insensitive on the Alt Text
- All pictures with matching Alt Text are replaced
