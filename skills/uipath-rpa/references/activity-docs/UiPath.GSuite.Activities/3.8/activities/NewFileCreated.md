# NewFileCreated

**Integration trigger** (`isTrigger: true, triggerType: "integration"` from `uip rpa activities find`; requires a `ConnectionId` to a Google Drive connection). **Placement: strict** — first activity of `Main.xaml`'s root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per new file. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

Fully qualified name: `UiPath.GSuite.Activities.Drive.Triggers.NewFileCreated`

Key attributes:
- `Item` / `BrowserLocation` — folder to watch (Browse mode)
- `Filter` — child block for name/type filtering conditions
- Output: `Result` as `UiPath.GSuite.Drive.Models.GDriveRemoteItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`
