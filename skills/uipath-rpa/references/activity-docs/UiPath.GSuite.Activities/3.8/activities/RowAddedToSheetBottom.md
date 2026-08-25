# RowAddedToSheetBottom

**Integration trigger** (`isTrigger: true, triggerType: "integration"` from `uip rpa activities find`; requires a `ConnectionId` to a Google Sheets connection). **Placement: strict** — first activity of `Main.xaml`'s root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per appended row. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

Fully qualified name: `UiPath.GSuite.Activities.Sheets.Triggers.RowAddedToSheetBottom<System.Data.DataRow>`

Key attributes:
- `Item` — spreadsheet (Browse mode)
- `SheetName` — name of the sheet tab to watch
- `HasHeaders` — `"True"` / `"False"`
- Output: `AddedRow` as `System.Data.DataRow`, `Spreadsheet` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`
