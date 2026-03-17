### FindAndReplaceTextInPresentation

Finds and replaces text across the entire presentation.

```xml
<p:FindAndReplaceTextInPresentation
    DisplayName="Find and Replace Text"
    MatchCase="False"
    NumberOfReplacements="[replacementCount]"
    Presentation="[PowerPoint]"
    ReplaceAll="True"
    ReplaceWith="[&quot;NewValue&quot;]"
    SearchFor="[&quot;OldValue&quot;]"
    WholeWordsOnly="False" />
```

- `SearchFor` / `ReplaceWith` — string expressions
- `NumberOfReplacements` — output `Int32` count of replacements made
