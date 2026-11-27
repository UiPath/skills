### ReadRange

**Style:** Classic (`ui:`) — Standalone, No Scope

Classic activities specify the workbook path directly — no scope container needed.

```xml
<ui:ReadRange
    Range="{x:Null}"
    WorkbookPathResource="{x:Null}"
    AddHeaders="True"
    DataTable="[dtResult]"
    DisplayName="Read Range"
    SheetName="[SheetName]"
    WorkbookPath="[ExcelFilePath]" />
```

Note: `WorkbookPath` and `WorkbookPathResource` are mutually exclusive. Set the unused one to `{x:Null}`.
