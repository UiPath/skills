### WriteRange

**Style:** Classic (`ui:`) — Standalone, No Scope

Classic activities specify the workbook path directly — no scope container needed.

```xml
<ui:WriteRange
    WorkbookPathResource="{x:Null}"
    DataTable="[dtData]"
    DisplayName="Write Range"
    SheetName="Sheet1"
    StartingCell="A1"
    WorkbookPath="[ExcelFilePath]" />
```

Note: `WorkbookPath` and `WorkbookPathResource` are mutually exclusive. Set the unused one to `{x:Null}`.
