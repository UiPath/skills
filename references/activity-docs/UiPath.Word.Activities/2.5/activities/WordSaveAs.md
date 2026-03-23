# WordSaveAs

Saves the document under a new file path.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordSaveAs
    DisplayName="Save As"
    FilePath="[newFilePath]" />
```

- `FilePath` — new file path (string expression) for the saved copy
