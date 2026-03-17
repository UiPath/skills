# WordAppendText

Appends text to the end of the document.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordAppendText
    DisplayName="Append Text"
    NewLine="True"
    Text="[&quot;New paragraph to append&quot;]" />
```

- `Text` — string expression with the text to append
- `NewLine` — `True` to add a new line before the text
