### ReplaceShapeWithDataTable

Inserts a `DataTable` as a table into a shape/placeholder.

```xml
<p:ReplaceShapeWithDataTable
    AppendMode="CreateNewTable"
    DisplayName="Insert Table"
    ExcludeHeaders="False"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Table Holder&quot;]"
    SlideIndex="[slideIndex]"
    StartColumn="1"
    StartRow="0"
    TableToInsert="[dtData]" />
```

- `TableToInsert` — `System.Data.DataTable` variable
- `AppendMode` — `"CreateNewTable"` to create a new table in the shape
- `ExcludeHeaders` — `True` to skip the header row
- `StartRow` — 0-based starting row; `StartColumn` — 1-based starting column
