# Replace Text in Presentation

`UiPath.Presentations.Activities.FindAndReplaceTextInPresentation`

Replaces all occurrences of a text within a presentation with another text using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation in which to search and replace text |
| `SearchFor` | Find what | InArgument | `string` | Yes | | | The text to be replaced. Only String variables and strings are supported |
| `ReplaceWith` | Replace with | InArgument | `string` | Yes | | | The text to replace with. Only String variables and strings are supported |

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

## XAML Example

```xml
<pres:FindAndReplaceTextInPresentation
    DisplayName="Replace Text"
    Presentation="[presentation]"
    SearchFor="[&quot;{{date}}&quot;]"
    ReplaceWith="[DateTime.Now.ToString(&quot;yyyy-MM-dd&quot;)]"
    MatchCase="True"
    ReplaceAll="True"
    NumberOfReplacements="[replacementCount]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- `WholeWordsOnly` is disabled in PowerPoint when using non-alphanumeric characters
