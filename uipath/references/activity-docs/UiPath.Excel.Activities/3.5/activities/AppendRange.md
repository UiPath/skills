### AppendRange

**Style:** Classic (`ui:`) — Standalone, No Scope

Classic activities specify the workbook path directly — no scope container needed.

```xml
<ui:AppendRange
    WorkbookPathResource="{x:Null}"
    DataTable="[dtData]"
    DisplayName="Append Range"
    SheetName="[SheetName]"
    WorkbookPath="[ExcelFilePath]" />
```

Note: `WorkbookPath` and `WorkbookPathResource` are mutually exclusive. Set the unused one to `{x:Null}`.
