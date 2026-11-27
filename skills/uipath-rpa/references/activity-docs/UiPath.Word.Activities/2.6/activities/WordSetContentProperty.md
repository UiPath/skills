# Set Content Property

`UiPath.Word.Activities.WordSetContentProperty`

Sets the value of a content control in the Word document by matching its Text, Title, or Tag property.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `MatchBy` | Match by | InArgument | `MatchPropertyBy` | Yes | `Text` | Specifies the property to match content controls by |
| `MatchTo` | Match to | InArgument | `string` | Yes | | The value to match against the selected property |
| `Value` | Value | InArgument | `string` | Yes | | The text value to set in the matched content control |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReplaceAll` | Replace all | `bool` | `false` | If true, replaces all matching content controls; otherwise only the first match |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Found` | Found | `bool` | Indicates whether at least one content control was found and updated |

### Enum Reference

**`MatchPropertyBy`**: `Text` (match by current text content), `Title` (match by control title), `Tag` (match by control tag)

## XAML Example

```xml
<ui:WordSetContentProperty
    DisplayName="Set Content Property"
    MatchBy="[MatchPropertyBy.Title]"
    MatchTo="[&quot;CompanyName&quot;]"
    Value="[companyName]"
    ReplaceAll="False"
    Found="[wasFound]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Content controls are structured document elements in Word used for form fields and templates
- Useful for filling in Word templates that use content controls as placeholders
