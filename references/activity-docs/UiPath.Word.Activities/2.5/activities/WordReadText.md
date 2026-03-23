# WordReadText

Reads all text content from the Word document.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordReadText
    DisplayName="Read Text"
    Text="[documentText]" />
```

- `Text` — output `String` variable containing the document's text content
