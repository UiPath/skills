# Refresh Excel Data Connections

`UiPath.Excel.Activities.Business.RefreshDataConnectionsX`

Get the latest data by refreshing all sources in the workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Takes a handle to the Excel workbook. |

## XAML Example
```xml
<excel:RefreshDataConnectionsX
  DisplayName="Refresh Excel Data Connections"
  Workbook="[workbookHandle]" />
```

## Notes
- Refreshes all external data connections in the workbook (e.g., database queries, web queries, linked data sources).
- Throws `ArgumentNullException` if the workbook handle is null.
