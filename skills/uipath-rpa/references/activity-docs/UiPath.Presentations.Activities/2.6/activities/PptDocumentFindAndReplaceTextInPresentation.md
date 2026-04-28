# Replace Text in Presentation

`UiPath.Presentations.Activities.PptDocumentFindAndReplaceTextInPresentation`

Replaces all occurrences of a text within a presentation with another text. This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SearchFor` | Find what | InArgument | `string` | Yes | | | The text to be replaced. Only String variables and strings are supported |
| `ReplaceWith` | Replace with | InArgument | `string` | Yes | | | The text to replace with. Only String variables and strings are supported. Must not be null or empty |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation to search |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation to search |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `MatchCase` | Match case | `bool` | `false` | Whether to replace text that only matches specific capitalization |
| `WholeWordsOnly` | Whole words only | `bool` | `false` | Whether to replace entire words, not parts of a longer word. Throws if the search text contains non-alphanumeric characters |
| `ReplaceAll` | Replace All | `bool` | `true` | Replace all occurrences. If false, only the first occurrence is replaced |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `NumberOfReplacements` | Number of replacements | `int` | The number of replacements made |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

## XAML Example

```xml
<pres:PptDocumentFindAndReplaceTextInPresentation
    DisplayName="Replace Text in Presentation"
    SearchFor="[&quot;{{placeholder}}&quot;]"
    ReplaceWith="[&quot;Actual Value&quot;]"
    FilePath="[&quot;C:\Presentations\report.pptx&quot;]"
    MatchCase="True"
    ReplaceAll="True"
    NumberOfReplacements="[replacementCount]" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
- `WholeWordsOnly` is not supported when the search text contains non-alphanumeric characters — throws at runtime
