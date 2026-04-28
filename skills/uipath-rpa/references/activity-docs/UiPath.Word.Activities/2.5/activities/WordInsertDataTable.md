# WordInsertDataTable

Inserts a `DataTable` into the Word document as a formatted table.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordInsertDataTable
    DataTable="[dtData]"
    DisplayName="Insert Data Table"
    InsertRelativeTo="Document"
    Position="End" />
```

- `DataTable` — `System.Data.DataTable` variable to insert
- `Position` — `Start` (default) or `End`. **CRITICAL: defaults to `Start`**, which inserts at the beginning of the document. Use `Position="End"` to insert after existing content (e.g., after text appended with `WordAppendText`)
- `InsertRelativeTo` — `Document` (default), `Bookmark`, or `Text`. Controls where the table is placed relative to
- `Text` — search string when `InsertRelativeTo="Text"`
- `Bookmark` — bookmark name when `InsertRelativeTo="Bookmark"`
- `Occurrence` — `All`, `First`, `Last`, or `Specific` (when using Text/Bookmark positioning)

**Formatting tip:** `WordInsertDataTable` calls `.ToString()` on every cell value. For human-readable output, create a **formatted copy** of your DataTable with string columns containing pre-formatted values (e.g., `"$255.76"` instead of raw `255.76`, `"+1.23%"` instead of `0.0123`, `"40.1M"` instead of `40132517`). Column headers are included automatically if they have non-default names.
